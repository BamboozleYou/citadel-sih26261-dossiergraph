"""Envelope encryption (prototype stand-in for HashiCorp Vault transit).

Every stored document gets its own random 256-bit data key. The document is
encrypted with AES-256-GCM under that key, and the data key is itself wrapped
with the master key. Only wrapped keys are stored next to the ciphertext.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import config


def _master_key() -> bytes:
    config.ensure_dirs()
    path = config.KEYS / "master.key"
    if not path.exists():
        path.write_bytes(secrets.token_bytes(32))
        os.chmod(path, 0o600)
    return path.read_bytes()


def _hmac_key() -> bytes:
    path = config.KEYS / "faculty_hmac.key"
    if not path.exists():
        config.ensure_dirs()
        path.write_bytes(secrets.token_bytes(32))
        os.chmod(path, 0o600)
    return path.read_bytes()


def encrypt_blob(data: bytes, aad: bytes = b"") -> bytes:
    """Return wrapped_key_nonce(12) | wrapped_key(48) | nonce(12) | ciphertext."""
    dek = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    ct = AESGCM(dek).encrypt(nonce, data, aad)
    wnonce = secrets.token_bytes(12)
    wrapped = AESGCM(_master_key()).encrypt(wnonce, dek, b"dek")
    return wnonce + wrapped + nonce + ct


def decrypt_blob(blob: bytes, aad: bytes = b"") -> bytes:
    wnonce, wrapped, nonce, ct = blob[:12], blob[12:60], blob[60:72], blob[72:]
    dek = AESGCM(_master_key()).decrypt(wnonce, wrapped, b"dek")
    return AESGCM(dek).decrypt(nonce, ct, aad)


def store(doc_id: str, data: bytes) -> Path:
    config.ensure_dirs()
    path = config.VAULT / f"{doc_id}.bin"
    path.write_bytes(encrypt_blob(data, doc_id.encode()))
    return path


def load(doc_id: str) -> bytes:
    return decrypt_blob((config.VAULT / f"{doc_id}.bin").read_bytes(), doc_id.encode())


def faculty_token(faculty_id: str) -> str:
    """Keyed hash of a faculty ID: lets institutions be compared without storing the ID."""
    norm = "".join(ch for ch in faculty_id.upper() if ch.isalnum())
    return hmac.new(_hmac_key(), norm.encode(), hashlib.sha256).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
