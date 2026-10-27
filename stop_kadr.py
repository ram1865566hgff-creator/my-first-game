"""Стоп кадр: offline Russian hands-free video play/pause controller for Windows."""
import ctypes, os, queue, sys, threading, time, tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from voice_engine_stop_kadr import GRAMMAR, decode_result
from video_controls_stop_kadr import MODES, PlaybackGuard, apply_command
from fast_voice_stop_kadr import FastVoiceDetector
from windows_video_stop_kadr import send_input_key, list_windows, activate_target

TITLE="Стоп кадр"
MODEL="vosk-model-small-ru-0.22"
NAVY="#102543"; BLUE="#064fca"; WHITE="#ffffff"
MUTED="#596c84"; PANEL="#e8f2ff"

def root_path():
    return Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent))

def get_model():
    dirs=[root_path()/"models"/MODEL,
          Path(__file__).resolve().parent/"models"/MODEL]
    if os.environ.get("LOCALAPPDATA"):
        dirs.append(Path(os.environ["LOCALAPPDATA"])/TITLE/"models"/MODEL)
    return next((d for d in dirs if (d/"am").is_dir() and (d/"conf").is_dir()),None)

def foreground():
    return ctypes.windll.user32.GetForegroundWindow()

def this_window(hwnd):
    pid=ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    return pid.value==os.getpid()

