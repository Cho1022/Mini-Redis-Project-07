import time

from src.storage.engine import StorageEngine


def test_set_get_exists_delete_round_trip() -> None:
    store = StorageEngine()

    assert store.set("name", "mini-redis") is None
    assert store.exists("name") == 1
    assert store.get("name") == "mini-redis"

    assert store.delete("name") == 1
    assert store.delete("name") == 0
    assert store.exists("name") == 0
    assert store.get("name") is None


def test_set_clears_previous_ttl_like_redis() -> None:
    store = StorageEngine()

    assert store.set("k", "v", ex=1) is None
    assert store.ttl("k") >= 0

    # Plain SET should remove previous expiration.
    assert store.set("k", "v2") is None
    assert store.ttl("k") == -1
    assert store.get("k") == "v2"


def test_expire_and_lazy_expiration_behavior() -> None:
    store = StorageEngine()

    assert store.set("token", "abc") is None
    assert store.expire("token", 1) == 1
    assert store.ttl("token") >= 0

    time.sleep(1.1)
    # Expired key is removed lazily on access.
    assert store.get("token") is None
    assert store.exists("token") == 0
    assert store.ttl("token") == -2


def test_ttl_special_return_codes() -> None:
    store = StorageEngine()

    assert store.ttl("missing") == -2

    assert store.set("alive", "x") is None
    assert store.ttl("alive") == -1


def test_invalidate_aliases_delete() -> None:
    store = StorageEngine()

    assert store.set("session", "s1") is None
    assert store.invalidate("session") == 1
    assert store.invalidate("session") == 0


def test_expire_returns_zero_for_missing_or_invalid_ttl() -> None:
    store = StorageEngine()

    assert store.expire("missing", 1) == 0

    store.set("key", "value")
    assert store.expire("key", 0) == 0
