"""Video player hotkey routing. Play/pause is a toggle in most players."""
MODES=(
  ("Пробел — видеоплееры и браузеры",0x20),
  ("K — YouTube",0x4B),
  ("Мультимедиа — Windows Play/Pause",0xB3),
)
class PlaybackGuard:
    def __init__(self): self.history={}
    def clear(self): self.history.clear()
    def should_send(self,hwnd,mode,command):
        return self.history.get((hwnd,mode))!=command
    def record(self,hwnd,mode,command):
        self.history[(hwnd,mode)]=command

def apply_command(command,mode,hwnd,own,guard,send_key):
    if command not in ("pause","play"): raise ValueError("Bad command")
    if mode not in dict(MODES): raise ValueError("Bad mode")
    key=dict(MODES)[mode]
    if own and key!=0xB3: return "переключитесь в окно видео"
    if not guard.should_send(hwnd,mode,command):
        return "повтор команды пропущен, чтобы не изменить состояние обратно"
    send_key(key)
    guard.record(hwnd,mode,command)
    return "команда паузы отправлена" if command=="pause" else "команда воспроизведения отправлена"
