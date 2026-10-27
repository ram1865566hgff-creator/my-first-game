"""Offline Russian two-command speech recognition."""
import json
COMMANDS={"стоп":"pause","плей":"play"}
GRAMMAR=json.dumps(["стоп","плей","[unk]"],ensure_ascii=False)
def parse_command(text):
    return COMMANDS.get(" ".join(text.casefold().strip().split())) if isinstance(text,str) else None
def decode_result(raw):
    try: return parse_command(json.loads(raw).get("text",""))
    except (TypeError,ValueError,AttributeError): return None
