import unittest
from voice_engine import parse_command, decode_result

class VoiceTests(unittest.TestCase):
    def test_commands(self):
        self.assertEqual(parse_command(" ДАЛЬШЕ "), "next")
        self.assertEqual(parse_command("назад"), "previous")
        self.assertEqual(decode_result('{"text":"назад"}'), "previous")
    def test_ignored(self):
        for spoken in ["", "дальше назад", "можно дальше", "[unk]", "не назад"]:
            self.assertIsNone(parse_command(spoken))
        self.assertIsNone(decode_result("incorrect-json"))

if __name__ == "__main__":
    unittest.main()
