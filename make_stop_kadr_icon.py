"""Draw a professional Stop Kadr app icon (video/voice/play/pause)."""
from PIL import Image,ImageDraw
from pathlib import Path
S=512
im=Image.new("RGBA",(S,S),(0,0,0,0))
d=ImageDraw.Draw(im)
for y in range(S):
    t=y/511
    d.line((12,y,499,y),fill=(int(12+3*t),int(100-72*t),int(231-127*t),255))
mask=Image.new("L",(S,S),0)
ImageDraw.Draw(mask).rounded_rectangle((13,13,499,499),radius=108,fill=255)
im.putalpha(mask)
d=ImageDraw.Draw(im)
d.rounded_rectangle((22,22,491,491),radius=100,outline="#64c6ff",width=8)
d.rounded_rectangle((67,108,442,362),radius=27,fill="#081d50",outline="#b3e9ff",width=12)
for y in (136,205,274):
    for x in (82,410):
        d.rounded_rectangle((x,y,x+23,y+26),radius=5,fill="#42aefa")
d.polygon(((154,170),(154,310),(262,240)),fill="#e5f8ff")
d.rounded_rectangle((277,163,310,307),radius=7,fill="#ff5366")
d.rounded_rectangle((333,163,366,307),radius=7,fill="#ff5366")
d.ellipse((303,302,455,456),fill="#061943")
d.rounded_rectangle((359,322,399,405),radius=20,fill="#d5f5ff")
d.arc((338,342,421,443),0,180,fill="#a5ddff",width=13)
d.line((380,443,380,455),fill="#a5ddff",width=11)
d.line((352,457,408,457),fill="#a5ddff",width=9)
folder=Path(__file__).resolve().parent/"stop_kadr_assets"
folder.mkdir(exist_ok=True)
im.resize((256,256),Image.Resampling.LANCZOS).save(folder/"stop_kadr.png")
im.save(folder/"stop_kadr.ico",format="ICO",sizes=[
(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Icon ready")
