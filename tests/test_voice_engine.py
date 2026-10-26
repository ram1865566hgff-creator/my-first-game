import json
import unittest
from voice_engine import COMMANDS, GRAMMAR, parse_command, decode_result
from ppt_controls import decide_action

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

class PowerPointTests(unittest.TestCase):
    def test_animation_boundaries(self):
        self.assertEqual(decide_action("animation_next", 0, 3, 2, 5),
                         ("key", "animation_next"))
        self.assertEqual(decide_action("animation_next", 3, 3, 2, 5),
                         ("info", "все анимации показаны"))
        self.assertEqual(decide_action("animation_next", -2, 3, 2, 5),
                         ("info", "все анимации показаны"))
        self.assertEqual(decide_action("animation_previous", 0, 3, 2, 5),
                         ("info", "начало анимации"))
        self.assertEqual(decide_action("animation_previous", 1, 3, 2, 5),
                         ("key", "animation_previous"))
        self.assertEqual(decide_action("animation_next", 0, 0, 2, 5),
                         ("info", "все анимации показаны"))
    def test_slide_navigation_ignores_click_position(self):
        self.assertEqual(decide_action("slide_next", 0, 5, 2, 6), ("goto", 3))
        self.assertEqual(decide_action("slide_previous", 5, 5, 2, 6), ("goto", 1))
        self.assertEqual(decide_action("slide_next", 0, 0, 6, 6),
                         ("info", "последний слайд"))
        self.assertEqual(decide_action("slide_previous", 0, 0, 1, 6),
                         ("info", "первый слайд"))

if __name__ == "__main__":
    unittest.main()
