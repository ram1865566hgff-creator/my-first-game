"""Build the new Слайд вперед Windows icon from bundled original artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(exist_ok=True)
art_path = ASSETS / "slide-vpered-art.jpg"
if not art_path.is_file():
    raise FileNotFoundError("The source app artwork is missing: " + str(art_path))

art = Image.open(art_path).convert("RGBA")
# Export crisp, transparent-edge Windows icon versions.
image = art.resize((512, 512), Image.Resampling.LANCZOS)
image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=105, threshold=2))
mask = Image.new("L", (512, 512), 0)
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle((2, 2, 510, 510), radius=91, fill=255)
image.putalpha(mask)
image.save(ASSETS / "slide-vpered.ico", format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
           (64, 64), (128, 128), (256, 256)])
image.resize((256, 256), Image.Resampling.LANCZOS).save(ASSETS / "slide-vpered.png")
