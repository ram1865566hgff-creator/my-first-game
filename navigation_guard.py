"""Dedupe repeated speech recognitions for full slide navigation.

Prevent extremely close duplicate recognition results only.

The previous 2.7-second lockout accidentally ignored the next deliberate
"Следующий слайд" or "Предыдущий слайд" command. Normal speech repetitions
must be accepted on every utterance. Animation steps are not rate-limited.
"""
class SlideCommandGuard:
    SLIDES = frozenset(("slide_next", "slide_previous"))
    def __init__(self, window_seconds=0.45):
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
