from __future__ import annotations

import time
from typing import Callable


class ExpirationManager:
    """Tracks per-key expiration timestamps and computes TTL on demand."""

    def __init__(self, now_fn: Callable[[], float] | None = None) -> None:
        self._expires_at: dict[str, float] = {}
        self._now_fn = now_fn or time.time

    def set_expire(self, key: str, ttl_seconds: int) -> bool:
        if ttl_seconds <= 0:
            return False
        self._expires_at[key] = self._now_fn() + ttl_seconds
        return True

    def persist(self, key: str) -> bool:
        return self._expires_at.pop(key, None) is not None

    def delete(self, key: str) -> None:
        self._expires_at.pop(key, None)

    def is_expired(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return False
        if expires_at > self._now_fn():
            return False
        self._expires_at.pop(key, None)
        return True

    def ttl(self, key: str, key_exists: bool) -> int:
        if not key_exists:
            return -2
        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return -1

        remaining = int(expires_at - self._now_fn())
        if remaining >= 0:
            return remaining

        self._expires_at.pop(key, None)
        return -2
