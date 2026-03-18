from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.persistence.aof import AofPersistence
from src.persistence.rdb import RdbPersistence
from src.storage.engine import StorageEngine


LOGGER = logging.getLogger(__name__)


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
        snapshot = self._rdb.load()
        LOGGER.info(
            "Restored from RDB: path=%s keys=%d",
            self._config.rdb_path.resolve(),
            len(snapshot.data),
        )

        state = self._aof.replay(snapshot.data, snapshot.expires_at)
        self._storage.load_snapshot(state.data, state.expires_at)
        LOGGER.info(
            "Applied AOF replay: path=%s keys=%d",
            self._config.aof_path.resolve(),
            len(state.data),
        )

    def snapshot(self) -> Path:
        data, expires_at = self._storage.snapshot()
        path = self._rdb.save(data, expires_at)
        self._aof.reset()
        LOGGER.info(
            "Saved RDB snapshot: path=%s keys=%d ttl_keys=%d",
            path.resolve(),
            len(data),
            len(expires_at),
        )
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
