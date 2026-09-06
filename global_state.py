import random
import time


class Global:
    RANSOM_DURATION = 24 * 60 * 60

    TARGET_PATH = r"C:\Users\tearx\Downloads\ransomware doors\ransomdoors-python\prueba"

    taunt_titles = [
        "RANS0M",
        "MOSNAR",
        "RANSOM",
        "M0NARS",
        "YOU ARE AN IDIOT",
        "Untitled",
        "Untitled (3)",
        "I FOUND YOU",
        "RANSOM.exe",
        "RAANNNSSSSOOOOOMMMMMM",
        "times up",
        "GIVE MONEY",
        "ERROR",
        "DHAUFGH",
        "_________",
    ]

    ransom_left = 0
    under_ransom = False
    ransom_paid_cb = None
    used_coins = []
    can_attack = True

    rng = random.Random()
    screen_bounds = (1920, 1080)


    @staticmethod
    def is_administrator():
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def glitch_idle(widget, divide_and_taunt=False, spawn_taunt=None):
        pos = {"x": widget.winfo_x(), "y": widget.winfo_y()}

        def tick():
            try:
                if not widget.winfo_exists():
                    return
            except Exception:
                return

            if not Global.under_ransom:
                try:
                    widget.destroy()
                except Exception:
                    pass
                return

            try:
                if divide_and_taunt and Global.rng.randint(1, 100) <= 2:
                    w = max(widget.winfo_width(), 1)
                    h = max(widget.winfo_height(), 1)
                    pos["x"] = Global.rng.randint(0, max(0, Global.screen_bounds[0] - w))
                    pos["y"] = Global.rng.randint(0, max(0, Global.screen_bounds[1] - h))
                    if spawn_taunt:
                        spawn_taunt()

                widget.geometry(f"+{pos['x'] + Global.rng.randint(-5, 5)}"
                                f"+{pos['y'] + Global.rng.randint(-5, 5)}")
            except Exception:
                return

            widget.after(200, tick)

        widget.after(200, tick)
