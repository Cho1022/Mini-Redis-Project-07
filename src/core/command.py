from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Command:
    name: str
    args: list[str]

    def normalized_name(self) -> str:
        return self.name.strip().upper()

    def require_arity(self, expected: int) -> None:
        actual = len(self.args)
        if actual != expected:
            raise ValueError(
                f"wrong number of arguments for '{self.normalized_name().lower()}' command"
            )

    def key(self) -> str | None:
        if not self.args:
            return None
        if self.normalized_name() in {"PING", "SAVE"}:
            return None
        return self.args[0]
