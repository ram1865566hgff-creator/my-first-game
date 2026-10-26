package com.ironfront.assault;

import android.app.Activity;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.media.AudioAttributes;
import android.media.SoundPool;
import android.media.MediaPlayer;
import android.content.res.AssetFileDescriptor;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowManager;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Random;

public class MainActivity extends Activity {
  Game game;
  @Override public void onCreate(Bundle b) {
    super.onCreate(b); getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
    immersive(); game = new Game(this); setContentView(game);
  }
  private void immersive() {getWindow().getDecorView().setSystemUiVisibility(
      5894 | View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);}
  @Override public void onWindowFocusChanged(boolean focus) {super.onWindowFocusChanged(focus);if(focus) immersive();}
  @Override protected void onPause() {super.onPause();if(game!=null)game.halt();}
  @Override protected void onResume() {super.onResume();if(game!=null)game.resume();}
  @Override public void onBackPressed(){if(game!=null)game.back();}

  static class Enemy {
    float x,y,vx,baseY,shoot=0,phase=0,hp,maxhp,invuln=0;
    int type,points=200;boolean dead=false;
    Enemy(float xx,float yy,int tt,int hp0){x=xx;y=yy;baseY=yy;type=tt;hp=maxhp=hp0;phase=xx/101f;}
  }
  static class Shot {
    float x,y,vx,vy,life;int type;float power,r;
    Shot(float xx,float yy,float a,float speed,int ty,float pp){x=xx;y=yy;vx=(float)Math.cos(a)*speed;vy=(float)Math.sin(a)*speed;type=ty;power=pp;life=ty==3?2.2f:1.7f;r=ty==3?13:ty==2?9:ty==1?8:5;}
  }
  static class Particle {
    float x,y,vx,vy,life,max,size;int color,type;
    Particle(float xx,float yy,float dx,float dy,float dur,float rad,int col,int ty){x=xx;y=yy;vx=dx;vy=dy;life=max=dur;size=rad;color=col;type=ty;}
  }
  static class Item {
    float x,y,phase=0;int type;boolean picked=false;
    Item(float xx,float yy,int t){x=xx;y=yy;type=t;}
  }
  static class Platform {float x,y,w; Platform(float xx,float yy,float ww){x=xx;y=yy;w=ww;}}
  static class Game extends SurfaceView implements SurfaceHolder.Callback, Runnable {
    static final int MENU=0,PLAY=1,PAUSE=2,DEAD=3,WIN=4;
    static final float GW=1280,GH=720,GROUND=569,LEVEL_LEN=9000;
    static final int[] ACC={0xff5ef5cb,0xff53ddff,0xffffbf68};
    static final String[] AREA={"THE OBSIDIAN JUNGLE","NEON EXODUS","THE LAST REACTOR"};
    final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG), text=new Paint(Paint.ANTI_ALIAS_FLAG),rPaint=new Paint(Paint.ANTI_ALIAS_FLAG);
    final Random rnd=new Random(3874); final ArrayList<Enemy> enemies=new ArrayList<>();final ArrayList<Shot> bullets=new ArrayList<>();final ArrayList<Particle> particles=new ArrayList<>();
    final ArrayList<Item> items=new ArrayList<>();final ArrayList<Platform> platforms=new ArrayList<>();
    Bitmap[][] scenery=new Bitmap[3][5];Bitmap[] troops=new Bitmap[3],bossArt=new Bitmap[3];SoundPool sound;MediaPlayer music;int[] soundId=new int[8];
    final int WHITE=Color.WHITE; volatile boolean active=false,ready=false;Thread thread; int mode=MENU,stage=0,levelStart=0;
    float x=100,y=GROUND,vx=0,vy=0,camera=0,health=100,invinc=0,time=0,shootCooldown=0,dashCooldown=0,dashTime=0,shake=0,aim=0;
    float bossHP=250,bossMax=250,bossFire=0, bossPhase=0,checkpoint=100,stageIntro=2.0f,transitionTimer=0;int nextStage=-1;
    float joyX=0,joyY=0; int jumps=0,score=0,grenades=4,weapon=0,combo=0; boolean movingLeft=false,movingRight=false,firing=false,bossAlive=true,muted=false;
    int joystickId=-1,fireId=-1,jumpId=-1,dashId=-1,grenadeId=-1; boolean menuDown=false;
    long lastNano=0;float pixelW=1280,pixelH=720;
    Game(Context c){super(c);setFocusable(true);getHolder().addCallback(this);loadArt(c);initAudio(c);setup(0,false);mode=MENU;ready=true;}
    void loadArt(Context c){
      BitmapFactory.Options opt=new BitmapFactory.Options();opt.inScaled=false;
      for(int z=0;z<3;z++){
        for(int j=0;j<5;j++)try{scenery[z][j]=BitmapFactory.decodeStream(c.getAssets().open("bg"+z+"/"+j+(j==0?".jpg":".png")),null,opt);}catch(Exception ignored){}
        try{bossArt[z]=BitmapFactory.decodeStream(c.getAssets().open("boss"+z+".png"),null,opt);}catch(Exception ignored){}
      }
      for(int z=0;z<3;z++)try{troops[z]=BitmapFactory.decodeStream(c.getAssets().open("soldier_"+new String[]{"blue","red","purple"}[z]+".png"),null,opt);}catch(Exception ignored){}
    }
    void initAudio(Context c){try{
      sound=new SoundPool.Builder().setMaxStreams(9).setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()).build();
      String[] names={"fire","enemyfire","jump","hit","explode","pick","dash","boss"};
      for(int i=0;i<names.length;i++)soundId[i]=sound.load(c.getAssets().openFd(names[i]+".wav"),1);

      try { AssetFileDescriptor afd=c.getAssets().openFd("music.wav");music=new MediaPlayer();music.setDataSource(afd.getFileDescriptor(),afd.getStartOffset(),afd.getLength());afd.close();music.setLooping(true);music.setVolume(.20f,.20f);music.prepare();music.start();}catch(Exception ignored){music=null;}
    }catch(Exception ignored){sound=null;}}
    void snd(int i,float v){if(!muted&&sound!=null&&i>=0&&i<soundId.length)try{sound.play(soundId[i],v,v,0,0,1f);}catch(Exception ignored){}}
    @Override public void surfaceCreated(SurfaceHolder h){resume();}
    @Override public void surfaceChanged(SurfaceHolder h,int f,int w,int hh){}
    @Override public void surfaceDestroyed(SurfaceHolder h){halt();}
    synchronized void resume(){if(active)return;active=true;if(music!=null&&!music.isPlaying()&&!muted)music.start();lastNano=0;thread=new Thread(this,"IronFrontGameThread");thread.start();}
    synchronized void halt(){active=false;if(music!=null&&music.isPlaying())music.pause();Thread t=thread;if(t!=null&&t!=Thread.currentThread())try{t.join(450);}catch(InterruptedException ignored){} thread=null;if(mode==PLAY)mode=PAUSE;}
    void back(){if(mode==PLAY)mode=PAUSE;else if(mode==PAUSE)mode=PLAY;else if(mode==MENU){}else mode=MENU;}
    void setup(int s,boolean retain){stage=s;levelStart=s;mode=PLAY;x=90;y=GROUND;vx=vy=0;camera=0;health=100;invinc=1.7f;bossAlive=true;bossMax=260+stage*95;bossHP=bossMax;
      time=0;shootCooldown=0;dashCooldown=0;dashTime=0;nextStage=-1;transitionTimer=0;bossFire=1;bossPhase=0;stageIntro=2.5f;checkpoint=100;jumps=0;grenades=4;weapon=0;combo=0;
      if(!retain)score=0;enemies.clear();bullets.clear();particles.clear();items.clear();platforms.clear();
      Random r=new Random(92081+stage*86);
      for(int i=0;i<27;i++){
        float px=480+i*295+r.nextInt(75);float py= 444- r.nextInt(3)*62;float wd=125+r.nextInt(120);
        if(i%5!=3)platforms.add(new Platform(px,py,wd));
      }
      for(float i=500;i<LEVEL_LEN-950;i+=255+r.nextInt(210)){
        int t=r.nextInt(10)<4?0:r.nextInt(10)<5?1:r.nextInt(10)<6?2:3;
        float ey=t==1?270+r.nextInt(100):GROUND;
        enemies.add(new Enemy(i,ey,t,t==3?85:(t==2?65:30)+stage*6));
      }
      for(int i=0;i<12;i++)items.add(new Item(670+i*650,460-r.nextInt(175),i%5==0?1:i%4==0?2:i%3==0?3:0));
    }
    @Override public void run(){
      while(active){long tick=System.nanoTime();float dt=lastNano==0?0.016f:Math.min(0.032f,(tick-lastNano)/1e9f);lastNano=tick;
        if(ready && mode==PLAY)update(dt);
        Canvas c=null;try{if(getHolder().getSurface().isValid()){c=getHolder().lockCanvas();if(c!=null)render(c);}}
        catch(Exception ignored){}finally{if(c!=null)try{getHolder().unlockCanvasAndPost(c);}catch(Exception ignored){}}
        long ms=(System.nanoTime()-tick)/1000000;if(ms<16)try{Thread.sleep(16-ms);}catch(InterruptedException ignored){}
      }
    }
    float clamp(float value,float a,float b){return Math.max(a,Math.min(b,value));}
    void update(float dt){time+=dt;if(nextStage>=0){transitionTimer-=dt;if(transitionTimer<=0){int st=nextStage;setup(st,true);return;}}stageIntro=Math.max(0,stageIntro-dt);invinc=Math.max(0,invinc-dt);shootCooldown-=dt;dashCooldown=Math.max(0,dashCooldown-dt);shake=Math.max(0,shake-dt*15);bossPhase+=dt;
      float input=(movingRight?1:0)-(movingLeft?1:0); if(joystickId!=-1)input=clamp(joyX,-1,1);
      float desired=input*360;vx+=(desired-vx)*Math.min(1,dt*(Math.abs(input)>.1?14:11));
      if(dashTime>0){dashTime-=dt;vx=(input>=0?1:-1)*770; if(rnd.nextBoolean()) spark(x-vx*.03f,y-63,ACC[stage],3);}
      float oldY=y;vy+=1700*dt;vy=clamp(vy,-1010,1150);x+=vx*dt;y+=vy*dt;
      x=clamp(x,34,LEVEL_LEN-135);
      boolean landing=false;
      if(y>=GROUND){y=GROUND;landing=true;}
      if(vy>=0)for(Platform pl:platforms){if(x>pl.x-35&&x<pl.x+pl.w+35 && oldY<=pl.y+6&&y>=pl.y&&y<pl.y+50){y=pl.y;landing=true;}}
      if(landing){if(vy>300)for(int i=0;i<7;i++)spawn(x+rnd.nextInt(40)-20,y, rnd.nextInt(190)-95,-rnd.nextInt(120),.38f,3,0xff83cbb3,1);vy=0;jumps=0;}
      if(y>900){health=0;mode=DEAD;}
      if(firing&&shootCooldown<=0)fire();
      for(int i=bullets.size()-1;i>=0;i--){Shot b=bullets.get(i);float lastX=b.x,lastY=b.y;b.x+=b.vx*dt;b.y+=b.vy*dt;
        if(b.type==3)b.vy+=730*dt;b.life-=dt;
        boolean remove=b.life<=0||b.y>700;
        if(b.type==3 &&(b.y>=GROUND-12 || (b.vy>0&&b.y>550))){explosion(b.x,b.y,85,65,true);remove=true;}
        if(b.type<=0||b.type==3){
          if(b.x>LEVEL_LEN-575&&bossAlive&&Math.abs(b.y-(GROUND-158))<170&&b.x>LEVEL_LEN-675){bossHP-=b.power;impact(b.x,b.y,0xffffb78d);remove=true;if(bossHP<=0)killBoss();}
          for(Enemy e:enemies){if(e.dead||Math.abs(e.x-b.x)>42+(e.type==3?14:0)||Math.abs((e.y-(e.type==1?0:67))-b.y)>60)continue;
            e.hp-=b.power;e.invuln=.13f;impact(b.x,b.y,0xfff9c27f);remove=true;
            if(e.hp<=0){e.dead=true;score+=e.points;combo++;explosion(e.x,e.y-55,36,22,false);if(rnd.nextFloat()<.15)items.add(new Item(e.x,e.y-55,0));}
            break;
          }
        }else if(invinc<=0&&Math.abs(b.x-x)<30 && Math.abs(b.y-(y-65))<63){takeDamage(b.power);remove=true;}
        if(remove)bullets.remove(i);
      }
      for(Enemy e:enemies){if(e.dead || e.x<camera-180 || e.x>camera+GW+350)continue;
        e.phase+=dt*(e.type==1?4:2);e.invuln=Math.max(0,e.invuln-dt);
        if(e.type==0||e.type==3){e.x+=((x>e.x)?1:-1)*dt*(e.type==3?42:69);e.y=GROUND;}
        if(e.type==1)e.y=e.baseY+(float)Math.sin(e.phase)*35;
        e.shoot-=dt;
        if(e.shoot<=0&&e.x>camera+90 &&Math.abs(e.x-x)<790){
          float ex=e.x,ey=e.y-(e.type==1?0:e.type==2?77:79);
          float a=(float)Math.atan2(y-67-ey,x-ex);
          if(e.type==3){for(int j=-1;j<=1;j++)enemyBullet(ex,ey,a+j*.15f,e.type);}
          else enemyBullet(ex,ey,a,e.type);
          e.shoot=e.type==3?2.0f:e.type==2?1.55f:e.type==1?2.2f:2.4f;
        }
        if(invinc<=0&&Math.abs(x-e.x)<32&&Math.abs(y-e.y)<62)takeDamage(12);
      }
      if(bossAlive&&x>LEVEL_LEN-1140){bossFire-=dt;if(bossFire<=0){
        float bx=LEVEL_LEN-450,by=GROUND-155;float a=(float)Math.atan2(y-70-by,x-bx);
        for(int k=-2;k<=2;k++)enemyBullet(bx-105,by,a+k*.19f,3);
        bossFire=1.6f-stage*.2f;
      }}
      for(Item it:items)if(!it.picked){it.phase+=dt*3;if(Math.abs(it.x-x)<52&&Math.abs(it.y-(y-65))<73){
        it.picked=true;score+=150;snd(5,.6f);glow(it.x,it.y,ACC[stage],24);
        if(it.type==0)health=Math.min(100,health+27);if(it.type==1)weapon=(weapon+1)%3;
        if(it.type==2)grenades+=2;if(it.type==3){health=Math.min(100,health+15);grenades++;}
      }}
      for(int i=particles.size()-1;i>=0;i--){Particle a=particles.get(i);a.x+=a.vx*dt;a.y+=a.vy*dt;a.vy+=(a.type==1?450:a.type==2?-120:100)*dt;a.life-=dt;if(a.life<=0)particles.remove(i);}
      if(rnd.nextFloat()<dt*(stage==1?130:stage==0?14:45)){float xx=camera+rnd.nextInt(1550),yy=rnd.nextInt(700);spawn(xx,yy,stage==1?-160:-26,stage==1?650:80,stage==1?1.1f:2.4f,stage==1?1:2,stage==1?0xff70bde9:ACC[stage],stage==1?3:2);}
      camera+=(clamp(x-375,0,LEVEL_LEN-1280)-camera)*Math.min(1,dt*6.5f);
      if(x>LEVEL_LEN-750)checkpoint=Math.max(checkpoint,LEVEL_LEN-990);else if(x-checkpoint>1500)checkpoint=x-250;
    }
    void fire(){shootCooldown=weapon==2?.12f:weapon==1?.28f:.16f;
      float sign=(movingLeft&&!movingRight)?-1:1;float aa=aim+(sign<0?(float)Math.PI:0);float px=x+sign*53,py=y-79;
      if(weapon==1){for(int j=-1;j<=1;j++)bullets.add(new Shot(px,py,aa+j*.16f,820,0,11));}
      else bullets.add(new Shot(px,py,aa,weapon==2?1220:990,0,weapon==2?18:15));
      for(int j=0;j<3;j++)spawn(px,py,rnd.nextInt(180)-25,-rnd.nextInt(170),.2f,3,0xffffc56b,0);
      snd(0,.3f);if(rnd.nextFloat()<.2f)shake=Math.max(shake,1.5f);
    }
    void enemyBullet(float sx,float sy,float angle,int type){Shot b=new Shot(sx,sy,angle,type==3?365:420, type==3?2:1,type==3?11:8);bullets.add(b);snd(1,.16f);}
    void jump(){if(jumps>=2)return;vy=jumps==0?-745:-675;jumps++;snd(2,.50f);
      for(int i=0;i<11;i++)spawn(x+rnd.nextInt(34)-17,y,rnd.nextInt(200)-100,rnd.nextInt(180),.4f,3,ACC[stage],1);
    }
    void dash(){if(dashCooldown>0)return;dashTime=.23f;dashCooldown=1.4f;invinc=Math.max(invinc,.22f);snd(6,.55f);shake=2;}
    void throwGrenade(){if(grenades<=0)return;grenades--;float sx=movingLeft?-1:1;Shot b=new Shot(x+sx*20,y-103,sx<0?3.1f:-.48f,490,3,38);bullets.add(b);snd(1,.35f);}
    void takeDamage(float n){if(invinc>0)return;health-=n;invinc=1.0f;shake=10;snd(3,.55f);
      for(int j=0;j<19;j++)spawn(x,y-64,rnd.nextInt(400)-200,rnd.nextInt(390)-195,.3f+rnd.nextFloat()*.5f,2,0xffff6b68,1);
      if(health<=0){health=0;mode=DEAD;snd(7,.8f);}}
    void killBoss(){bossAlive=false;score+=3000;snd(7,1);shake=20;for(int j=0;j<130;j++)spawn(LEVEL_LEN-450+rnd.nextInt(230)-115,GROUND-135+rnd.nextInt(140)-70,rnd.nextInt(600)-300,rnd.nextInt(600)-350,.4f+rnd.nextFloat()*1.4f,rnd.nextInt(14)+2,j%3==0?ACC[stage]:0xffffae5b,1);
      if(stage==2){mode=WIN;}else{nextStage=stage+1;transitionTimer=1.9f;}}
    void explosion(float px,float py,float radius,float dmg,boolean big){shake=Math.max(shake,big?14:5);snd(4,big?.67f:.35f);glow(px,py,0xffffad54,big?48:24);
      for(int i=0;i<(big?52:24);i++){float a=rnd.nextFloat()*6.28f,v=rnd.nextInt(290)+80;spawn(px,py,(float)Math.cos(a)*v,(float)Math.sin(a)*v, .3f+rnd.nextFloat()*.7f,2+rnd.nextInt(6),i%3==0?0xffffffff:0xffffb64e,1);}
      if(big)for(Enemy e:enemies){float d=(float)Math.hypot(e.x-px,e.y-50-py);if(d<radius){e.hp-=dmg;if(e.hp<=0){e.dead=true;score+=e.points;}}}
    }
    void impact(float px,float py,int col){for(int j=0;j<7;j++)spawn(px,py,rnd.nextInt(300)-150,rnd.nextInt(300)-150,.22f+rnd.nextFloat()*.4f,2+rnd.nextInt(4),col,1);}
    void spark(float px,float py,int col,int n){for(int j=0;j<n;j++)spawn(px,py,rnd.nextInt(280)-140,rnd.nextInt(200)-100,.22f,4,col,1);}
    void glow(float px,float py,int col,int n){for(int j=0;j<n;j++){float a=rnd.nextFloat()*6.28f,v=rnd.nextFloat()*170;spawn(px,py,(float)Math.cos(a)*v,(float)Math.sin(a)*v, .2f+rnd.nextFloat()*.65f,rnd.nextInt(5)+2,col,2);}}
    void spawn(float xx,float yy,float vxx,float vyy,float life,float size,int col,int type){if(particles.size()<490)particles.add(new Particle(xx,yy,vxx,vyy,life,size,col,type));}
    void fill(Canvas c,int color,float l,float t,float r,float b){p.setShader(null);p.setStyle(Paint.Style.FILL);p.setColor(color);c.drawRect(l,t,r,b,p);}
    void round(Canvas c,int color,float l,float t,float r,float b,float rad){p.setShader(null);p.setColor(color);p.setStyle(Paint.Style.FILL);c.drawRoundRect(l,t,r,b,rad,rad,p);}
    void line(Canvas c,int color,float x1,float y1,float x2,float y2,float w){p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(w);p.setStrokeCap(Paint.Cap.ROUND);p.setColor(color);p.setShader(null);c.drawLine(x1,y1,x2,y2,p);p.setStyle(Paint.Style.FILL);}
    void circle(Canvas c,int color,float x,float y,float rad){p.setColor(color);p.setShader(null);p.setStyle(Paint.Style.FILL);c.drawCircle(x,y,rad,p);}
    void txt(Canvas c,String s,float xx,float yy,float size,int color,boolean center){text.setTypeface(android.graphics.Typeface.create("sans-serif-condensed",android.graphics.Typeface.BOLD));text.setColor(color);text.setTextSize(size);text.setShadowLayer(size*.14f,0,2,0xff071018);text.setTextAlign(center?Paint.Align.CENTER:Paint.Align.LEFT);c.drawText(s,xx,yy,text);text.clearShadowLayer();}
    void bg(Canvas c,int layer,float parallax){Bitmap b=scenery[stage][layer];if(b==null)return;
      float off=(camera*parallax)%1536;float viewShift=off;
      p.setAlpha(255);p.setFilterBitmap(true);
      for(int i=-1;i<3;i++){float start=i*1536-viewShift;c.drawBitmap(b,null,new RectF(start,0,start+1536,720),p);}
    }
    void ground(Canvas c){
      float sx=(float)Math.floor(camera/80)*80;int stageDark=stage==0?0xff132f32:stage==1?0xff17213c:0xff292633;
      fill(c,stageDark,0,GROUND,1280,720);fill(c,stage==0?0xff4da084:stage==1?0xff488ba9:0xffab6752,0,GROUND-9,1280,GROUND+3);
      fill(c,0xaa060d1a,0,GROUND+3,1280,GROUND+13);
      for(float wx=sx-100;wx<camera+1370;wx+=80){float px=wx-camera;
        fill(c,stage==0?0xff143d36:stage==1?0xff1b304b:0xff38333e,px+2,GROUND+18,px+76,720);
        line(c,0x66171e20,px+3,GROUND+44,px+77,GROUND+44,2);
        line(c,stage==0?0xff24644e:stage==1?0xff397d9c:0xff8e655a,px+5,GROUND+21,px+72,GROUND+21,2);
        for(int row=0;row<3;row++){
          int intensity=(int)(Math.abs(Math.sin((wx+row*52)*.022))*33)+18;
          fill(c,(intensity<<24)| (stage==0?0x34ecae:stage==1?0x49cefc:0xe6ab63),px+8+row*9,GROUND+57+row*29,px+45+row*3,GROUND+59+row*29);
        }
        if(((int)wx/80)%5==0){fill(c,0xff091622,px+12,GROUND+18,px+26,GROUND+30);circle(c,ACC[stage],px+20,GROUND+24,3);}
        if(stage==0){for(int j=0;j<5;j++){float X=px+j*14+5;line(c,0xff247551,X,GROUND-6,X+5,GROUND-14-(j%3)*8,2);}}
      }
    }
    void platforms(Canvas c){for(Platform pl:platforms){float px=pl.x-camera;if(px+pl.w<-10||px>1290)continue;
      fill(c,0x90000508,px+9,pl.y+10,px+pl.w+8,pl.y+36);
      fill(c,stage==0?0xff35544b:stage==1?0xff223d56:0xff4d404c,px,pl.y,px+pl.w,pl.y+27);
      fill(c,stage==0?0xff82c38b:stage==1?0xff42d5fa:0xfff49a5b,px-2,pl.y-7,px+pl.w+2,pl.y+3);
      for(int xx=22;xx<pl.w-9;xx+=24){line(c,0xff0b1b29,px+xx,pl.y+5,px+xx-8,pl.y+27,3);circle(c,0xff9fa6a4,px+xx,pl.y+17,2);}
      }}
    void units(Canvas c){
      for(Item it:items){if(it.picked)continue;float xx=it.x-camera;if(xx<-100||xx>1360)continue;
        float yy=it.y+(float)Math.sin(it.phase)*8;int col=it.type==0?0xff62eab8:it.type==1?0xffe4a6ff:it.type==2?0xffffd16d:0xff59cbff;
        circle(c,(col&0xffffff)|0x33000000,xx,yy,28);round(c,0xff0b2634,xx-17,yy-17,xx+17,yy+17,6);line(c,col,xx-13,yy-13,xx+13,yy-13,3);line(c,col,xx+13,yy-13,xx+13,yy+13,3);line(c,col,xx+13,yy+13,xx-13,yy+13,3);line(c,col,xx-13,yy+13,xx-13,yy-13,3);
        txt(c,it.type==0?"+":it.type==1?"W":it.type==2?"G":"A",xx,yy+8,23,col,true);
      }
      for(Enemy e:enemies){if(e.dead)continue;float ex=e.x-camera;if(ex<-130||ex>1410)continue;
        if(e.type==1){ // flying attack drone
          circle(c,0x5526a9e8,ex,e.y+14,34);
          p.setShader(new LinearGradient(ex-45,e.y-20,ex+55,e.y+40,new int[]{0xff4b5871,0xff142238,0xff0a1122},null,Shader.TileMode.CLAMP));c.drawOval(ex-47,e.y-25,ex+48,e.y+20,p);p.setShader(null);
          fill(c,0xff111a30,ex-59,e.y-9,ex-28,e.y+7);fill(c,0xff172f40,ex+26,e.y-8,ex+62,e.y+4);
          circle(c,0xffff6e80,ex+4,e.y,13);circle(c,0xffffd6c6,ex+4,e.y,5);
          line(c,0xff78d7eb,ex-55,e.y+8,ex-38,e.y+8,3);
        }else if(e.type==2){ // fixed automated turret
          fill(c,0xff121b2e,ex-36,GROUND-60,ex+36,GROUND);
          round(c,0xff455b67,ex-29,GROUND-90,ex+30,GROUND-49,9);
          fill(c,0xffaa596e,ex-4,GROUND-85,ex+36,GROUND-75);
          circle(c,0xffff5d75,ex+3,GROUND-68,10);
          fill(c,0xff1e2735,ex-37,GROUND-18,ex+36,GROUND-3);
        }else {int pal=e.type==3?2:1;int fi=e.invuln>0?9:((int)(time*9+e.phase))%8;drawUnit(c,troops[pal],fi,ex,e.y,e.type==3?1.22f:.91f,x<e.x?-1:1,e.invuln>0);}
      }
      if(bossAlive&&x>LEVEL_LEN-1550){float bx=LEVEL_LEN-460-camera,by=GROUND-255;
        circle(c,0x332fbee8,bx,GROUND-140,192);
        Bitmap img=bossArt[stage];if(img!=null){p.setColor(Color.WHITE);p.setAlpha(255);RectF dest=new RectF(bx-220,by-50+(float)Math.sin(bossPhase*2)*9,bx+220,by+280+(float)Math.sin(bossPhase*2)*9);c.drawBitmap(img,null,dest,p);}
        for(int j=0;j<3;j++)circle(c,ACC[stage],bx+40+(float)Math.sin(bossPhase*(j+1)*3)*18,by+89,7+j*5);
      }
      if(invinc<=0||(int)(invinc*18)%2==0)drawUnit(c,troops[0],dashTime>0?8:shootCooldown>0&&firing?9:jumps>0?8:Math.abs(vx)<15?0:((int)(time*13))%8,x-camera,y,1f,vx< -5?-1:1,false);
    }
    void drawUnit(Canvas c,Bitmap sheet,int frame,float xx,float yy,float scale,int face,boolean hit){if(sheet==null)return;
      float wid=132*scale,hei=145*scale;float x1=xx-wid*.49f,y1=yy-hei;
      c.save();if(face==-1){c.scale(-1,1,xx,yy);}
      p.setColor(Color.WHITE);p.setAlpha(hit?160:255);
      c.drawBitmap(sheet,new Rect(frame*140,0,(frame+1)*140,156),new RectF(x1,y1,x1+wid,yy),p);
      c.restore();p.setAlpha(255);
    }
    void shots(Canvas c){
      for(Shot b:bullets){float xx=b.x-camera;if(xx<-50||xx>1340)continue;
        int col=b.type==1?0xffff6589:b.type==2?0xffffb44f:b.type==3?0xffffcb69:weapon==2?0xff8cfbff:0xfff6f7c0;
        float ang=(float)Math.atan2(b.vy,b.vx),len=b.type==1?19:weapon==2?49:32;
        line(c,(col&0xffffff)|0x55000000,xx-(float)Math.cos(ang)*len,b.y-(float)Math.sin(ang)*len,xx,b.y,16);
        line(c,col,xx-(float)Math.cos(ang)*len,b.y-(float)Math.sin(ang)*len,xx,b.y,b.type==3?6:4);
        circle(c,Color.WHITE,xx,b.y,b.type==3?7:3);
      }
      for(Particle a:particles){float xx=a.x-camera;if(xx<-30||xx>1330)continue;float alpha=clamp(a.life/a.max,0,1);int co=(a.color&0x00ffffff)|(((int)(alpha*220))<<24);
        if(a.type==3)line(c,co,xx,a.y,xx+3,a.y-17,2);else if(a.type==1)line(c,co,xx,a.y,xx-a.vx*.026f,a.y-a.vy*.025f,Math.max(1,a.size*.65f));else circle(c,co,xx,a.y,a.size*alpha);
      }
    }
    void hud(Canvas c){
      p.setShader(new LinearGradient(0,0,0,118,0xd9060e21,0x00050b18,Shader.TileMode.CLAMP));c.drawRect(0,0,1280,120,p);p.setShader(null);
      line(c,ACC[stage],27,27,49,27,4);line(c,ACC[stage],27,27,27,54,4);
      txt(c,"IRON / FRONT",67,43,30,0xffe3faff,false);
      txt(c,"OPERATION " +(stage+1)+" / 03     ·     "+AREA[stage],69,68,16,0xff8caabb,false);
      round(c,0xff142b39,70,84,352,103,4);round(c,health>35?0xff45e9b5:0xffff6a66,73,87,73+Math.max(0,health)*2.76f,100,2);
      txt(c,"ARMOR",362,100,17,0xffbcd3db,false);
      txt(c,String.format(java.util.Locale.US,"%07d",score),1118,39,27,0xffecf7fc,true);
      txt(c,"SCORE",1120,59,14,0xff80acbf,true);
      txt(c,"GRENADES  "+grenades+"     " +new String[]{"PULSE","SPREAD","RAIL"}[weapon],888,91,18,0xffdffbf6,false);
      if(bossAlive&&x>LEVEL_LEN-1550){round(c,0xaa081522,444,19,842,37,5);round(c,0xffff5c71,447,22,447+392*Math.max(0,bossHP/bossMax),34,3);
        txt(c,"WARDEN // " +(stage+1),640,58,17,0xfff8d8d9,true);}
      // pause icon
      round(c,0x9912293c,1208,16,1261,67,11);fill(c,0xffacd8dd,1225,27,1231,55);fill(c,0xffacd8dd,1239,27,1245,55);
      // simple transparent analog joystick and tactile buttons
      circle(c,0x3429a4b9,123,619,78);circle(c,0x662a5261,123,619,62);circle(c,0x7049bad2,123+joyX*37,619+joyY*37,31);
      control(c,1082,635,48,"JUMP",0xff75dfed);
      control(c,1199,621,64,"FIRE",0xffffc267);
      control(c,980,657,41,"DASH",0xff73c9f6);
      control(c,1132,508,40,"BOMB",0xfff89094);
      if((stageIntro>0||nextStage>=0)&&mode==PLAY){float fade=clamp(stageIntro/1.4f,0,1);
        fill(c,((int)(fade*155)<<24)|0x061623,0,170,1280,415);
        txt(c,nextStage<0?"MISSION 0"+(stage+1):"TARGET ELIMINATED",640,247,27,ACC[stage],true);
        txt(c,nextStage<0?AREA[stage]:"SECTOR SECURED",640,317,55,0xffe5f9f4,true);
        txt(c,"REACH THE STRONGHOLD   ·   DESTROY ITS COMMANDER",640,360,20,0xffb7cacc,true);
      }
    }
    void control(Canvas c,float xx,float yy,float rr,String label,int color){circle(c,0x66142234,xx,yy,rr);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2);p.setColor((color&0x00ffffff)|0x88000000);c.drawCircle(xx,yy,rr,p);p.setStyle(Paint.Style.FILL);txt(c,label,xx,yy+6,15,color,true);}
    void overlay(Canvas c){fill(c,0xbb020b18,0,0,1280,720);
      line(c,ACC[stage],430,202,850,202,3);
      if(mode==MENU){txt(c,"IRON FRONT",640,238,91,0xffeaf6fd,true);txt(c,"ASHES OF THE MACHINE",640,290,31,ACC[stage],true);
        txt(c,"THREE WAR ZONES. ONE LAST STAND.",640,338,20,0xffa7b8c6,true);
        round(c,ACC[stage],463,395,817,463,12);txt(c,"DEPLOY / PLAY",640,440,31,0xff062333,true);
        txt(c,"MOVE: LEFT PAD     ·     FIRE / JUMP / DASH / BOMB: RIGHT",640,505,20,0xffb8d6db,true);
        txt(c,"ORIGINAL OFFLINE ACTION GAME  ·  60 FPS TARGET",640,553,16,0xff7794a6,true);
      }else if(mode==PAUSE){txt(c,"MISSION PAUSED",640,281,67,0xffe7f6f9,true);
        txt(c,"TAP TO RESUME",640,395,26,ACC[stage],true);txt(c,"PRESS BACK TO CONTINUE",640,457,18,0xffa5c0ce,true);
      }else if(mode==DEAD){txt(c,"OPERATIVE DOWN",640,273,68,0xffff8387,true);
        txt(c,"SCORE "+score+"   ·   MISSION "+(stage+1),640,349,26,0xffd5eaef,true);
        round(c,ACC[stage],447,387,833,467,12);txt(c,"RETRY MISSION",640,439,32,0xff071f31,true);
      }else if(mode==WIN){txt(c,"MISSION COMPLETE",640,265,67,0xff9af7cb,true);
        txt(c,"THE MACHINE IS SILENT",640,339,33,0xffe8f7ff,true);
        txt(c,"FINAL SCORE: "+score,640,404,27,ACC[stage],true);
        txt(c,"TAP TO PLAY AGAIN",640,497,25,0xffbedfe3,true);
      }
    }
    void render(Canvas target){if(!ready)return;
      float sx=target.getWidth()/GW,sy=target.getHeight()/GH;pixelW=target.getWidth();pixelH=target.getHeight();
      target.drawColor(0xff050c18);target.save();target.scale(sx,sy);
      if(shake>0 && mode==PLAY)target.translate((rnd.nextFloat()-.5f)*shake,(rnd.nextFloat()-.5f)*shake);
      for(int i=0;i<4;i++)bg(target,i,new float[]{0,.10f,.27f,.49f}[i]);
      ground(target);platforms(target);units(target);shots(target);bg(target,4,.77f);
      // haze, weather, atmospheric frame
      if(stage==1){for(int i=0;i<50;i++){float dx=(i*61+(time*98)%1200)%1280,dy=(i*73+time*650)%720;line(target,0x527cd7ee,dx,dy,dx-14,dy+25,1);}}
      if(stage==2){for(int i=0;i<18;i++){float dx=(i*157+time*37)%1280,dy=(i*73+(float)Math.sin(time+i)*75+720)%720;circle(target,0x669f5b4c,dx,dy,(i%4)+1);}}
      hud(target);
      if(mode!=PLAY)overlay(target);
      target.restore();
    }
    int hitButton(float px,float py){if(px>1200&&py<110)return 7;
      if(Math.hypot(px-1199,py-621)<90)return 2;
      if(Math.hypot(px-1082,py-635)<73)return 3;
      if(Math.hypot(px-980,py-657)<65)return 4;
      if(Math.hypot(px-1132,py-508)<64)return 5;
      if(px<460 && py>420)return 1;
      if(px>GW*.55f)return 2;
      return 1;
    }
    @Override public boolean onTouchEvent(MotionEvent ev){
      int action=ev.getActionMasked(),index=ev.getActionIndex();
      if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN){
        int pid=ev.getPointerId(index);float xx=ev.getX(index)*GW/Math.max(1,getWidth()),yy=ev.getY(index)*GH/Math.max(1,getHeight());
        if(mode==MENU){mode=PLAY;stageIntro=2.5f;return true;}
        if(mode==DEAD){setup(stage,true);return true;}
        if(mode==WIN){setup(0,false);return true;}
        if(mode==PAUSE){mode=PLAY;return true;}
        int which=hitButton(xx,yy);
        if(which==7){mode=PAUSE;return true;}
        if(which==1){joystickId=pid;joyX=clamp((xx-123)/73,-1,1);joyY=clamp((yy-619)/73,-1,1);movingRight=joyX>.22;movingLeft=joyX<-.22;}
        else if(which==2){fireId=pid;firing=true;}
        else if(which==3){jumpId=pid;jump();}
        else if(which==4){dashId=pid;dash();}
        else if(which==5){grenadeId=pid;throwGrenade();}
        return true;
      }
      if(action==MotionEvent.ACTION_MOVE){
        for(int i=0;i<ev.getPointerCount();i++){int pid=ev.getPointerId(i);float xx=ev.getX(i)*GW/Math.max(1,getWidth()),yy=ev.getY(i)*GH/Math.max(1,getHeight());
          if(joystickId==pid){joyX=clamp((xx-123)/73,-1,1);joyY=clamp((yy-619)/73,-1,1);movingRight=joyX>.22;movingLeft=joyX<-.22;}
          if(fireId==pid){aim=clamp((yy-621)/310,-.75f,.75f);}
        }return true;
      }
      if(action==MotionEvent.ACTION_CANCEL||action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_POINTER_UP){
        int pid=ev.getPointerId(index);
        if(pid==joystickId){joystickId=-1;joyX=joyY=0;movingLeft=movingRight=false;}
        if(pid==fireId){fireId=-1;firing=false;aim=0;}
        if(pid==jumpId)jumpId=-1;if(pid==dashId)dashId=-1;if(pid==grenadeId)grenadeId=-1;
        return true;
      }
      return true;
    }
  }
}