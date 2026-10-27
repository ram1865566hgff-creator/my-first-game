"""Safe STOP verification using unrestricted Vosk transcription.

A two-command grammar may turn arbitrary sounds beginning with "с" into
"стоп". Require the complete, unforced transcript of the utterance to be
exactly that word. Partial transcripts are never accepted for pausing.
"""
import json

def is_verified_stop(raw, min_confidence=0.62):
    try:
        result=json.loads(raw)
    except (TypeError,ValueError):
        return False
    if not isinstance(result,dict):
        return False
    transcript=result.get("text")
    if not isinstance(transcript,str) or transcript.strip().casefold()!="стоп":
        return False
    words=result.get("result")
    if words is None:
        # Vosk can omit word timings when unavailable. Exact unrestricted
        # transcript is still safer than grammar-only partial recognition.
        return True
    if not isinstance(words,list) or len(words)!=1:
        return False
    word=words[0]
    if not isinstance(word,dict) or word.get("word")!="стоп":
        return False
    confidence=word.get("conf")
    if isinstance(confidence,(float,int)):
        return float(confidence)>=min_confidence
    return True
