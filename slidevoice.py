"""Слайд вперед — offline Russian voice control for presentations."""
import ctypes
import os
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from voice_engine import GRAMMAR, decode_result
from ppt_controls import execute_powerpoint_command, route_command

NAME = "vosk-model-small-ru-0.22"
DARK = "#0d1527"
CARD = "#19263e"
WHITE = "#edf4ff"
MUTED = "#9caece"
CYAN = "#58dfff"
GREEN = "#78ecaf"

def locate_model():
    roots = [Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)),
             Path(__file__).resolve().parent]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "Слайд вперед")
    for root in roots:
        path = root / "models" / NAME
        if (path / "am").is_dir() and (path / "conf").is_dir():
            return path
    return None

def switch_slide(command):
    # Only explicit slide commands can inject a key. Animation never does.
    key = {"slide_next": 0x22, "slide_previous": 0x21}[command]
    api = ctypes.windll.user32
    api.keybd_event(key, 0, 0, 0)
    api.keybd_event(key, 0, 2, 0)

def focused_on_slidevoice():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == os.getpid()

class SlaidVpered(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Слайд вперед — голосовые слайды")
        self.geometry("800x690")
        self.minsize(660, 520)
        self.configure(bg=DARK)
        app_icon = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets" / "slide-vpered.ico"
        if app_icon.is_file():
            try:
                self.iconbitmap(str(app_icon))
            except tk.TclError:
                pass
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.thread = None
        self.listening = False
        self.last_trigger = 0.0
        self.mics = []
        self.mic_choice = tk.StringVar()
        self.status = tk.StringVar(value="Ожидание запуска")
        self.recent = tk.StringVar(value="Команда ещё не прозвучала")
        self.draw()
        self.find_microphones()
        self.after(100, self.update_events)

    def label(self, parent, caption, size=11, color=WHITE, bold=False):
        return tk.Label(parent, text=caption, font=("Segoe UI", size, "bold" if bold else "normal"),
                        bg=parent["bg"], fg=color, anchor="w")

    def draw(self):
        """Light Windows UI matching the Слайд вперед visual reference."""
        bg = "#f4f8fe"
        paper = "#ffffff"
        blue = "#073fae"
        ink = "#13223b"
        muted = "#536781"
        pale = "#e8f2ff"
        pale_deep = "#e2eefc"
        self.configure(bg=bg)
        self.geometry("800x690")
        self.minsize(660, 520)

        # Scrollable page stays usable at 1366x768 and with Windows text scaling.
        shell = tk.Frame(self, bg=bg)
        shell.pack(fill="both", expand=True, padx=9, pady=8)
        canvas = tk.Canvas(shell, bg=paper, bd=0, highlightthickness=1,
                           highlightbackground="#d5e3f2")
        bar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=paper)
        window_id = canvas.create_window(0, 0, window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            window_id, width=e.width))
        def scroll_page(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", scroll_page)

        def lbl(parent, text="", size=12, color=ink, weight="normal", **kw):
            return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                            font=("Segoe UI", size, weight), **kw)

        # Brand block: top developer byline and logo with oversized title.
        lbl(body, "Разработчик: Рамазанов Роман Валерьевич", 12,
            ink, "bold").pack(pady=(10, 3))
        hero = tk.Frame(body, bg=paper)
        hero.pack(fill="x", padx=20, pady=(0, 8))
        asset = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        logo = asset / "assets" / "slide-vpered-art.jpg"
        if logo.is_file():
            try:
                from PIL import Image, ImageTk
                art = Image.open(logo).convert("RGBA").resize((94, 94),
                                               Image.Resampling.LANCZOS)
                self._brand_image = ImageTk.PhotoImage(art)
                tk.Label(hero, image=self._brand_image, bg=paper).pack(
                    side="left", padx=(4, 15))
            except Exception:
                lbl(hero, "▣", 48, blue).pack(side="left", padx=(10, 22))
        else:
            lbl(hero, "▣", 48, blue).pack(side="left", padx=(10, 22))
        hero_words = tk.Frame(hero, bg=paper)
        hero_words.pack(side="left", fill="both", expand=True, pady=8)
        lbl(hero_words, "Слайд вперед", 31, "#082f88", "bold",
            anchor="w").pack(anchor="w")
        lbl(hero_words, "Голосовое управление презентациями", 12, muted,
            anchor="w").pack(anchor="w", pady=(3, 0))

        # Rounded-looking light-blue state banner.
        state = tk.Frame(body, bg=pale, highlightthickness=1,
                         highlightbackground="#d3e4f9", padx=14, pady=9)
        state.pack(fill="x", padx=17, pady=(0, 9))
        tk.Label(state, text="●", bg=pale, fg="#21b938",
                 font=("Segoe UI", 19, "bold")).pack(side="left", padx=(0, 9))
        state_labels = tk.Frame(state, bg=pale)
        state_labels.pack(side="left", fill="x", expand=True)
        self.state_head = tk.Label(state_labels, text="Готов к работе", bg=pale,
                    fg=ink, font=("Segoe UI", 15, "bold"))
        self.state_head.pack(anchor="w")
        self.state_sub = tk.Label(state_labels,
                    text="Нажмите «Запустить» для начала прослушивания",
                    bg=pale, fg=muted, font=("Segoe UI", 9))
        self.state_sub.pack(anchor="w", pady=(3, 0))
        self.button = tk.Button(state, text="▶  Запустить", command=self.toggle,
                         font=("Segoe UI", 11, "bold"), bg="#0b4cc7",
                         fg="white", activebackground="#0b63ef",
                         activeforeground="white", bd=0, relief="flat",
                         padx=15, pady=8, cursor="hand2")
        self.button.pack(side="right", padx=(8, 0))

        # Audio device row and a real settings button.
        device_row = tk.Frame(body, bg=paper)
        device_row.pack(fill="x", padx=17, pady=(0, 9))
        lbl(device_row, "🎙  Микрофон:", 11, ink, "bold").pack(
             side="left", padx=(2, 7), pady=5)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Voice.TCombobox", padding=6,
                        fieldbackground="#ffffff", foreground=ink,
                        bordercolor="#cbd8e9", lightcolor="#cbd8e9",
                        darkcolor="#cbd8e9", arrowcolor=ink)
        self.combo = ttk.Combobox(device_row, textvariable=self.mic_choice,
                           state="readonly", style="Voice.TCombobox",
                           font=("Segoe UI", 10))
        self.combo.pack(side="left", fill="x", expand=True, pady=5)
        def show_settings():
            messagebox.showinfo("Слайд вперед — настройки",
                "Голосовые команды:\n\n"
                "«Дальше» — следующий шаг анимации.\n"
                "«Назад» — предыдущий шаг анимации.\n"
                "«Следующий слайд» — переход вперед.\n"
                "«Предыдущий слайд» — переход назад.\n\n"
                "Для анимаций нужен настольный Microsoft PowerPoint.")
        tk.Button(device_row, text="⚙  Настройки", command=show_settings,
                  font=("Segoe UI", 10, "bold"), bg="#f4f8ff", fg=ink,
                  relief="solid", bd=1, highlightthickness=0,
                  padx=8, pady=6, cursor="hand2").pack(
                      side="right", padx=(7, 0), pady=5)

        # Four command cards, aligned as in the reference screenshot.
        section = tk.Frame(body, bg=pale_deep, highlightthickness=1,
                           highlightbackground="#d5e5f9", padx=10, pady=8)
        section.pack(fill="x", padx=17, pady=(0, 8))
        lbl(section, "Голосовые команды", 15, "#0744b7", "bold").pack(
            anchor="w", padx=6, pady=(0, 6))
        commands = [
            ("▶", "«Дальше»", "Показать следующую строку\nили анимацию на текущем слайде"),
            ("◀", "«Назад»", "Вернуться к предыдущему шагу\nанимации на текущем слайде"),
            ("⏭", "«Следующий слайд»", "Перейти на следующий слайд"),
            ("⏮", "«Предыдущий слайд»", "Перейти на предыдущий слайд")
        ]
        for glyph, voice, detail in commands:
            cell = tk.Frame(section, bg="#fbfdff", highlightthickness=1,
                            highlightbackground="#d9e6f5")
            cell.pack(fill="x", pady=3)
            cell.grid_columnconfigure(1, weight=2, uniform="text")
            cell.grid_columnconfigure(2, weight=2, uniform="text")
            tk.Label(cell, text=glyph, fg="#0a61ef", bg="#fbfdff",
                     font=("Segoe UI Symbol", 19, "bold"), width=2).grid(
                         row=0, column=0, padx=(8, 5), pady=7, sticky="w")
            lbl(cell, voice, 11, ink, "bold", anchor="w").grid(
                row=0, column=1, sticky="w", padx=(0, 6), pady=7)
            lbl(cell, detail, 9, "#40536f", "normal", anchor="w",
                justify="left").grid(row=0, column=2, sticky="w",
                                     padx=(2, 7), pady=7)

        # Blue help strip with live feedback.
        tip = tk.Frame(body, bg="#deedff", highlightthickness=1,
                       highlightbackground="#d0e4fc", padx=12, pady=8)
        tip.pack(fill="x", padx=17, pady=(0, 10))
        tk.Label(tip, text="●", bg="#deedff", fg="#0865e5",
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=(0, 8))
        tip_body = tk.Frame(tip, bg="#deedff")
        tip_body.pack(side="left", fill="x", expand=True)
        lbl(tip_body, "Команды «Дальше» и «Назад» управляют анимациями и не "
            "переключают слайд, если анимаций нет.", 10, "#063d9b",
            "normal", wraplength=600, justify="left").pack(anchor="w")
        tk.Label(tip_body, textvariable=self.recent, bg="#deedff",
                 fg="#3e597a", font=("Segoe UI", 9)).pack(
                     anchor="w", pady=(5, 0))

    def find_microphones(self):
        self.mics = [("По умолчанию (Windows)", None)]
        try:
            import sounddevice as sd
            self.mics.extend((f"{n}: {d['name']}", n)
                for n, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0)
        except Exception as exc:
            self.status.set("Не удалось получить список микрофонов")
            self.recent.set(str(exc))
        self.combo["values"] = [name for name, _ in self.mics]
        self.mic_choice.set(self.mics[0][0])

    def toggle(self):
        if self.listening:
            self.stop.set()
            self.button.config(state="disabled", text="Остановка…")
            self.state_head.configure(text="Останавливаю…")
            self.state_sub.configure(text="Завершаю прослушивание")
            return
        if self.thread and self.thread.is_alive():
            return
        path = locate_model()
        if not path:
            messagebox.showerror("Слайд вперед", "Не найдена русская речевая модель.\n"
                "В готовом EXE она встроена. Для запуска из исходников "
                "откройте УСТАНОВИТЬ_И_ЗАПУСТИТЬ.bat.")
            return
        mic = next((n for name, n in self.mics if name == self.mic_choice.get()), None)
        self.stop.clear()
        self.listening = True
        self.combo.config(state="disabled")
        self.button.config(text="■  Остановить", bg="#0b4cc7")
        self.status.set("Загружаю распознавание…")
        self.state_head.configure(text="Подключаю микрофон…")
        self.state_sub.configure(text="Загружаю русскую модель распознавания")
        self.thread = threading.Thread(target=self.listen,
            args=(str(path), mic), daemon=True)
        self.thread.start()

    def listen(self, path, mic):
        recorded = queue.Queue(maxsize=32)
        try:
            import sounddevice as sd
            from vosk import Model, KaldiRecognizer, SetLogLevel
            SetLogLevel(-1)
            model = Model(path)
            frequency = int(sd.query_devices(mic, "input")["default_samplerate"])
            recognizer = KaldiRecognizer(model, frequency, GRAMMAR)

            def callback(audio, frames, timestamp, errors):
                if not self.stop.is_set():
                    try:
                        recorded.put_nowait(bytes(audio))
                    except queue.Full:
                        pass

            with sd.RawInputStream(samplerate=frequency, blocksize=4000,
                                   device=mic, dtype="int16", channels=1,
                                   callback=callback):
                self.events.put(("ready", None))
                while not self.stop.is_set():
                    try:
                        data = recorded.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    if recognizer.AcceptWaveform(data):
                        action = decode_result(recognizer.Result())
                        now = time.monotonic()
                        if action and now - self.last_trigger >= 1.0:
                            self.last_trigger = now
                            self.events.put(("action", action))
        except Exception as exc:
            self.events.put(("error", str(exc)))
        finally:
            self.events.put(("stopped", None))

    def update_events(self):
        try:
            while True:
                name, value = self.events.get_nowait()
                if name == "ready":
                    self.status.set("Слушаю четыре голосовые команды")
                    self.state_head.configure(text="Готов к работе")
                    self.state_sub.configure(text="Слушаю голосовые команды…")
                elif name == "action":
                    names = {
                        "animation_next": "Дальше",
                        "animation_previous": "Назад",
                        "slide_next": "Следующий слайд",
                        "slide_previous": "Предыдущий слайд",
                    }
                    word = names[value]
                    if focused_on_slidevoice():
                        self.recent.set(word + " — откройте презентацию")
                    else:
                        # Safe routing: never send Right/Left for animations.
                        outcome = route_command(
                            value, execute_powerpoint_command, switch_slide)
                        self.recent.set(word + " — " + outcome)
                elif name == "error":
                    self.status.set("Ошибка распознавания")
                    self.state_head.configure(text="Ошибка микрофона")
                    self.state_sub.configure(text="Проверьте выбранное устройство")
                    messagebox.showerror("Ошибка Слайд вперед", str(value))
                elif name == "stopped":
                    self.listening = False
                    self.combo.config(state="readonly")
                    self.button.config(state="normal", text="▶  Запустить", bg="#0b4cc7")
                    self.state_head.configure(text="Готов к работе")
                    self.state_sub.configure(text="Нажмите «Запустить» для начала прослушивания")
                    if self.status.get() != "Ошибка распознавания":
                        self.status.set("Остановлено")
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self.update_events)

    def close(self):
        self.stop.set()
        self.destroy()

if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("Поддерживается Windows 10/11")
    SlaidVpered().mainloop()
