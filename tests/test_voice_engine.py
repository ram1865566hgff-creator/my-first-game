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
    def test_single_phrase_cannot_skip_two_slides(self):
        guard = SlideCommandGuard(window_seconds=2.7)
        self.assertTrue(guard.accept("slide_next", 10.0))
        # Two recognizer results for one spoken "следующий слайд".
        self.assertFalse(guard.accept("slide_next", 11.3))
        self.assertFalse(guard.accept("slide_next", 12.4))
        self.assertTrue(guard.accept("slide_next", 12.8))

    def test_backwards_independent(self):
        guard = SlideCommandGuard()
        self.assertTrue(guard.accept("slide_next", 1.0))
        self.assertTrue(guard.accept("slide_previous", 1.2))
        self.assertFalse(guard.accept("slide_previous", 2.2))
        self.assertTrue(guard.accept("slide_next", 2.3))

    def test_animations_not_blocked(self):
        guard = SlideCommandGuard()
        self.assertTrue(guard.accept("animation_next", 1.0))
        self.assertTrue(guard.accept("animation_next", 1.1))
        self.assertTrue(guard.accept("animation_previous", 1.15))

    def test_reset_on_new_session(self):
        guard=SlideCommandGuard()
        self.assertTrue(guard.accept("slide_next", 5.0))
        guard.reset()
        self.assertTrue(guard.accept("slide_next", 5.1))
