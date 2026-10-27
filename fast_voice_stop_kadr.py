"""Trigger short voice commands on stable partial Vosk results before silence."""
import json
from voice_engine_stop_kadr import parse_command, decode_result

class FastVoiceDetector:
    def __init__(self,min_stable_seconds=0.10):
        self.delay=min_stable_seconds
        self.partial=None
        self.first_at=None
        self.held=False

    def accept_partial(self,raw,now):
        try:
            command=parse_command(json.loads(raw).get("partial",""))
        except (ValueError,TypeError,AttributeError):
            command=None
        if self.held:
            return None
        if command!=self.partial:
            self.partial=command
            self.first_at=now
            return None
        if command and self.first_at is not None and now-self.first_at>=self.delay:
            self.held=True
            return command
        return None

    def accept_final(self,raw):
        command=decode_result(raw)
        already=self.held
        self.partial=None
        self.first_at=None
        self.held=False
        return None if already else command
