from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.persistence.aof import AofPersistence
from src.persistence.rdb import RdbPersistence
from src.storage.engine import StorageEngine


@dataclass(frozen=True, slots=True)
class PersistenceConfig:
    data_dir: Path
    rdb_filename: str = "dump.rdb"
    aof_filename: str = "appendonly.aof"

    @property
    def rdb_path(self) -> Path:
        return self.data_dir / self.rdb_filename

    @property
    def aof_path(self) -> Path:
        return self.data_dir / self.aof_filename


class PersistenceManager:
    def __init__(self, storage: StorageEngine, config: PersistenceConfig) -> None:
        self._storage = storage
        self._config = config
        self._rdb = RdbPersistence(config.rdb_path)
        self._aof = AofPersistence(config.aof_path)

    def restore(self) -> None:
        if self._config.aof_path.exists():
            state = self._aof.replay()
            self._storage.load_snapshot(state.data, state.expires_at)
            return

        snapshot = self._rdb.load()
        self._storage.load_snapshot(snapshot.data, snapshot.expires_at)

    def snapshot(self) -> Path:
        data, expires_at = self._storage.snapshot()
        path = self._rdb.save(data, expires_at)
        self._aof.reset()
        return path

    def record_write(self, command: str, *args: str) -> None:
        normalized = command.upper()
        if normalized == "SET":
            self._aof.append("SET", *args)
            return

        if normalized == "DEL":
            self._aof.append("DEL", *args)
            return

        if normalized == "EXPIRE":
            key = args[0]
            expires_at = self._storage.get_expire_at(key)
            if expires_at is None:
                return
            self._aof.append("EXPIRE", key, str(expires_at))
            return

        raise ValueError(f"unsupported persistence command: {command}")

    def snapshot_on_shutdown(self) -> Path:
        return self.snapshot()
