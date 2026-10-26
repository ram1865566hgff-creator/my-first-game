"""Safe PowerPoint slide-show actions for SlideVoice.

Animation commands use ONLY PowerPoint.GotoClick(), never keyboard arrows.
Even a failed COM connection cannot turn "Дальше"/"Назад" into a slide change.
"""
COMMANDS = {"animation_next", "animation_previous", "slide_next", "slide_previous"}

def decide_action(action, click_index, click_total, slide_index, slides_total):
    """Returns (kind, payload): click, goto, info. Never key for animations."""
    if action not in COMMANDS:
        raise ValueError("Unknown voice command")
    if action == "slide_next":
        return ("goto", slide_index + 1) if slide_index < slides_total else (
            "info", "последний слайд")
    if action == "slide_previous":
        return ("goto", slide_index - 1) if slide_index > 1 else (
            "info", "первый слайд")
    # When PowerPoint reports no click-triggered animations, do nothing.
    if click_total <= 0:
        return "info", "на слайде нет пошаговых анимаций"
    # Unknown/automatic state: fail closed instead of advancing slides.
    if click_index < 0 or click_index > click_total:
        return "info", "состояние анимации не определено"
    if action == "animation_next":
        if click_index >= click_total:
            return "info", "все анимации показаны"
        return "click", click_index + 1
    if click_index <= 0:
        return "info", "начало анимации"
    return "click", click_index - 1

def apply_to_view(action, view, slides_total):
    """Apply checked action to slideshow object. No keystroke is generated."""
    current_slide = int(view.Slide.SlideIndex)
    if action.startswith("animation_"):
        click_total = int(view.GetClickCount())
        click_index = int(view.GetClickIndex())
    else:
        click_total = click_index = 0
    kind, payload = decide_action(
        action, click_index, click_total, current_slide, slides_total)
    if kind == "info":
        return payload
    if kind == "goto":
        view.GotoSlide(int(payload), -1)
        return "слайд " + str(payload)
    # GotoClick targets an animation on the SAME slide and cannot turn the page.
    view.GotoClick(int(payload))
    return "анимация " + str(payload) + "/" + str(click_total)

def execute_powerpoint_command(action):
    """Return None if no running desktop PowerPoint slideshow is accessible."""
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
            show = ppt.SlideShowWindows(1)
        except Exception:
            return None
        try:
            return apply_to_view(
                action, show.View, int(show.Presentation.Slides.Count))
        except Exception:
            return "PowerPoint: ошибка управления, действие отменено"
    finally:
        pythoncom.CoUninitialize()

def route_command(action, powerpoint_executor, send_slide_key):
    """Never fall back to generic keys for animation commands."""
    if action not in COMMANDS:
        raise ValueError("Unknown voice command")
    result = powerpoint_executor(action)
    if result is not None:
        return result
    if action.startswith("animation_"):
        return "показ PowerPoint не найден; действие отменено"
    # Generic PDF/browser presentations use PageUp/PageDown for explicit slides.
    send_slide_key(action)
    return "команда переключения слайда отправлена"
