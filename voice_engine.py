"""Recognize only two commands; disregard all other speech."""
import json

GRAMMAR = json.dumps(["дальше", "назад", "[unk]"], ensure_ascii=False)
COMMANDS = {"дальше": "next", "назад": "previous"}

def parse_command(text):
    return COMMANDS.get(" ".join(text.casefold().strip().split()))

def decode_result(raw):
    try:
        return parse_command(json.loads(raw).get("text", ""))
    except (TypeError, ValueError, AttributeError):
        return None