def send_key(vk):
    send_input_key(vk)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Стоп кадр — управляй видео голосом")
        self.geometry("720x665")
        self.minsize(590,500)
        self.configure(bg="#edf4fc")
        ico=root_path()/"assets"/"stop_kadr.ico"
        if ico.exists():
            try: self.iconbitmap(str(ico))
            except tk.TclError: pass
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.queue=queue.Queue()
        self.stop_event=threading.Event()
        self.worker=None
        self.running=False
        self.last_heard=0.
        self.guard=PlaybackGuard()
        self.mic_var=tk.StringVar()
        self.mode_var=tk.StringVar(value=MODES[0][0])
        self.target_var=tk.StringVar(value="Автоматически (активное окно)")
        self.target_hwnds={}
        self.status=tk.StringVar(value="Ожидание запуска")
        self.subtitle=tk.StringVar(value="Выберите микрофон и нажмите «Начать»")
        self.last=tk.StringVar(value="Команда пока не прозвучала")
        self.devices=[]
        self.layout()
        self.read_mics()
        self.refresh_targets()
        self.after(30,self.poll)

    def layout(self):
        host=tk.Frame(self,bg="#edf4fc")
        host.pack(fill="both",expand=True,padx=10,pady=9)
        cv=tk.Canvas(host,bg=WHITE,borderwidth=0,highlightthickness=1,
                     highlightbackground="#d4e1ef")
        scroll=ttk.Scrollbar(host,orient="vertical",command=cv.yview)
        scroll.pack(side="right",fill="y")
        cv.configure(yscrollcommand=scroll.set)
        cv.pack(side="left",fill="both",expand=True)
        page=tk.Frame(cv,bg=WHITE)
        win=cv.create_window(0,0,window=page,anchor="nw")
        page.bind("<Configure>",lambda e:cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",lambda e:cv.itemconfig(win,width=e.width))
        cv.bind("<MouseWheel>",lambda e:cv.yview_scroll(-int(e.delta/120),"units"))
        def label(where,text,size=11,fg=NAVY,bold=False,**kw):
            return tk.Label(where,text=text,fg=fg,bg=where["bg"],
                            font=("Segoe UI",size,"bold" if bold else "normal"),**kw)
        label(page,"Разработчик: Рамазанов Роман Валерьевич",12,bold=True).pack(pady=(13,6))
        head=tk.Frame(page,bg=WHITE)
        head.pack(fill="x",padx=22,pady=(0,12))
        img=root_path()/"assets"/"stop_kadr.png"
        if img.exists():
            from PIL import Image,ImageTk
            photo=Image.open(img).resize((105,105),Image.Resampling.LANCZOS)
            self.image=ImageTk.PhotoImage(photo)
            tk.Label(head,image=self.image,bg=WHITE).pack(side="left",padx=(0,19))
        else:
            label(head,"▶Ⅱ",30,BLUE,True).pack(side="left",padx=(0,20))
        words=tk.Frame(head,bg=WHITE)
        words.pack(side="left",fill="x",expand=True,pady=16)
        label(words,"Стоп кадр",34,BLUE,True).pack(anchor="w")
        label(words,"Управляй видео голосом",15,MUTED).pack(anchor="w",pady=(2,0))
        state=tk.Frame(page,bg=PANEL,highlightthickness=1,
                       highlightbackground="#d2e2f5",padx=13,pady=12)
        state.pack(fill="x",padx=19,pady=(0,12))
        label(state,"●",25,"#23bb50",True).pack(side="left",padx=(0,10))
        statusbox=tk.Frame(state,bg=PANEL)
        statusbox.pack(side="left",fill="x",expand=True)
        tk.Label(statusbox,textvariable=self.status,bg=PANEL,fg=NAVY,
                 font=("Segoe UI",16,"bold")).pack(anchor="w")
        tk.Label(statusbox,textvariable=self.subtitle,bg=PANEL,fg=MUTED,
                 font=("Segoe UI",10)).pack(anchor="w",pady=(3,0))
        self.button=tk.Button(state,text="▶  Начать",command=self.toggle,
                 bg=BLUE,fg=WHITE,activebackground="#1574e8",
                 activeforeground=WHITE,font=("Segoe UI",11,"bold"),
                 relief="flat",bd=0,cursor="hand2",padx=15,pady=9)
        self.button.pack(side="right",padx=(7,0))
        ttk.Style(self).theme_use("clam")
        ttk.Style(self).configure("Stop.TCombobox",padding=7,
                  fieldbackground="white",foreground=NAVY)
        microw=tk.Frame(page,bg=WHITE)
        microw.pack(fill="x",padx=19,pady=(0,10))
        label(microw,"🎙 Микрофон",11,bold=True).pack(side="left",padx=(0,10))
        self.mics=ttk.Combobox(microw,textvariable=self.mic_var,state="readonly",
                    style="Stop.TCombobox",font=("Segoe UI",10))
        self.mics.pack(side="left",fill="x",expand=True)
        moderow=tk.Frame(page,bg=WHITE)
        moderow.pack(fill="x",padx=19,pady=(0,13))
        label(moderow,"Управление",11,bold=True).pack(side="left",padx=(0,10))
        self.methods=ttk.Combobox(moderow,textvariable=self.mode_var,state="readonly",
            style="Stop.TCombobox",font=("Segoe UI",10),
            values=[name for name,value in MODES])
        self.methods.pack(side="left",fill="x",expand=True)
        # In some browsers a keyboard event is ignored unless the video window
        # itself is active. Select its window to bring it to foreground first.
        targetrow=tk.Frame(page,bg=WHITE)
        targetrow.pack(fill="x",padx=19,pady=(0,9))
        label(targetrow,"Окно видео",11,bold=True).pack(side="left",padx=(0,10))
        self.targets=ttk.Combobox(targetrow,textvariable=self.target_var,
             state="readonly",style="Stop.TCombobox",font=("Segoe UI",10))
        self.targets.pack(side="left",fill="x",expand=True)
        tk.Button(targetrow,text="↻ Обновить",command=self.refresh_targets,
             bg="#e4efff",fg=NAVY,font=("Segoe UI",10),
             relief="flat",padx=9,pady=6).pack(side="right",padx=(7,0))
        pane=tk.Frame(page,bg="#e3efff",highlightthickness=1,
                      highlightbackground="#d1e2f8",padx=13,pady=12)
        pane.pack(fill="x",padx=19,pady=(0,12))
        label(pane,"Голосовые команды",16,BLUE,True).pack(anchor="w",pady=(0,9))
        for icon,command,desc,color in [
            ("▶","«Плей»","Продолжить воспроизведение",BLUE),
            ("Ⅱ","«Стоп»","Поставить видео на паузу","#ed4354")
        ]:
            item=tk.Frame(pane,bg="#fbfdff",highlightthickness=1,
                         highlightbackground="#d6e4f6",padx=12,pady=11)
            item.pack(fill="x",pady=5)
            label(item,icon,25,color,True,width=3).pack(side="left",padx=(0,8))
            texts=tk.Frame(item,bg="#fbfdff")
            texts.pack(side="left",fill="x",expand=True)
            label(texts,command,16,bold=True).pack(anchor="w")
            label(texts,desc,11,MUTED).pack(anchor="w",pady=(3,0))
        info=tk.Frame(page,bg="#e4efff",padx=14,pady=13)
        info.pack(fill="x",padx=19,pady=(0,18))
        label(info,"ⓘ",21,BLUE,True).pack(side="left",padx=(0,12))
        tt=tk.Frame(info,bg="#e4efff")
        tt.pack(side="left",fill="x",expand=True)
        label(tt,"Для VK Видео выберите режим «ВК Видео», затем окно браузера "
              "в строке «Окно видео» и нажмите на самом видео один раз.",10,
              "#194276",wraplength=530,justify="left").pack(anchor="w")
        tk.Label(tt,textvariable=self.last,bg="#e4efff",fg=MUTED,
                 font=("Segoe UI",10),wraplength=530,
                 justify="left").pack(anchor="w",pady=(5,0))

    def refresh_targets(self):
        selected=self.target_var.get()
        self.target_hwnds={"Автоматически (активное окно)":None}
        for hwnd,title in list_windows():
            name=f"{title[:67]}  [{hwnd}]"
            self.target_hwnds[name]=hwnd
        self.targets["values"]=list(self.target_hwnds)
        self.target_var.set(selected if selected in self.target_hwnds
                            else "Автоматически (активное окно)")

    def read_mics(self):
        self.devices=[("По умолчанию (Windows)",None)]
        try:
            import sounddevice as sd
            self.devices.extend((f"{i}: {d['name']}",i)
                   for i,d in enumerate(sd.query_devices())
                   if d["max_input_channels"]>0)
        except Exception as ex:
            self.last.set("Не удалось получить микрофоны: "+str(ex))
        self.mics["values"]=[a for a,b in self.devices]
        self.mic_var.set(self.devices[0][0])

    def toggle(self):
        if self.running:
            self.stop_event.set()
            self.button.config(state="disabled",text="Остановка...")
            return
        if self.worker and self.worker.is_alive():
            return
        folder=get_model()
        if folder is None:
            messagebox.showerror("Стоп кадр","Речевая модель не найдена. "
                 "Готовый EXE включает русскую модель.")
            return
        device=next((n for name,n in self.devices
                     if name==self.mic_var.get()),None)
        self.guard.clear()
        self.last_heard=0.0
        self.stop_event.clear()
        self.running=True
        self.mics.config(state="disabled")
        self.methods.config(state="disabled")
        self.button.config(text="■ Остановить")
        self.status.set("Подключаю микрофон...")
        self.subtitle.set("Загрузка русской модели")
        self.worker=threading.Thread(target=self.listen,
                 args=(str(folder),device),daemon=True)
        self.worker.start()

    def listen(self,folder,device):
        q=queue.Queue(maxsize=32)
        try:
            import sounddevice as sd
            from vosk import Model,KaldiRecognizer,SetLogLevel
            SetLogLevel(-1)
            model=Model(folder)
            rate=int(sd.query_devices(device,"input")["default_samplerate"])
            recognizer=KaldiRecognizer(model,rate,GRAMMAR)
            detector=FastVoiceDetector(min_stable_seconds=0.10)
            def audio_callback(data,frames,ts,status):
                if not self.stop_event.is_set():
                    try: q.put_nowait(bytes(data))
                    except queue.Full: pass
            with sd.RawInputStream(samplerate=rate,blocksize=1600,device=device,
                    dtype="int16",channels=1,callback=audio_callback):
                self.queue.put(("ready",None))
                while not self.stop_event.is_set():
                    try: data=q.get(timeout=.2)
                    except queue.Empty: continue
                    finished=recognizer.AcceptWaveform(data)
                    now=time.monotonic()
                    if finished:
                        command=detector.accept_final(recognizer.Result())
                    else:
                        command=detector.accept_partial(recognizer.PartialResult(),now)
                    if command and now-self.last_heard>=0.20:
                        self.last_heard=now
                        self.queue.put(("command",command))
        except Exception as ex:
            self.queue.put(("error",str(ex)))
        finally:
            self.queue.put(("stopped",None))

    def poll(self):
        try:
            while True:
                event,value=self.queue.get_nowait()
                if event=="ready":
                    self.status.set("Готов к работе")
                    self.subtitle.set("Слушаю команды «Стоп» и «Плей»")
                elif event=="command":
                    try:
                        chosen=self.target_hwnds.get(self.target_var.get())
                        if chosen is not None:
                            ok,info=activate_target(chosen)
                            if not ok:
                                self.last.set("Окно видео: "+info)
                                continue
                            hwnd=chosen
                        else:
                            hwnd=foreground()
                        message=apply_command(value,self.mode_var.get(),hwnd,
                           this_window(hwnd),self.guard,send_key)
                        self.last.set(("Стоп" if value=="pause" else "Плей")+" — "+message)
                    except Exception as ex:
                        self.last.set("Ошибка: "+str(ex))
                elif event=="error":
                    self.status.set("Ошибка микрофона")
                    self.subtitle.set("Проверьте подключение устройства")
                    messagebox.showerror(TITLE,str(value))
                elif event=="stopped":
                    self.running=False
                    self.mics.config(state="readonly")
                    self.methods.config(state="readonly")
                    self.button.config(state="normal",text="▶  Начать")
                    if self.status.get()!="Ошибка микрофона":
                        self.status.set("Ожидание запуска")
                        self.subtitle.set("Выберите микрофон и нажмите «Начать»")
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(30,self.poll)

    def close(self):
        self.stop_event.set()
        self.destroy()

if __name__=="__main__":
    if sys.platform!="win32":
        raise SystemExit("Программа предназначена для Windows 10/11")
    App().mainloop()
