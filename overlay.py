import ctypes
import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from global_state import Global
from ransomed_window import Ransomed
from resources import load_taunt_images, resource
from sound_helper import SoundHelper

_user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010

SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79

TRANSPARENT_COLOR = "#0000c0"

try:
    from tkinterdnd2 import TkinterDnD
    _BASE = TkinterDnD.Tk
except Exception:
    _BASE = tk.Tk


class Overlay(_BASE):
    def __init__(self):
        super().__init__()
        self._closing = False
        self._ransomed_form = None
        self._layers = ()
        self._tray_icon = None
        self._fx_run = 0
        self._fx_labels = []

        self.withdraw()

        load_taunt_images()
        self.title("RANS0M")
        self.overrideredirect(True)
        x = _user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        y = _user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        w = _user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        h = _user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        self.geometry(f"{w}x{h}+{x}+{y}")
        Global.screen_bounds = (w, h)
        self.configure(bg=TRANSPARENT_COLOR)
        self.attributes("-transparentcolor", TRANSPARENT_COLOR)

        self._img_ransom_idle = self._photo(resource("ransom_idle.png"), (192, 191))
        self._img_ransom_idle_big = self._photo(resource("ransom_idle.png"), (900, 900))
        self._img_ransom_attack = self._photo(resource("ransom_attack.png"), (900, 900))
        self._img_stopsign = self._photo(resource("stop_sign.png"), (200, 200))
        self._img_stopsign_192 = self._photo(resource("stop_sign.png"), (192, 192))
        self._img_ransom_random_src = Image.open(resource("ransom_random.png"))

        self._pc_ransom = tk.Label(self, image=self._img_ransom_idle, bg=TRANSPARENT_COLOR)
        self._pc_stopsign = tk.Label(self, image=self._img_stopsign, bg=TRANSPARENT_COLOR)
        self._pc_attack = tk.Label(self, image=self._img_ransom_attack, bg=TRANSPARENT_COLOR)

        self._txt_download = tk.Label(self, text="DOWNLOADING...", font=("Consolas", 36, "bold"),
                                      fg="white", bg=TRANSPARENT_COLOR)
        self._pb_download = ttk.Progressbar(self, orient="horizontal", length=473, maximum=100)

        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._on_load()


    def _photo(self, path, size):
        pil = Image.open(path).resize(size)
        return ImageTk.PhotoImage(pil, master=self)

    def _ui(self, fn):
        try:
            self.after(0, fn)
        except Exception:
            pass

    def _center(self, widget, y_offset=0):
        widget.place(relx=0.5, rely=0.5, anchor="center", x=0, y=y_offset)

    def _show_random(self, widget, size=192):
        x = Global.rng.randint(0, max(0, Global.screen_bounds[0] - size))
        y = Global.rng.randint(0, max(0, Global.screen_bounds[1] - size))
        widget.place(x=x, y=y)

    def _hide(self, widget):
        try:
            widget.place_forget()
        except Exception:
            pass

    def _set_bg(self, color):
        try:
            self.configure(bg=color)
        except Exception:
            pass

    def _set_opacity(self, value):
        try:
            self.attributes("-alpha", value)
        except Exception:
            pass


    def _ransom_warning(self):
        spawn_sound = SoundHelper.create(resource("spawn.wav"))
        spawn_sound.play()

        def show_ransom():
            self._show_random(self._pc_ransom)

        self._ui(show_ransom)

        time.sleep(0.5)

        def swap_faces():
            self._pc_ransom.place_forget()
            sw, sh = Global.screen_bounds
            self._pc_stopsign.place(x=0, y=0, width=sw, height=sh)
            self._pc_stopsign.lift()

        self._ui(swap_faces)

        time.sleep(0.5)

        def back_to_face():
            self._pc_stopsign.place_forget()
            self._pc_ransom.config(image=self._img_ransom_idle_big)
            self._center(self._pc_ransom)
            self._pc_ransom.lift()
            self._set_bg("DarkRed")

        self._ui(back_to_face)
        time.sleep(0.1)

        def calm_down():
            self._set_bg(TRANSPARENT_COLOR)
            self._pc_ransom.config(image=self._img_ransom_idle)
            self._pc_ransom.place_forget()

        self._ui(calm_down)

    def _download_jumpscare(self):
        run = self._fx_run
        attack_sound = SoundHelper.create(resource("attack.wav"))
        attack_sound.play()

        def show_attack():
            self._center(self._pc_attack)
            self._pc_attack.place_configure(x=0, y=0)
            self._pc_attack.lift()
            self._set_bg("DarkRed")

        self._ui(show_attack)

        def shake():
            for _ in range(25):
                if self._fx_run != run:
                    return
                time.sleep(0.02)
                if self._fx_run != run:
                    return
                self._ui(lambda: self._pc_attack.place_configure(
                    x=Global.rng.randint(-40, 40), y=Global.rng.randint(-40, 40)))

        threading.Thread(target=shake, daemon=True).start()

        time.sleep(0.8)

        def hide_faces():
            self._fx_run += 1
            self._pc_ransom.place_forget()
            self._pc_attack.place_forget()

        self._ui(hide_faces)

        install_sound = SoundHelper.create(resource("install.wav"))
        install_sound.play()

        def add_sign():
            label = tk.Label(self, image=self._img_stopsign_192, bg=TRANSPARENT_COLOR)
            label.place(x=Global.rng.randint(0, max(0, Global.screen_bounds[0] - 192)),
                        y=Global.rng.randint(0, max(0, Global.screen_bounds[1] - 192)))
            self._fx_labels.append(label)

        def signs_thread():
            for _ in range(70):
                if self._fx_run != run:
                    break
                time.sleep(0.01)
                if self._fx_run != run:
                    break
                self._ui(add_sign)

            def clear_signs():
                for item in self._fx_labels:
                    try:
                        item.destroy()
                    except Exception:
                        pass
                self._fx_labels.clear()

            self._ui(clear_signs)

        threading.Thread(target=signs_thread, daemon=True).start()

        def show_download():
            self._center(self._txt_download)
            self._center(self._pb_download, y_offset=50)
            self._txt_download.place_configure(x=0, y=0)
            self._pb_download.place_configure(x=0, y=50)
            self._txt_download.lift()
            self._pb_download.lift()
            self._txt_download.config(text="DOWNLOADING...", font=("Consolas", 36, "bold"))
            self._pb_download.config(value=100)

        self._ui(show_download)

        def glitch_bar():
            for _ in range(40):
                if self._fx_run != run:
                    return
                time.sleep(0.04)
                if self._fx_run != run:
                    return
                def jitter():
                    size = max(20, 36 + Global.rng.randint(-2, 2))
                    self._txt_download.config(font=("Consolas", size, "bold"))
                    self._txt_download.place_configure(x=Global.rng.randint(-5, 5),
                                                       y=Global.rng.randint(-5, 5))
                    self._pb_download.place_configure(x=Global.rng.randint(-5, 5),
                                                      y=50 + Global.rng.randint(-5, 5))
                self._ui(jitter)

        threading.Thread(target=glitch_bar, daemon=True).start()

        time.sleep(1.2)

        def hide_download():
            self._fx_run += 1
            self._pc_ransom.place_forget()
            self._pc_attack.place_forget()
            self._txt_download.place_forget()
            self._pb_download.place_forget()
            self._pb_download.config(value=0)

        self._ui(hide_download)

    def _ransomed(self):
        def flash():
            try:
                self._ui(lambda: self._set_bg("Red"))
                for i in range(50):
                    time.sleep(0.001)
                    self._ui(lambda v=1 - (i * 2 / 100.0): self._set_opacity(v))
                self._ui(lambda: (self._set_opacity(1.0), self._set_bg(TRANSPARENT_COLOR)))
            except Exception:
                pass

        threading.Thread(target=flash, daemon=True).start()

        def start_ui():
            threading.Thread(target=self._faces_loop, daemon=True).start()
            self._ransomed_form = Ransomed(self)

        Global.ransom_left = 500
        Global.under_ransom = True

        layer1 = SoundHelper.create(resource("layer1.wav"))
        layer2 = SoundHelper.create(resource("layer2.wav"))
        layer3 = SoundHelper.create(resource("layer3.wav"))
        self._layers = (layer1, layer2, layer3)

        def on_paid():
            for layer in self._layers:
                layer.stop()
            SoundHelper.close_all()
            self._ui(self.reset_ransom)

        Global.ransom_paid_cb = on_paid

        self._ui(start_ui)

        deadline = time.time() + Global.RANSOM_DURATION

        def wait(seconds):
            end = time.time() + seconds
            while (Global.under_ransom and not self._closing
                   and time.time() < deadline and time.time() < end):
                time.sleep(1)

        layer1.play(loop=True)
        wait(26)
        if not Global.under_ransom or self._closing:
            return False
        if time.time() >= deadline:
            return True

        layer2.play(loop=True)
        wait(26)
        if not Global.under_ransom or self._closing:
            return False
        if time.time() >= deadline:
            return True

        layer3.play(loop=True)
        while Global.under_ransom and not self._closing and time.time() < deadline:
            time.sleep(1)

        if not Global.under_ransom or self._closing:
            return False
        return True

        self._ui(self._close_ransomed_form)
        return True

    def _faces_loop(self):
        while Global.under_ransom and not self._closing:
            time.sleep(Global.rng.uniform(0, 5))
            if not Global.under_ransom or self._closing:
                break

            def flash_faces():
                for _ in range(Global.rng.randint(1, 5)):
                    try:
                        size = Global.rng.randint(50, 400)
                        photo = ImageTk.PhotoImage(
                            self._img_ransom_random_src.resize((size, size)), master=self)
                        face = tk.Label(self, image=photo, bg=TRANSPARENT_COLOR)
                        face.image = photo
                        face.place(x=Global.rng.randint(0, max(0, Global.screen_bounds[0] - size)),
                                   y=Global.rng.randint(0, max(0, Global.screen_bounds[1] - size)))
                        self._fx_labels.append(face)
                        self.after(25, lambda f=face: self._destroy_label(f))
                    except Exception:
                        break

            self._ui(flash_faces)

    def _destroy_label(self, widget):
        try:
            widget.destroy()
        except Exception:
            pass
        try:
            self._fx_labels.remove(widget)
        except ValueError:
            pass

    def _close_ransomed_form(self):
        form = self._ransomed_form
        self._ransomed_form = None
        try:
            if form is not None and form.winfo_exists():
                form.destroy()
        except Exception:
            pass

    def _crash_jumpscare(self):
        attack_sound = SoundHelper.create(resource("attack.wav"))
        attack_sound.play()
        run = self._fx_run

        def show_attack():
            self._center(self._pc_attack)
            self._pc_attack.place_configure(x=0, y=0)
            self._pc_attack.lift()
            self._set_bg("DarkRed")

        self._ui(show_attack)

        def shake():
            for _ in range(25):
                if self._fx_run != run:
                    return
                time.sleep(0.01)
                if self._fx_run != run:
                    return
                self._ui(lambda: self._pc_attack.place_configure(
                    x=Global.rng.randint(-40, 40), y=Global.rng.randint(-40, 40)))

        threading.Thread(target=shake, daemon=True).start()

        time.sleep(1.0)

        subprocess.run(["shutdown", "/s", "/t", "0"], check=False)


    def reset_ransom(self):
        self._fx_run += 1
        for layer in self._layers:
            layer.stop()
        self._layers = ()
        for leftover in list(self._fx_labels):
            self._destroy_label(leftover)
        self._fx_labels.clear()

        Global.can_attack = True
        Global.ransom_paid_cb = None
        Global.under_ransom = False
        Global.ransom_left = 0

        try:
            self._txt_download.config(font=("Consolas", 36, "bold"))
        except Exception:
            pass
        try:
            self._pc_ransom.config(image=self._img_ransom_idle)
        except Exception:
            pass
        for widget in (self._pc_ransom, self._pc_attack, self._txt_download,
                       self._pb_download, self._pc_stopsign):
            self._hide(widget)
        try:
            self._pb_download.config(value=0)
        except Exception:
            pass

        self._set_bg(TRANSPARENT_COLOR)
        self._ransomed_form = None

    def spawn_ransom(self):
        if not Global.can_attack:
            return
        Global.can_attack = False
        threading.Thread(target=self._ransom_flow, daemon=True).start()

    def _ransom_flow(self):
        self._ransom_warning()
        self._download_jumpscare()

        if self._ransomed():
            Global.under_ransom = False
            self._crash_jumpscare()
            self._ui(self._quit)

    def _on_load(self):
        self.update_idletasks()
        self._apply_clickthrough()

        self.deiconify()
        self.reset_ransom()
        self._setup_tray_icon()
        self._setup_topmost_timer()

        self._ui(self.spawn_ransom)

    def _root_hwnd(self):
        GA_ROOT = 2
        hwnd = int(self.winfo_id())
        return _user32.GetAncestor(hwnd, GA_ROOT) or hwnd

    def _apply_clickthrough(self):
        try:
            hwnd = self._root_hwnd()
            style = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            _user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                                   style | WS_EX_LAYERED | WS_EX_TRANSPARENT |
                                   WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        except Exception:
            pass

    def _setup_topmost_timer(self):
        def tick():
            if self._closing:
                return
            try:
                _user32.SetWindowPos(self._root_hwnd(), HWND_TOPMOST, 0, 0, 0, 0,
                                     SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            except Exception:
                pass
            self.after(500, tick)

        self.after(500, tick)

    def _setup_tray_icon(self):
        try:
            import pystray
            icon_image = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 "main_ico.ico"))
            menu = pystray.Menu(pystray.MenuItem("Close", self._tray_close))
            self._tray_icon = pystray.Icon("RANS0M", icon_image, "RANS0M", menu)
            threading.Thread(target=self._tray_icon.run, daemon=True).start()
        except Exception:
            self._tray_icon = None

    def _tray_close(self, icon=None, item=None):
        if not Global.can_attack:
            return
        self._ui(self._quit)

    def _on_window_close(self):
        if Global.under_ransom:
            return
        self._quit()

    def _quit(self):
        if self._closing:
            return
        self._closing = True
        Global.can_attack = True
        for layer in self._layers:
            layer.stop()
        try:
            if self._tray_icon is not None:
                self._tray_icon.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
