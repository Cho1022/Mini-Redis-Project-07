from pathlib import Path

from src.persistence.aof import AofEntry, AofPersistence
from src.persistence.rdb import RdbPersistence


def test_rdb_save_and_load_snapshot(tmp_path: Path) -> None:
    persistence = RdbPersistence(tmp_path / "dump.rdb.json")

    persistence.save(
        {"user:1": "kim", "user:2": "lee"},
        {"user:2": 12345.0},
    )

    snapshot = persistence.load()

    assert snapshot.data == {"user:1": "kim", "user:2": "lee"}
    assert snapshot.expires_at == {"user:2": 12345.0}


def test_aof_append_and_replay_state(tmp_path: Path) -> None:
    persistence = AofPersistence(tmp_path / "appendonly.aof")

    persistence.append_entries(
        [
            AofEntry(command="SET", args=("session:1", "active")),
            AofEntry(command="EXPIRE", args=("session:1", "1700000000")),
            AofEntry(command="SET", args=("user:1", "kim")),
            AofEntry(command="DEL", args=("session:1",)),
        ]
    )

    state = persistence.replay()

    assert state.data == {"user:1": "kim"}
    assert state.expires_at == {}
