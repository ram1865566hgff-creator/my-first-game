"""Download small official Russian Vosk model before packaging."""
from pathlib import Path
import urllib.request
import zipfile

NAME = "vosk-model-small-ru-0.22"
ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
TARGET = MODELS / NAME
URL = "https://alphacephei.com/vosk/models/" + NAME + ".zip"

def main():
    if (TARGET / "am").is_dir() and (TARGET / "conf").is_dir():
        print("Речевая модель установлена")
        return
    MODELS.mkdir(exist_ok=True)
    archive_path = MODELS / (NAME + ".zip")
    try:
        print("Загружаю русскую модель...")
        urllib.request.urlretrieve(URL, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                extracted = (MODELS / member.filename).resolve()
                if not extracted.is_relative_to(MODELS.resolve()):
                    raise RuntimeError("Недопустимый путь в архиве")
            archive.extractall(MODELS)
        if not (TARGET / "am").is_dir() or not (TARGET / "conf").is_dir():
            raise RuntimeError("Речевая модель не была установлена")
    finally:
        archive_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
