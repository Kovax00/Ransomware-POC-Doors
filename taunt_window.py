import tkinter as tk
from PIL import ImageTk

from global_state import Global
from resources import load_taunt_images
from winutil import hide_control_box


class TauntWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self._photo = None

        if not Global.taunt_images:
            load_taunt_images()

        self.title(Global.taunt_titles[Global.rng.randrange(len(Global.taunt_titles))])
        self.configure(bg="DarkRed")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        width = Global.rng.randint(200, 400)
        height = Global.rng.randint(200, 400)

        if Global.taunt_images:
            try:
                image = Global.rng.choice(Global.taunt_images).resize((width, height))
                self._photo = ImageTk.PhotoImage(image, master=self)
                tk.Label(self, image=self._photo, bg="DarkRed"
                         ).place(x=0, y=0, width=width, height=height)
            except Exception:
                self._photo = None

        x = Global.rng.randint(0, max(0, Global.screen_bounds[0] - width))
        y = Global.rng.randint(0, max(0, Global.screen_bounds[1] - height))
        self.geometry(f"{width}x{height}+{x}+{y}")

        hide_control_box(self)

        Global.glitch_idle(self)

        self.after(Global.rng.randint(4000, 10 * 1000), self._close_if_alive)

    def _close_if_alive(self):
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass
