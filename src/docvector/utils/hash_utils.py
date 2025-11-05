"""Hashing utilities."""

import hashlib
from typing import Union


def compute_hash(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """
    Compute hash of data.

    Args:
        data: Data to hash (string or bytes)
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)

    Returns:
        Hex digest of hash
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(data)

    return hasher.hexdigest()


def compute_text_hash(text: str) -> str:
    """
    Compute SHA256 hash of text content.

    Useful for detecting duplicate documents.

    Args:
        text: Text content

    Returns:
        SHA256 hex digest
    """
    return compute_hash(text, algorithm="sha256")
