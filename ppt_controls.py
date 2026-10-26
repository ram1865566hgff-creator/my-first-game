"""Controls running desktop PowerPoint slideshow via its COM object model."""
COMMANDS = {"animation_next", "animation_previous", "slide_next", "slide_previous"}

def decide_action(action, click_index, click_total, slide_index, slides_total):
    """Pure logic; result is (kind, payload) with kind key/goto/info."""
    if action not in COMMANDS:
        raise ValueError("Unknown voice command")
    if action == "slide_next":
        if slide_index >= slides_total:
            return "info", "последний слайд"
        return "goto", slide_index + 1
    if action == "slide_previous":
        if slide_index <= 1:
            return "info", "первый слайд"
        return "goto", slide_index - 1
    if action == "animation_next":
        if click_total <= 0 or click_index == -2 or click_index >= click_total:
            return "info", "все анимации показаны"
        return "key", action
    if click_total <= 0 or click_index in (-1, 0):
        return "info", "начало анимации"
    return "key", action

def execute_powerpoint_command(command, send_key):
    """Return None when no running PowerPoint slideshow can be accessed."""
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None
    pythoncom.CoInitialize()
    try:
        try:
            ppt = win32com.client.GetActiveObject("PowerPoint.Application")
            if ppt.SlideShowWindows.Count < 1:
                return None
        except Exception:
            return None
        try:
            show = ppt.SlideShowWindows(1)
            view = show.View
            current = int(view.Slide.SlideIndex)
            total = int(show.Presentation.Slides.Count)
            click_index = int(view.GetClickIndex()) if command.startswith("animation_") else 0
            click_total = int(view.GetClickCount()) if command.startswith("animation_") else 0
            kind, payload = decide_action(command, click_index, click_total, current, total)
            if kind == "info":
                return payload
            if kind == "goto":
                # -1 = msoTrue: animations restart when visiting the target slide.
                view.GotoSlide(int(payload), -1)
                return "слайд " + str(payload)
            send_key(payload)
            return "шаг анимации"
        except Exception:
            # Do not silently send a potentially incorrect slide-change keystroke.
            return "не удалось управлять PowerPoint"
    finally:
        pythoncom.CoUninitialize()
