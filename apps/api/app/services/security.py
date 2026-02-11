from __future__ import annotations

import hashlib

import bcrypt


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    # bcrypt truncates at 72 bytes; prehash for longer inputs.
    if len(raw) > 72:
        raw = hashlib.sha256(raw).digest()
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raw = hashlib.sha256(raw).digest()
    return bcrypt.checkpw(raw, password_hash.encode("utf-8"))
