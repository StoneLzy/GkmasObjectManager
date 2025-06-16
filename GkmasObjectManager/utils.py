"""
utils.py
General-purpose utilities: hashing, decorators, etc.
"""

from typing import Callable

from cryptography.hazmat.primitives import hashes


def sha256sum(data: bytes) -> bytes:
    """Calculates SHA-256 hash of the given data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def md5sum(data: bytes) -> bytes:
    """Calculates MD5 hash of the given data."""
    digest = hashes.Hash(hashes.MD5())
    digest.update(data)
    return digest.finalize()


def nocache(func) -> Callable:
    """Decorator to temporarily disable caching for GkmasDummyMedia and children."""

    from .media import GkmasDummyMedia

    def wrapper(*args, **kwargs):
        original = GkmasDummyMedia.ENABLE_CACHE
        GkmasDummyMedia.ENABLE_CACHE = False
        try:
            return func(*args, **kwargs)
        finally:
            GkmasDummyMedia.ENABLE_CACHE = original

    return wrapper
