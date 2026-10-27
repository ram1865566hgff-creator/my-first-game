import unittest,json
from voice_engine_stop_kadr import parse_command,decode_result,GRAMMAR
from video_controls_stop_kadr import MODES,PlaybackGuard,apply_command
class Commands(unittest.TestCase):
    def test_voices(self):
        self.assertEqual(parse_command(" СТОП "),"pause")
        self.assertEqual(parse_command("ПЛЕЙ"),"play")
        self.assertEqual(decode_result('{"text":"плей"}'),"play")
        self.assertEqual(json.loads(GRAMMAR),["стоп","плей","[unk]"])
    def test_unknown(self):
        for x in ("","пауза","стоп плей","включи","[unk]"):
            self.assertIsNone(parse_command(x))
        self.assertIsNone(decode_result("broken"))
    def test_safe_repeat(self):
        sent=[];g=PlaybackGuard();mode=MODES[0][0]
        apply_command("pause",mode,100,False,g,sent.append)
        apply_command("pause",mode,100,False,g,sent.append)
        apply_command("play",mode,100,False,g,sent.append)
        self.assertEqual(sent,[0x20,0x20])
    def test_own_window(self):
        sent=[]
        apply_command("pause",MODES[0][0],100,True,PlaybackGuard(),sent.append)
        self.assertEqual(sent,[])
        apply_command("play",MODES[2][0],100,True,PlaybackGuard(),sent.append)
        self.assertEqual(sent,[0xB3])
if __name__=="__main__":unittest.main()


from fast_voice_stop_kadr import FastVoiceDetector
class SpeedTests(unittest.TestCase):
    def test_trigger_before_final(self):
        d=FastVoiceDetector(.10)
        self.assertIsNone(d.accept_partial('{"partial":"стоп"}',1.00))
        self.assertIsNone(d.accept_partial('{"partial":"стоп"}',1.05))
        self.assertEqual(d.accept_partial('{"partial":"стоп"}',1.12),"pause")
        self.assertIsNone(d.accept_final('{"text":"стоп"}'))
        self.assertIsNone(d.accept_partial('{"partial":"плей"}',2.00))
        self.assertEqual(d.accept_partial('{"partial":"плей"}',2.12),"play")
    def test_final_fallback(self):
        d=FastVoiceDetector()
        self.assertEqual(d.accept_final('{"text":"плей"}'),"play")
        self.assertIsNone(d.accept_final('{"text":"бессмысленно"}'))
    def test_revised_videomode(self):
        self.assertEqual(dict(MODES)["ВК Видео — пробел"],0x20)
