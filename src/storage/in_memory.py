from __future__ import annotations

from asd import HashTable

from src.storage.expiration import ExpirationManager


class InMemoryStore:
    """Hash table based key-value store with lazy expiration."""

    def __init__(self) -> None:
        self._data: HashTable[str, str] = HashTable()
        self._expiration = ExpirationManager()

    def _evict_if_expired(self, key: str) -> bool:
        if not self._expiration.is_expired(key):
            return False
        self._data.pop(key, None)
        return True

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._data[key] = value
        self._expiration.persist(key)
        if ex is not None:
            if ex <= 0:
                self._data.pop(key, None)
                self._expiration.delete(key)
                return
            self._expiration.set_expire(key, ex)

    def get(self, key: str) -> str | None:
        self._evict_if_expired(key)
        return self._data.get(key)

    def delete(self, key: str) -> int:
        self._evict_if_expired(key)
        if key not in self._data:
            self._expiration.delete(key)
            return 0
        del self._data[key]
        self._expiration.delete(key)
        return 1

    def exists(self, key: str) -> int:
        self._evict_if_expired(key)
        return 1 if key in self._data else 0

    def expire(self, key: str, seconds: int) -> int:
        self._evict_if_expired(key)
        if key not in self._data:
            return 0
        return 1 if self._expiration.set_expire(key, seconds) else 0

    def ttl(self, key: str) -> int:
        expired = self._evict_if_expired(key)
        if expired:
            return -2
        return self._expiration.ttl(key, key_exists=(key in self._data))

    def invalidate(self, key: str) -> int:
        return self.delete(key)

    def snapshot(self) -> tuple[dict[str, str], dict[str, float]]:
        for key in list(self._data.keys()):
            self._evict_if_expired(key)
        return dict(self._data.items()), self._expiration.snapshot()

    def load(self, data: dict[str, str], expires_at: dict[str, float]) -> None:
        self._data.clear()
        self._data.update((str(key), str(value)) for key, value in data.items())
        self._expiration.load(expires_at)
        for key in list(self._data.keys()):
            self._evict_if_expired(key)

    def get_expire_at(self, key: str) -> float | None:
        self._evict_if_expired(key)
        return self._expiration.get_expire_at(key)
