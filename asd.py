from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class HashTable(Generic[K, V]):
    """A small hash table with a dict-like interface."""

    _MAX_LOAD_FACTOR = 0.75
    _MIN_CAPACITY = 8

    def __init__(self, initial: Iterable[tuple[K, V]] | None = None, capacity: int = 8) -> None:
        bucket_count = max(self._MIN_CAPACITY, capacity)
        self._buckets: list[list[tuple[K, V]]] = [[] for _ in range(bucket_count)]
        self._size = 0

        if initial is not None:
            for key, value in initial:
                self[key] = value

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: object) -> bool:
        try:
            self[key]  # type: ignore[index]
            return True
        except KeyError:
            return False

    def __iter__(self) -> Iterator[K]:
        for bucket in self._buckets:
            for key, _ in bucket:
                yield key

    def __getitem__(self, key: K) -> V:
        bucket = self._find_bucket(key)
        for existing_key, value in bucket:
            if existing_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        bucket = self._find_bucket(key)
        for index, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                bucket[index] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1

        if self.load_factor > self._MAX_LOAD_FACTOR:
            self._resize(len(self._buckets) * 2)

    def __delitem__(self, key: K) -> None:
        bucket = self._find_bucket(key)
        for index, (existing_key, _) in enumerate(bucket):
            if existing_key == key:
                bucket.pop(index)
                self._size -= 1
                return
        raise KeyError(key)

    def __repr__(self) -> str:
        pairs = ", ".join(f"{key!r}: {value!r}" for key, value in self.items())
        return f"HashTable({{{pairs}}})"

    @property
    def load_factor(self) -> float:
        return self._size / len(self._buckets)

    def get(self, key: K, default: V | None = None) -> V | None:
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key: K, default: V) -> V:
        if key not in self:
            self[key] = default
            return default
        return self[key]

    def pop(self, key: K, default: V | None = None) -> V | None:
        bucket = self._find_bucket(key)
        for index, (existing_key, value) in enumerate(bucket):
            if existing_key == key:
                bucket.pop(index)
                self._size -= 1
                return value

        if default is not None:
            return default
        raise KeyError(key)

    def clear(self) -> None:
        self._buckets = [[] for _ in range(self._MIN_CAPACITY)]
        self._size = 0

    def keys(self) -> Iterator[K]:
        return iter(self)

    def values(self) -> Iterator[V]:
        for bucket in self._buckets:
            for _, value in bucket:
                yield value

    def items(self) -> Iterator[tuple[K, V]]:
        for bucket in self._buckets:
            for key, value in bucket:
                yield key, value

    def update(self, other: Iterable[tuple[K, V]] | dict[K, V]) -> None:
        source = other.items() if isinstance(other, dict) else other
        for key, value in source:
            self[key] = value

    def _find_bucket(self, key: K) -> list[tuple[K, V]]:
        index = hash(key) % len(self._buckets)
        return self._buckets[index]

    def _resize(self, new_capacity: int) -> None:
        old_items = list(self.items())
        self._buckets = [[] for _ in range(max(self._MIN_CAPACITY, new_capacity))]
        self._size = 0
        for key, value in old_items:
            self[key] = value


if __name__ == "__main__":
    table = HashTable[str, int]()
    table["apple"] = 3
    table["banana"] = 7
    table["banana"] = 9

    print(table)
    print(table["apple"])
    print(table.get("orange", 0))
    print(list(table.items()))
