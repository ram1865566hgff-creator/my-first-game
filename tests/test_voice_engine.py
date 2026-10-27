import json
import unittest
from voice_engine import COMMANDS, GRAMMAR, parse_command, decode_result
from ppt_controls import decide_action, apply_to_view, route_command

class SpeechTests(unittest.TestCase):
    def test_all_commands(self):
        for words, action in COMMANDS.items():
            self.assertEqual(parse_command(words.upper()), action)
            self.assertEqual(decode_result(json.dumps({"text": words}, ensure_ascii=False)), action)
        self.assertEqual(len(json.loads(GRAMMAR)), 5)
    def test_unknown(self):
        for words in ["", "[unk]", "можно дальше", "дальше назад",
                      "не следующий слайд", "слайд"]:
            self.assertIsNone(parse_command(words))
        self.assertIsNone(decode_result("{broken"))

class FakeSlide:
    SlideIndex = 3

class FakeView:
    Slide = FakeSlide()
    def __init__(self, clicks=0, current=0):
        self.clicks = clicks
        self.current = current
        self.operations = []
    def GetClickCount(self):
        return self.clicks
    def GetClickIndex(self):
        return self.current
    def GotoClick(self, index):
        self.operations.append(("click", index))
    def GotoSlide(self, index, reset):
        self.operations.append(("slide", index, reset))

class PowerPointTests(unittest.TestCase):
    def test_no_animation_never_changes_slide(self):
        view = FakeView(0, 0)
        self.assertIn("нет пошаговых", apply_to_view("animation_next", view, 5))
        self.assertIn("нет пошаговых", apply_to_view("animation_previous", view, 5))
        self.assertEqual(view.operations, [])
    def test_animation_end_and_start_are_safe(self):
        view = FakeView(3, 3)
        self.assertEqual(decide_action("animation_next", 3, 3, 3, 5),
                         ("info", "все анимации показаны"))
        apply_to_view("animation_next", view, 5)
        self.assertEqual(view.operations, [])
        view.current = 0
        apply_to_view("animation_previous", view, 5)
        self.assertEqual(view.operations, [])
    def test_animation_commands_only_go_to_click(self):
        view = FakeView(3, 1)
        apply_to_view("animation_next", view, 6)
        self.assertEqual(view.operations, [("click", 2)])
        apply_to_view("animation_previous", view, 6)
        self.assertEqual(view.operations, [("click", 2), ("click", 0)])
    def test_slide_commands_only_go_to_slide(self):
        view = FakeView(3, 2)
        apply_to_view("slide_next", view, 6)
        apply_to_view("slide_previous", view, 6)
        self.assertEqual(view.operations, [("slide", 4, -1), ("slide", 2, -1)])
    def test_com_missing_cannot_send_animation_key(self):
        sent = []
        no_com = lambda action: None
        route_command("animation_next", no_com, sent.append)
        route_command("animation_previous", no_com, sent.append)
        self.assertEqual(sent, [])
        route_command("slide_next", no_com, sent.append)
        self.assertEqual(sent, ["slide_next"])
    def test_unknown_or_automatic_state_rejected(self):
        self.assertEqual(decide_action("animation_next", -2, 3, 3, 6)[0], "info")
        self.assertEqual(decide_action("animation_next", 7, 3, 3, 6)[0], "info")

if __name__ == "__main__":
    unittest.main()


from navigation_guard import SlideCommandGuard

class RepeatedVoiceTests(unittest.TestCase):
    def test_next_command_on_every_utterance(self):
        guard = SlideCommandGuard(window_seconds=0.45)
        self.assertTrue(guard.accept("slide_next", 10.00))
        # Duplicated recognizer event inside a fraction of a second.
        self.assertFalse(guard.accept("slide_next", 10.12))
        # Two intentional spoken phrases follow one another normally.
        self.assertTrue(guard.accept("slide_next", 10.9))
        self.assertTrue(guard.accept("slide_next", 11.8))
        self.assertTrue(guard.accept("slide_next", 12.7))

    def test_previous_command_on_every_utterance(self):
        guard=SlideCommandGuard()
        for t in (1.0, 1.9, 2.8, 3.7, 4.6):
            self.assertTrue(guard.accept("slide_previous", t))
        self.assertFalse(guard.accept("slide_previous", 4.82))

    def test_immediate_change_of_direction(self):
        guard=SlideCommandGuard()
        self.assertTrue(guard.accept("slide_next", 5.0))
        self.assertTrue(guard.accept("slide_previous", 5.12))
        self.assertTrue(guard.accept("slide_next", 5.24))

    def test_animation_commands_never_locked(self):
        guard=SlideCommandGuard()
        for action in ("animation_next","animation_next","animation_previous"):
            self.assertTrue(guard.accept(action,5.0))

    def test_session_reset(self):
        guard=SlideCommandGuard()
        self.assertTrue(guard.accept("slide_next",5.0))
        guard.reset()
        self.assertTrue(guard.accept("slide_next",5.1))

    def test_integration_five_real_commands_one_slide_each(self):
        guard=SlideCommandGuard()
        slide=1
        transitions=[]
        for now in (10.0, 10.12, 11.05, 12.10, 13.15, 14.20):
            if guard.accept("slide_next",now):
                slide+=1
                transitions.append(slide)
        self.assertEqual(transitions,[2,3,4,5,6])
