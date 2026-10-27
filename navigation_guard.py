"""Dedupe repeated speech recognitions for full slide navigation.

Vosk can produce a repeated final result for one spoken phrase, especially if
the audio is echoed by nearby speakers. "Следующий слайд" must cause one
transition, not two. Animation steps retain their previous behavior.
"""
class SlideCommandGuard:
    SLIDES = frozenset(("slide_next", "slide_previous"))
    def __init__(self, window_seconds=2.7):
        if window_seconds<=0:
            raise ValueError("window_seconds must be positive")
        self.window_seconds=float(window_seconds)
        self.reset()
    def reset(self):
        self.last_action=None
        self.last_time=float("-inf")
    def accept(self,action,now):
        if action not in self.SLIDES:
            # No delay is imposed on individual animation steps.
            return True
        if action==self.last_action and now-self.last_time<self.window_seconds:
            return False
        self.last_action=action
        self.last_time=now
        return True
