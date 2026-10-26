"""Russian offline speech grammar for four commands."""
import json

COMMANDS = {
    "дальше": "animation_next",
    "назад": "animation_previous",
    "следующий слайд": "slide_next",
    "предыдущий слайд": "slide_previous",
}
GRAMMAR = json.dumps([*COMMANDS, "[unk]"], ensure_ascii=False)

def parse_command(text):
    if not isinstance(text, str):
        return None
    return COMMANDS.get(" ".join(text.casefold().strip().split()))

def decode_result(raw):
    try:
        return parse_command(json.loads(raw).get("text", ""))
    except (TypeError, ValueError, AttributeError):
        return None
