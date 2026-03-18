from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Command:
    name: str
    args: list[str] = field(default_factory=list)

    def normalized_name(self) -> str:
        return self.name.strip().upper()

    def require_arity(self, expected: int) -> None:
        actual = len(self.args)
        if actual != expected:
            raise ValueError(
                f"wrong number of arguments for '{self.normalized_name().lower()}' command"
            )
