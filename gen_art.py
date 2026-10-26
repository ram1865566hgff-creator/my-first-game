from PIL import Image, ImageDraw, ImageFilter
import math, random, os, struct, wave
R=random.Random(14938)
OUT=os.environ.get('ART_OUT','/mnt/data/Ironfront/assets');os.makedirs(OUT,exist_ok=True)
W,H=1536,720
PALETTES=[{'sky':(7,14,34),'horizon':(27,58,75),'far':(16,46,64),'mid':(10,33,45),'near':(5,24,33),'lum':(89,255,205),'other':(235,125,76)},
{'sky':(15,10,38),'horizon':(72,29,68),'far':(37,28,68),'mid':(22,22,55),'near':(10,19,40),'lum':(46,216,255),'other':(255,57,158)},
{'sky':(16,12,32),'horizon':(77,33,34),'far':(59,31,44),'mid':(35,25,42),'near':(19,21,38),'lum':(247,184,71),'other':(247,72,75)}]
def grad(c0,c1,y):
 t=max(0,min(1,y/H));return tuple(int(a*(1-t)+b*t) for a,b in zip(c0,c1))
def glow(img,x,y,r,c,strength=165):
 a=Image.new('RGBA',img.size,(0,0,0,0));d=ImageDraw.Draw(a)
 for k in range(6,0,-1):
  rr=int(r*(k/2.5)); op=int(strength/(k*2.1));d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*c,min(op,255)))
 a=a.filter(ImageFilter.GaussianBlur(max(4,r//5)))
 img.alpha_composite(a)
def fog_layer(img,tint, y0=430,alpha=40):
 d=ImageDraw.Draw(img,'RGBA');R2=random.Random(221)
 for i in range(105):
  x=R2.randrange(W);y=y0+R2.randrange(-120,115);rx=R2.randrange(40,180);ry=R2.randrange(8,38)
  d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=(*tint,alpha//(1+i%3)))
def hills(d,seed,color,base=450,amp=90,detail=14):
 rr=random.Random(seed);points=[(-60,H)];u=-60
 while u<W+100:
  points.append((u,base+rr.randint(-amp,amp)));u+=rr.randint(55,165)
 points.extend([(W+100,H)]);d.polygon(points,fill=color)
def leafcluster(d,x,y,size,p,shine):
 for j in range(28):
  a=2*math.pi*j/28; rr=size*(.3+.65*R.random());ex=x+math.cos(a)*rr;ey=y+math.sin(a)*rr*.48
  d.ellipse((ex-size*.18,ey-size*.12,ex+size*.2,ey+size*.12),fill= p if j%5 else shine)
def jungle(bg,lay,p):
 d=ImageDraw.Draw(bg,'RGBA')
 if lay==1:
  hills(d,32,(*p['far'],240),430,63);hills(d,37,(10,42,58,225),505,48)
  fog_layer(bg,p['lum'],456,12)
 if lay==2:
  for x in range(-50,W+100,100):
   x+=R.randint(-25,25);height=R.randint(230,410)
   d.polygon([(x-11,600),(x+16,600),(x+11,590-height),(x,580-height)],fill=(13,38,38,255))
   for zz in range(6):
    yy=590-height+zz*28;d.line([(x,yy),(x-35+R.randint(-12,12),yy-28)],fill=(11,35,39,255),width=7)
   leafcluster(d,x,555-height,49,(15,65,54,245),(19,94,68,255))
 if lay==3:
  for x in range(-80,W+100,165):
   x+=R.randrange(-42,42);h=R.randint(270,425)
   d.polygon([(x-22,680),(x+26,680),(x+14,660-h),(x-12,640-h)],fill=(5,27,30,255))
   for j in range(7):
    yy=670-h+j*45;d.line((x,yy,x+(-1)**j*R.randint(45,95),yy-49),fill=(7,39,36,255),width=9)
   leafcluster(d,x,630-h,66,(9,62,54,250),(22,111,76,255))
  for x in range(60,W,230):
   d.line([(x,0),(x-30,112),(x-8,225)],fill=(13,73,63,220),width=6)
   for y in range(90,220,28):
    d.ellipse((x-45,y-8,x-16,y+5), fill=(18,82,65,200))
 if lay==4:
  for x in range(-40,W+80,44):
   y=R.randint(565,630);h=R.randint(24,96);color=(12,R.randrange(70,125),65,205)
   for j in range(4):
    dx=R.randint(-30,30);d.polygon([(x,y),(x+dx,y-h),(x+dx+R.randint(10,24),y-h//2)],fill=color)
  for x in range(0,W,230):
   if x%2:glow(bg,x,600,10,p['lum'],45)
def city(bg,lay,p):
 d=ImageDraw.Draw(bg,'RGBA')
 if lay==1:
  for x in range(-40,W+50,55):
   hei=R.randrange(100,290);wide=R.randrange(45,100);d.rectangle((x,565-hei,x+wide,570),fill=(34,35,78,220))
   for yy in range(576-hei,560,16):
    for xx in range(x+8,x+wide-6,13):
     if R.random()>.55:d.rectangle((xx,yy,xx+4,yy+7),fill=(*p['lum'],R.randrange(25,90)))
 if lay==2:
  for x in range(-25,W+70,125):
   ht=R.randrange(200,400);wd=R.randrange(90,165)
   d.polygon([(x,620),(x,615-ht),(x+wd-12,615-ht),(x+wd,620)], fill=(15,24,59,245))
   d.rectangle((x,615-ht,x+wd,620),outline=(55,79,109,120),width=3)
   for yy in range(630-ht,580,23):
    for xx in range(x+9,x+wd-10,20):
     if R.random()>.29:d.rectangle((xx,yy,xx+9,yy+12),fill=(*[p['lum'],p['other']][R.randrange(2)],R.randrange(70,150)))
   if R.random()>.52:
    d.rectangle((x+7,615-ht+40,x+wd-10,615-ht+83),fill=(*p['other'],92),outline=(*p['other'],210),width=2)
    d.line((x+13,615-ht+60,x+wd-20,615-ht+60),fill=(233,182,255,180),width=3)
 if lay==3:
  for x in range(-60,W+50,190):
   ht=R.randrange(250,440);wd=R.randrange(130,235)
   d.rectangle((x,640-ht,x+wd,640),fill=(8,19,38,253),outline=(36,92,113,250),width=4)
   for yy in range(655-ht,620,37):
    d.line((x+5,yy,x+wd-5,yy),fill=(27,55,82,200),width=3)
    for xx in range(x+12,x+wd-13,29):
     if R.random()>.35:d.rectangle((xx,yy+8,xx+14,yy+22),fill=(*p['lum'],R.randrange(50,145)))
   d.line((x+wd-10,640-ht,x+wd-10,580),fill=(*p['other'],160),width=4)
 if lay==4:
  for x in range(0,W,225):
   d.line((x+20,0,x+20,420),fill=(20,32,53,210),width=9)
   d.line((x+20,350,x+60,365),fill=(*p['lum'],110),width=3)
  for x in range(100,W,370):
   d.rectangle((x,480,x+185,515),fill=(12,22,43,220),outline=(*p['other'],200),width=2)
   d.line((x+15,496,x+145,496),fill=(*p['lum'],200),width=3)
def reactor(bg,lay,p):
 d=ImageDraw.Draw(bg,'RGBA')
 if lay==1:
  for x in range(-120,W+200,260):
   y=R.randrange(220,350);d.ellipse((x-100,y-125,x+120,y+100),fill=(66,36,54,235),outline=(150,61,71,120),width=6)
   d.ellipse((x-55,y-55,x+70,y+64),fill=(21,23,45,220),outline=(*p['other'],90),width=9)
 if lay==2:
  for x in range(-50,W+200,240):
   d.rectangle((x,175,x+R.randrange(170,255),610),fill=(37,29,49,250),outline=(105,66,70,220),width=8)
   for xx in range(x+20,x+220,55):
    d.line((xx,165,xx,620),fill=(16,18,34,230),width=22)
    d.line((xx-4,165,xx-4,620),fill=(119,63,69,130),width=3)
   for yy in (217,330,465):d.line((x,yy,x+221,yy),fill=(147,69,67,160),width=10)
 if lay==3:
  for x in range(-30,W+100,205):
   d.rectangle((x,310,x+185,622),fill=(14,22,39,248),outline=(67,64,74,255),width=6)
   for yy in range(330,618,43):
    d.rectangle((x+15,yy,x+168,yy+22),fill=(34,41,58,255),outline=(95,73,76,190),width=3)
   d.ellipse((x+47,364,x+135,446),fill=(9,26,44,255),outline=(*p['other'],180),width=8)
   d.ellipse((x+74,390,x+110,426),fill=(*p['lum'],135))
 if lay==4:
  for x in range(-15,W+30,125):
   d.line((x,0,x,710),fill=(15,18,35,190),width=18)
   d.line((x+11,0,x+11,710),fill=(96,76,80,150),width=3)
  for x in range(0,W,335):
   d.ellipse((x+55,510,x+91,546),fill=(*p['other'],155));glow(bg,x+73,527,9,p['other'],70)
def create_bg(stage):
 global R
 p=PALETTES[stage];root=os.path.join(OUT,'bg'+str(stage));os.makedirs(root,exist_ok=True)
 sky=Image.new('RGBA',(W,H));pixels=sky.load()
 for y in range(H):
  col=grad(p['sky'],p['horizon'],y*1.32)
  for x in range(W):
   v=math.sin(x*.003+stage)*4+math.sin((x+y)*.011)*3
   pixels[x,y]=tuple(max(0,min(255,int(c+v))) for c in col)+(255,)
 sd=ImageDraw.Draw(sky,'RGBA')
 for n in range(130):
  x=R.randrange(W);y=R.randrange(460);rs=R.choice((1,1,1,2));sd.ellipse((x-rs,y-rs,x+rs,y+rs),fill=(*p['lum'],R.randrange(35,110)))
 if stage==0:
  glow(sky,1110,135,58,(104,255,212),100)
  sd.ellipse((1064,92,1155,183),fill=(201,240,204,255))
  sd.ellipse((1092,78,1180,165),fill=(*p['sky'],255))
 elif stage==1:
  glow(sky,1070,240,103,(250,74,171),210)
  sd.ellipse((990,159,1150,316),fill=(243,79,142,255))
  for y in range(162,315,14):sd.line((990,y,1150,y),fill=(75,31,70,130),width=4)
 else:
  glow(sky,1120,245,100,p['other'],110)
  sd.ellipse((1060,185,1190,312),fill=(215,83,64,255))
  sd.ellipse((1090,164,1210,270),fill=(*p['sky'],255))
 sky.convert('RGB').save(os.path.join(root,'0.jpg'),quality=87,optimize=True)
 for lay in range(1,5):
  R=random.Random(2317+stage*109+lay*7)
  bg=Image.new('RGBA',(W,H));
  [jungle,city,reactor][stage](bg,lay,p)
  bg.save(os.path.join(root,str(lay)+'.png'),optimize=True)
 print('generated',stage)

def draw_hero(d,ox,oy,n,palette,scale=1):
 # Original angular sci-fi trooper sprite drawn in layered pieces with animated articulated limbs
 cx=ox+70;by=oy+144; phase=n*2*math.pi/8; stride=math.sin(phase)*14
 if n==8:stride=-9
 if n==9:stride=0
 C={
 'blue':((25,51,73),(41,97,120),(54,230,239),(233,245,224),(9,21,32)),
 'red':((77,39,58),(156,53,79),(255,104,87),(255,228,195),(31,20,34)),
 'purple':((53,38,80),(99,58,136),(188,93,255),(242,221,250),(22,20,37)),
 }[palette]
 dark,mid,neon,skin,edge=C
 # soft shadow
 d.ellipse((cx-32,by-9,cx+35,by+1),fill=(3,13,20,75))
 # scarf flowing backward
 sway=int(math.sin(phase)*6)
 d.polygon([(cx-13,oy+56),(cx-32,oy+53+sway),(cx-60,oy+65+sway),(cx-33,oy+67+sway),(cx-12,oy+65)],fill=(167,46,69,225))
 # legs and boots, dynamic angles
 for k in (-1,1):
  xx=cx+(k*11);s=stride*k
  kne=(xx+s*.85,oy+112-abs(s)*.32)
  foot=(xx+s*1.3,oy+135-abs(s)*.32)
  d.line((xx,oy+93,*kne),fill=edge,width=23)
  d.line((xx,oy+93,*kne),fill=mid,width=15)
  d.line((*kne,*foot),fill=dark,width=20)
  d.line((*kne,*foot),fill=mid,width=11)
  d.polygon([(foot[0]-14,foot[1]-4),(foot[0]+12,foot[1]-3),(foot[0]+18,foot[1]+6),(foot[0]-17,foot[1]+6)],fill=edge)
  d.line((foot[0]-10,foot[1]+3,foot[0]+12,foot[1]+3),fill=neon,width=3)
 # chest shadow and body
 d.polygon([(cx-24,oy+56),(cx+23,oy+53),(cx+29,oy+100),(cx-20,oy+100)],fill=edge)
 d.polygon([(cx-23,oy+56),(cx+21,oy+55),(cx+26,oy+92),(cx-18,oy+93)],fill=dark)
 d.polygon([(cx-18,oy+62),(cx+16,oy+61),(cx+19,oy+82),(cx-13,oy+88)],fill=mid)
 d.polygon([(cx-4,oy+65),(cx+10,oy+64),(cx+5,oy+76),(cx-4,oy+77)],fill=neon)
 d.line((cx-12,oy+90,cx+20,oy+85),fill=(100,137,150),width=4)
 # arm behind barrel
 d.line((cx+17,oy+66,cx+39,oy+79),fill=edge,width=18)
 d.line((cx+17,oy+66,cx+37,oy+77),fill=mid,width=11)
 # head helmet
 d.ellipse((cx-19,oy+22,cx+17,oy+61),fill=edge)
 d.polygon([(cx-20,oy+36),(cx-15,oy+18),(cx+11,oy+12),(cx+23,oy+27),(cx+20,oy+48),(cx-12,oy+55)],fill=dark)
 d.polygon([(cx-17,oy+29),(cx+12,oy+22),(cx+20,oy+31),(cx+15,oy+39),(cx-17,oy+41)],fill=mid)
 d.polygon([(cx-9,oy+34),(cx+19,oy+31),(cx+13,oy+40),(cx-12,oy+45)],fill=neon)
 d.line((cx-9,oy+36,cx+9,oy+34),fill=skin,width=3)
 d.line((cx-15,oy+49,cx+5,oy+52),fill=(59,89,110),width=3)
 # front arm, large rifle
 d.line((cx-18,oy+64,cx+19,oy+77),fill=edge,width=17)
 d.line((cx-17,oy+63,cx+18,oy+76),fill=mid,width=11)
 d.polygon([(cx+10,oy+68),(cx+55,oy+66),(cx+69,oy+73),(cx+63,oy+84),(cx+13,oy+86)],fill=edge)
 d.polygon([(cx+17,oy+71),(cx+57,oy+70),(cx+64,oy+76),(cx+19,oy+81)],fill=dark)
 d.line((cx+37,oy+70,cx+59,oy+71),fill=neon,width=3)
 d.line((cx+28,oy+84,cx+31,oy+96),fill=mid,width=9)
 if n==9:d.ellipse((cx+62,oy+65,cx+82,oy+88), fill=(*neon,120))

def sprite_sheets():
 for p in ('blue','red','purple'):
  im=Image.new('RGBA',(140*10,156),(0,0,0,0));d=ImageDraw.Draw(im,'RGBA')
  for i in range(10):draw_hero(d,i*140,0,i,p)
  im.save(os.path.join(OUT,'soldier_'+p+'.png'),optimize=True)

def boss_art():
 for z,c in enumerate([(76,255,224),(255,81,174),(255,189,84)]):
  im=Image.new('RGBA',(460,330));d=ImageDraw.Draw(im,'RGBA')
  ed=(13,24,41);metal=(32+z*8,53,77);light=(102+z*23,128,140)
  # engine legs
  for x in (115,340):
   d.polygon([(x-33,185),(x+25,188),(x+56,267),(x+8,316),(x-28,292)],fill=ed)
   d.polygon([(x-15,198),(x+15,201),(x+39,268),(x,286)],fill=metal)
   d.line((x-15,205,x+13,240), fill=c,width=8)
  # huge body with mechanical detail
  d.polygon([(56,96),(146,39),(296,34),(398,99),(427,172),(357,223),(118,234),(36,181)],fill=ed)
  d.polygon([(78,104),(150,52),(303,49),(379,109),(399,166),(353,207),(116,212),(64,171)],fill=metal)
  d.polygon([(157,68),(287,65),(330,104),(127,104)],fill=light)
  d.polygon([(115,122),(345,122),(362,170),(337,198),(130,194),(96,170)],fill=(11,21,36))
  for x in (92,363):
   d.ellipse((x-46,116,x+45,206), fill=ed,outline=light,width=9)
   d.ellipse((x-23,139,x+22,183),fill=c)
  d.ellipse((165,90,302,219),fill=ed,outline=light,width=9)
  d.ellipse((181,108,286,202),fill=c)
  d.ellipse((204,127,263,184),fill=(247,249,227))
  for yy in (63,83,107,196):
   d.line((127,yy,332,yy),fill=light,width=4)
  for x in (118,333):
   d.polygon([(x-13,205),(x+15,202),(x+30,218),(x-20,234)],fill=light)
   d.line((x-20,226,x-60,235),fill=c,width=8)
  im.save(os.path.join(OUT,'boss'+str(z)+'.png'),optimize=True)

def wav(name,duration,notes,kind):
 rate=22050;N=int(rate*duration);samples=[]
 for i in range(N):
  t=i/rate; env=(1-t/duration)**(1.8 if kind!='boom' else .9)
  f=notes[0]+(notes[-1]-notes[0])*(t/duration)
  val=(math.sin(t*math.pi*2*f)*.42+math.sin(t*math.pi*4*f)*.16+random.Random(i+176).uniform(-1,1)*(.35 if kind=='boom' else .13))*env
  samples.append(int(max(-1,min(1,val)) * 10000))
 with wave.open(os.path.join(OUT,name+'.wav'),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(struct.pack('<'+'h'*len(samples),*samples))
for i in range(3):create_bg(i)
sprite_sheets();boss_art()
for name,dur,notes,kind in [('fire',.17,[520,128],'zap'),('enemyfire',.23,[280,95],'zap'),('jump',.22,[180,420],'jump'),('hit',.22,[130,50],'boom'),('explode',.82,[80,35],'boom'),('pick',.28,[540,910],'jump'),('dash',.35,[170,610],'zap'),('boss',.67,[190,49],'boom')]:wav(name,dur,notes,kind)
print('TOTAL ASSET BYTES',sum(os.path.getsize(os.path.join(dp,n)) for dp,_,names in os.walk(OUT) for n in names))
# Music: original synthesized looping dark-wave / retro sci-fi action bed, no third-party samples.
import array
sr=22050;duration=24;N=sr*duration;out=array.array('h');roots=[55,55,65.406,49,55,73.42,65.406,49]
for i in range(N):
 t=i/sr;beat=t*(124/60); step=int(beat*2);n=step//8;root=roots[n%len(roots)];q=beat%1
 sub=(math.sin(2*math.pi*root*t)+.28*math.sin(2*math.pi*2*root*t))*.24
 leadfreq=root*4*(2**([0,3,7,10,7,3,10,12][step%8]/12));
 gate=max(0,1-(beat*2)%1)**2
 lead=(math.sin(2*math.pi*leadfreq*t)+.3*math.sin(2*math.pi*leadfreq*2*t))*gate*.19
 kick=math.sin(2*math.pi*(71-45*(q/.33))*t)*(.55*math.exp(-q*18)) if q<.34 else 0
 hat=(math.sin(t*21801)*math.sin(t*45367))*.044*math.exp(-((beat*4)%1)*10)
 pad=.05*(math.sin(2*math.pi*root*2*t)+math.sin(2*math.pi*(root*3.005)*t))
 vol= min(1, t*.75,(duration-t)*.85)
 v=(sub+lead+kick+hat+pad)*max(0,vol)
 out.append(int(max(-1,min(1,v))*13000))
with wave.open(os.path.join(OUT,'music.wav'),'wb') as a:
 a.setnchannels(1);a.setsampwidth(2);a.setframerate(sr);a.writeframes(out.tobytes())
print('WITH MUSIC',sum(os.path.getsize(os.path.join(dp,n)) for dp,_,names in os.walk(OUT) for n in names))