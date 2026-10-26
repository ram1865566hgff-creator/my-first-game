"""SlideVoice — offline Russian voice control for presentations."""
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
from ppt_controls import execute_powerpoint_command

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
        roots.append(Path(local) / "SlideVoice")
    for root in roots:
        path = root / "models" / NAME
        if (path / "am").is_dir() and (path / "conf").is_dir():
            return path
    return None

def switch_slide(command):
    key = {"animation_next": 0x27, "animation_previous": 0x25,
           "slide_next": 0x22, "slide_previous": 0x21}[command]
    api = ctypes.windll.user32
    api.keybd_event(key, 0, 0, 0)
    api.keybd_event(key, 0, 2, 0)

def focused_on_slidevoice():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == os.getpid()

class SlideVoice(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SlideVoice — голосовые слайды")
        self.geometry("630x755")
        self.minsize(570, 710)
        self.configure(bg=DARK)
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
        heading = tk.Frame(self, bg=DARK)
        heading.pack(fill="x", padx=26, pady=(25, 14))
        self.label(heading, "SlideVoice", 28, WHITE, True).pack(anchor="w")
        self.label(heading, "Переключение слайдов голосом · без интернета",
                   10, MUTED).pack(anchor="w", pady=(4, 0))
        row = tk.Frame(self, bg=DARK)
        row.pack(fill="x", padx=26, pady=(5, 16))
        row.grid_columnconfigure(0, weight=1, uniform="tile")
        row.grid_columnconfigure(1, weight=1, uniform="tile")
        for i, (arrow, caption, explanation, accent) in enumerate([
            ("→", "ДАЛЬШЕ", "Показать анимацию", CYAN),
            ("←", "НАЗАД", "Убрать анимацию", GREEN),
            ("⏭", "СЛЕДУЮЩИЙ СЛАЙД", "Минуя анимации", CYAN),
            ("⏮", "ПРЕДЫДУЩИЙ СЛАЙД", "Минуя анимации", GREEN),
        ]):
            tile = tk.Frame(row, bg=CARD, padx=16, pady=11)
            tile.grid(row=i // 2, column=i % 2, sticky="nsew",
                      padx=(0, 7) if i % 2 == 0 else (7, 0),
                      pady=(0, 10) if i < 2 else (0, 0))
            self.label(tile, arrow, 26, accent, True).pack(anchor="w")
            self.label(tile, caption, 12 if i > 1 else 16, WHITE, True).pack(anchor="w")
            self.label(tile, explanation, 9, MUTED).pack(anchor="w", pady=(6, 0))
        box = tk.Frame(self, bg=CARD)
        box.pack(fill="x", padx=26, pady=(0, 12))
        inside = tk.Frame(box, bg=CARD)
        inside.pack(fill="x", padx=19, pady=16)
        self.label(inside, "МИКРОФОН", 10, MUTED, True).pack(anchor="w", pady=(0, 9))
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Voice.TCombobox", padding=6, fieldbackground="white",
                        foreground="#172137")
        self.combo = ttk.Combobox(inside, textvariable=self.mic_choice,
                                 state="readonly", style="Voice.TCombobox")
        self.combo.pack(fill="x")
        self.label(inside, "Скажите команду отдельно, затем сделайте паузу.",
                   9, MUTED).pack(anchor="w", pady=(11, 0))
        state_box = tk.Frame(self, bg=CARD)
        state_box.pack(fill="x", padx=26, pady=(0, 12))
        self.label(state_box, "СОСТОЯНИЕ", 9, MUTED, True).pack(
            anchor="w", padx=19, pady=(14, 4))
        tk.Label(state_box, textvariable=self.status, bg=CARD, fg=GREEN,
                 font=("Segoe UI", 11)).pack(anchor="w", padx=19)
        self.label(state_box, "Последняя команда:", 9, MUTED).pack(
            anchor="w", padx=19, pady=(12, 0))
        tk.Label(state_box, textvariable=self.recent, bg=CARD, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=19, pady=(3, 14))
        self.button = tk.Button(self, text="▶  НАЧАТЬ СЛУШАТЬ", command=self.toggle,
                                font=("Segoe UI", 12, "bold"), bg=CYAN, fg="#031c2b",
                                activebackground="#b7f4ff", cursor="hand2",
                                relief="flat", bd=0, pady=12)
        self.button.pack(fill="x", padx=26, pady=(3, 10))
        self.label(self, "Для показа оставьте презентацию активным окном.",
                   9, MUTED).pack()
        self.label(self, "Разработчик: Рамазанов Роман Валерьевич",
                   10, MUTED).pack(pady=(7, 0))

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
            self.button.config(state="disabled", text="ОСТАНОВКА…")
            return
        if self.thread and self.thread.is_alive():
            return
        path = locate_model()
        if not path:
            messagebox.showerror("SlideVoice", "Не найдена русская речевая модель.\n"
                "В готовом EXE она встроена. Для запуска из исходников "
                "откройте УСТАНОВИТЬ_И_ЗАПУСТИТЬ.bat.")
            return
        mic = next((n for name, n in self.mics if name == self.mic_choice.get()), None)
        self.stop.clear()
        self.listening = True
        self.combo.config(state="disabled")
        self.button.config(text="■  ОСТАНОВИТЬ", bg="#ffbdad")
        self.status.set("Загружаю распознавание…")
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
                        outcome = execute_powerpoint_command(value, switch_slide)
                        if outcome is None:
                            switch_slide(value)
                            outcome = "клавиша отправлена"
                        self.recent.set(word + " — " + outcome)
                elif name == "error":
                    self.status.set("Ошибка распознавания")
                    messagebox.showerror("Ошибка SlideVoice", str(value))
                elif name == "stopped":
                    self.listening = False
                    self.combo.config(state="readonly")
                    self.button.config(state="normal", text="▶  НАЧАТЬ СЛУШАТЬ", bg=CYAN)
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
    SlideVoice().mainloop()
