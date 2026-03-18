from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Serializable snapshot of the in-memory dataset."""

    data: dict[str, str]
    expires_at: dict[str, float]


class RdbPersistence:
    """
    Save and load a point-in-time snapshot of the current dataset.

    The format is intentionally simple JSON so the team can inspect it during
    development and explain the recovery flow during the demo.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(
        self,
        data: Mapping[str, str],
        expires_at: Mapping[str, float] | None = None,
    ) -> Path:
        snapshot = {
            "data": dict(data),
            "expires_at": dict(expires_at or {}),
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as temp_file:
            json.dump(snapshot, temp_file, ensure_ascii=True, indent=2, sort_keys=True)
            temp_path = Path(temp_file.name)

        os.replace(temp_path, self.path)
        return self.path

    def load(self) -> Snapshot:
        if not self.path.exists():
            return Snapshot(data={}, expires_at={})

        with self.path.open("r", encoding="utf-8") as file:
            content = file.read().strip()

        if not content:
            return Snapshot(data={}, expires_at={})

        try:
            raw = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid RDB snapshot format in {self.path}") from exc

        data = raw.get("data", {})
        expires_at = raw.get("expires_at", {})

        if not isinstance(data, dict) or not isinstance(expires_at, dict):
            raise ValueError("Invalid RDB snapshot format")

        return Snapshot(
            data={str(key): str(value) for key, value in data.items()},
            expires_at={str(key): float(value) for key, value in expires_at.items()},
        )
