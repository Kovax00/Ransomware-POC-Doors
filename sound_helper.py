import ctypes
import uuid
from pathlib import Path

_winmm = ctypes.WinDLL("winmm")
_mci = _winmm.mciSendStringW
_mci.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
_mci.restype = ctypes.c_uint


def _mci_cmd(command: str) -> str:
    buf = ctypes.create_unicode_buffer(256)
    _mci(command, buf, 255, None)
    return buf.value


class WaveOut:

    _instances = []

    def __init__(self, path):
        self.path = str(path)
        self.alias = f"snd_{uuid.uuid4().hex}"
        self._opened = False
        WaveOut._instances.append(self)

    def _ensure_open(self) -> bool:
        if self._opened:
            return True
        for mci_type in ("mpegvideo", "waveaudio"):
            if _mci(f'open "{self.path}" type {mci_type} alias {self.alias}', None, 0, None) == 0:
                self._opened = True
                return True
        return False

    def play(self, loop: bool = False):
        if not self._ensure_open():
            return
        if loop and _mci(f"play {self.alias} from 0 repeat", None, 0, None) == 0:
            return
        _mci(f"play {self.alias} from 0", None, 0, None)

    def stop(self):
        if self._opened:
            _mci(f"stop {self.alias}", None, 0, None)
            _mci(f"close {self.alias}", None, 0, None)
            self._opened = False

    @property
    def volume(self) -> float:
        return 1.0

    @volume.setter
    def volume(self, value: float):
        if self._ensure_open():
            value = max(0.0, min(1.0, float(value)))
            _mci(f"setaudio {self.alias} volume to {int(value * 1000)}", None, 0, None)

    def close(self):
        if self._opened:
            _mci(f"close {self.alias}", None, 0, None)
            self._opened = False

    @classmethod
    def close_all(cls):
        _mci("close all", None, 0, None)


class SoundHelper:

    @staticmethod
    def create(sound) -> WaveOut:
        if isinstance(sound, Path):
            sound = str(sound)
        return WaveOut(sound)
