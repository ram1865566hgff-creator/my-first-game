"""Video player routing by currently focused WINDOW+TAB, no session pinning.

Hotkeys in most media players are toggles. We keep a last-command record for
each visible window title (browser tab), avoiding immediate same-command toggles.
This is not true playback-state detection and cannot cover every website.
"""
MODES = (
    ("Пробел — видеоплееры и браузеры", 0x20),
    ("K — YouTube", 0x4B),
    ("Мультимедиа — Windows Play/Pause", 0xB3),
    ("ВК Видео — пробел", 0x20),
    ("Авто — текущая вкладка и видеоплеер", "auto"),
)

def choose_key(mode, title=""):
    value=dict(MODES)[mode]
    if value!="auto":
        return value
    name=(title or "").casefold()
    if "youtube" in name or "ютуб" in name:
        return 0x4B
    return 0x20

class PlaybackGuard:
    """Tracks tabs separately, even when they share a browser HWND."""
    def __init__(self):
        self.history={}
    def clear(self):
        self.history.clear()
    def target(self,hwnd,mode,title=""):
        return (int(hwnd), (title or "").strip().casefold(),mode)
    def should_send(self,hwnd,mode,command,title=""):
        return self.history.get(self.target(hwnd,mode,title))!=command
    def record(self,hwnd,mode,command,title=""):
        # Prevent unlimited growth if browsing through thousands of pages.
        if len(self.history)>200:
            self.history.clear()
        self.history[self.target(hwnd,mode,title)]=command

def apply_command(command,mode,hwnd,own,guard,send_key,title=""):
    if command not in ("pause","play"):
        raise ValueError("Нераспознанная команда")
    if mode not in dict(MODES):
        raise ValueError("Неизвестный режим")
    key=choose_key(mode,title)
    if own and key!=0xB3:
        return "откройте окно с видео"
    if not guard.should_send(hwnd,mode,command,title):
        return "повторная команда пропущена для этой вкладки"
    send_key(key)
    guard.record(hwnd,mode,command,title)
    return "команда паузы отправлена" if command=="pause" else "команда воспроизведения отправлена"
