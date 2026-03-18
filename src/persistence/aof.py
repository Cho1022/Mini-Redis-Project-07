from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WRITE_COMMANDS = {"SET", "DEL", "EXPIRE"}


@dataclass(frozen=True, slots=True)
class AofEntry:
    """One append-only command record."""

    command: str
    args: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReplayState:
    """Recovered in-memory state reconstructed from the append-only log."""

    data: dict[str, str]
    expires_at: dict[str, float]


class AofPersistence:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, command: str, *args: str) -> None:
        normalized = command.upper()
        if normalized not in WRITE_COMMANDS:
            raise ValueError(f"Unsupported AOF command: {command}")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"command": normalized, "args": list(args)}

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=True) + "\n")

    def append_entries(self, entries: Iterable[AofEntry]) -> None:
        for entry in entries:
            self.append(entry.command, *entry.args)

    def replay(self) -> ReplayState:
        if not self.path.exists():
            return ReplayState(data={}, expires_at={})

        data: dict[str, str] = {}
        expires_at: dict[str, float] = {}

        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid AOF record at line {line_number}") from exc

                command = str(record.get("command", "")).upper()
                args = tuple(str(arg) for arg in record.get("args", []))
                self._apply(AofEntry(command=command, args=args), data, expires_at)

        return ReplayState(data=data, expires_at=expires_at)

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _apply(
        self,
        entry: AofEntry,
        data: dict[str, str],
        expires_at: dict[str, float],
    ) -> None:
        command = entry.command
        args = entry.args

        if command == "SET":
            if len(args) != 2:
                raise ValueError("SET requires 2 arguments in AOF replay")
            key, value = args
            data[key] = value
            expires_at.pop(key, None)
            return

        if command == "DEL":
            if len(args) != 1:
                raise ValueError("DEL requires 1 argument in AOF replay")
            key = args[0]
            data.pop(key, None)
            expires_at.pop(key, None)
            return

        if command == "EXPIRE":
            if len(args) != 2:
                raise ValueError("EXPIRE requires 2 arguments in AOF replay")
            key, expires_at_value = args
            if key in data:
                expires_at[key] = float(expires_at_value)
            return

        raise ValueError(f"Unsupported AOF command during replay: {command}")
