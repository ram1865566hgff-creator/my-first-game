"""Win32 keyboard injection and video-window selection (Windows 10/11 x64)."""
import ctypes
from ctypes import wintypes
import os

ULONG_PTR=wintypes.WPARAM
class MOUSEINPUT(ctypes.Structure):
    _fields_=[("dx",wintypes.LONG),("dy",wintypes.LONG),
        ("mouseData",wintypes.DWORD),("dwFlags",wintypes.DWORD),
        ("time",wintypes.DWORD),("dwExtraInfo",ULONG_PTR)]
class KEYBDINPUT(ctypes.Structure):
    _fields_=[("wVk",wintypes.WORD),("wScan",wintypes.WORD),
        ("dwFlags",wintypes.DWORD),("time",wintypes.DWORD),
        ("dwExtraInfo",ULONG_PTR)]
class HARDWAREINPUT(ctypes.Structure):
    _fields_=[("uMsg",wintypes.DWORD),("wParamL",wintypes.WORD),
        ("wParamH",wintypes.WORD)]
class INPUT_UNION(ctypes.Union):
    _fields_=[("mi",MOUSEINPUT),("ki",KEYBDINPUT),("hi",HARDWAREINPUT)]
class INPUT(ctypes.Structure):
    _fields_=[("type",wintypes.DWORD),("data",INPUT_UNION)]

def send_input_key(vk):
    """Send full physical key down/up events; compatible with Chromium shortcuts."""
    user32=ctypes.windll.user32
    user32.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int]
    user32.SendInput.restype=wintypes.UINT
    user32.MapVirtualKeyW.argtypes=[wintypes.UINT,wintypes.UINT]
    user32.MapVirtualKeyW.restype=wintypes.UINT
    scan=int(user32.MapVirtualKeyW(int(vk),0))
    # Virtual keys for multimedia keys, scancode for regular keyboard keys.
    using_scan=(vk!=0xB3 and scan!=0)
    arr=(INPUT*2)()
    for i,release in enumerate([False,True]):
        arr[i].type=1
        arr[i].data.ki.wVk=0 if using_scan else int(vk)
        arr[i].data.ki.wScan=scan if using_scan else 0
        arr[i].data.ki.dwFlags=(0x0008 if using_scan else 0)|(0x0002 if release else 0)
    count=user32.SendInput(2,arr,ctypes.sizeof(INPUT))
    if count!=2:
        raise OSError(ctypes.get_last_error(),"Windows не приняла команду клавиатуры")

def list_windows():
    user32=ctypes.windll.user32
    fn=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    user32.EnumWindows.argtypes=[fn,wintypes.LPARAM]
    windows=[]
    @fn
    def callback(hwnd,unused):
        if not user32.IsWindowVisible(hwnd):
            return True
        count=user32.GetWindowTextLengthW(hwnd)
        if count<4:
            return True
        buf=ctypes.create_unicode_buffer(count+1)
        user32.GetWindowTextW(hwnd,buf,count+1)
        name=buf.value.strip()
        if not name:
            return True
        pid=wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value!=os.getpid():
            windows.append((int(hwnd),name))
        return True
    if not user32.EnumWindows(callback,0):
        raise ctypes.WinError()
    return windows[:120]

def activate_target(hwnd):
    u=ctypes.windll.user32
    if not u.IsWindow(wintypes.HWND(hwnd)):
        return False,"окно закрыто; нажмите «Обновить»"
    if u.IsIconic(wintypes.HWND(hwnd)):
        u.ShowWindow(wintypes.HWND(hwnd),9)  # restore minimized
    u.SetForegroundWindow(wintypes.HWND(hwnd))
    if int(u.GetForegroundWindow())!=int(hwnd):
        return False,"Windows не разрешила активировать окно: щёлкните по видео"
    return True,"готово"
