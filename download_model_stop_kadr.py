"""Download official Russian small Vosk model for offline speech."""
from pathlib import Path
from urllib.request import urlretrieve
import zipfile
NAME="vosk-model-small-ru-0.22"
ROOT=Path(__file__).resolve().parent/"models"
TARGET=ROOT/NAME
URL="https://alphacephei.com/vosk/models/"+NAME+".zip"
if __name__=="__main__":
    if (TARGET/"am").is_dir() and (TARGET/"conf").is_dir():
        print("Model already installed")
    else:
        ROOT.mkdir(exist_ok=True)
        out=ROOT/(NAME+".zip")
        try:
            print("Downloading Russian speech model")
            urlretrieve(URL,out)
            with zipfile.ZipFile(out) as archive:
                for member in archive.infolist():
                    if not (ROOT/member.filename).resolve().is_relative_to(ROOT.resolve()):
                        raise ValueError("Unsafe model archive")
                archive.extractall(ROOT)
            if not (TARGET/"am").is_dir() or not (TARGET/"conf").is_dir():
                raise RuntimeError("Speech model extraction failed")
        finally: out.unlink(missing_ok=True)
