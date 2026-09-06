from pathlib import Path

RESOURCES_DIR = Path(__file__).resolve().parent / "resources"

_TAUNT_BG = (139, 0, 0)


def resource(name: str) -> Path:
    return RESOURCES_DIR / name


def load_taunt_images():
    from PIL import Image

    from global_state import Global

    names = [
        "glitch.jpg", "idiot.png", "ransom_idle.png", "ransom_random.png",
        "stop_sign.png", "static1.png", "taunt2.jpg", "taunt3.jpeg",
    ]
    imgs = []
    for name in names:
        try:
            img = Image.open(resource(name))
            img.load()
            if img.mode != "RGB":
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, _TAUNT_BG)
                bg.paste(img, mask=img.split()[-1])
                img = bg
            imgs.append(img)
        except Exception:
            pass
    Global.taunt_images = imgs
