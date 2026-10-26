"""Generate app icon at build time with Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw

target = Path(__file__).resolve().parent / "assets"
target.mkdir(exist_ok=True)
pic = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
d = ImageDraw.Draw(pic)
d.rounded_rectangle((8, 8, 248, 248), radius=62, fill="#10203b")
d.rounded_rectangle((21, 21, 235, 235), radius=51, outline="#42d9ff", width=6)
d.rounded_rectangle((76, 46, 182, 208), radius=15, fill="#e6f7ff")
d.polygon([(152, 46), (182, 76), (152, 76)], fill="#84b7db")
for y in (102, 134, 166):
    d.rounded_rectangle((93, y, 163, y + 8), radius=4, fill="#658cb7")
d.ellipse((162, 154, 238, 230), fill="#4ce1b2")
d.polygon([(188, 172), (188, 212), (217, 192)], fill="#10203b")
pic.save(target / "slidevoice.ico", format="ICO",
         sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
