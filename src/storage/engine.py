from __future__ import annotations

from src.storage.in_memory import InMemoryStore


class StorageEngine:
    """
    Stable storage interface for dispatcher/server layer.
    This wrapper lets us swap backend implementation later.
    """

    def __init__(self, backend: InMemoryStore | None = None) -> None:
        self._backend = backend or InMemoryStore()

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._backend.set(key, value, ex=ex)

    def get(self, key: str) -> str | None:
        return self._backend.get(key)

    def delete(self, key: str) -> int:
        return self._backend.delete(key)

    def exists(self, key: str) -> int:
        return self._backend.exists(key)

    def expire(self, key: str, seconds: int) -> int:
        return self._backend.expire(key, seconds)

    def ttl(self, key: str) -> int:
        return self._backend.ttl(key)

    def invalidate(self, key: str) -> int:
        return self._backend.invalidate(key)
