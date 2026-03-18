from __future__ import annotations

from dataclasses import dataclass

from src.core.command import Command
from src.core.exceptions import NeedMoreData, ProtocolError


class RespProtocolError(ProtocolError):
    """Raised when the incoming bytes are not valid RESP."""


class IncompleteRESPError(NeedMoreData):
    """Raised when the current TCP buffer does not contain a full command yet."""


@dataclass(slots=True, frozen=True)
class ParseResult:
    command: Command
    consumed: int


class RespParser:
    """Parse a RESP request as an array of bulk strings."""

    CRLF = b"\r\n"

    def parse(self, raw: bytes) -> tuple[Command, int]:
        result = self.parse_one(raw)
        return result.command, result.consumed

    def parse_command(self, raw: bytes) -> Command:
        result = self.parse_one(raw)
        if result.consumed != len(raw):
            raise RespProtocolError("trailing data after complete command")
        return result.command

    def parse_one(self, raw: bytes) -> ParseResult:
        if not raw:
            raise IncompleteRESPError("empty buffer")

        idx = 0
        if raw[idx:idx + 1] != b"*":
            raise RespProtocolError("expected RESP array")

        idx += 1
        array_count, idx = self._read_number_line(raw, idx, "array length")
        if array_count <= 0:
            raise RespProtocolError("array length must be greater than zero")

        parts: list[str] = []
        for _ in range(array_count):
            if idx >= len(raw):
                raise IncompleteRESPError("waiting for next bulk string")

            if raw[idx:idx + 1] != b"$":
                raise RespProtocolError("expected bulk string")

            idx += 1
            bulk_len, idx = self._read_number_line(raw, idx, "bulk string length")
            if bulk_len < 0:
                raise RespProtocolError("null bulk string is not allowed in request")

            if len(raw) < idx + bulk_len + 2:
                raise IncompleteRESPError("bulk string data not fully received")

            bulk_data = raw[idx:idx + bulk_len]
            idx += bulk_len

            if raw[idx:idx + 2] != self.CRLF:
                raise RespProtocolError("missing CRLF after bulk string data")

            idx += 2
            try:
                part = bulk_data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RespProtocolError("request contains invalid UTF-8") from exc

            parts.append(part)

        return ParseResult(command=Command(name=parts[0], args=parts[1:]), consumed=idx)

    def _read_number_line(self, raw: bytes, start: int, context: str) -> tuple[int, int]:
        line_end = raw.find(self.CRLF, start)
        if line_end == -1:
            raise IncompleteRESPError(f"missing CRLF after {context}")

        number_bytes = raw[start:line_end]
        if not number_bytes:
            raise RespProtocolError(f"empty {context}")

        try:
            number = int(number_bytes.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise RespProtocolError(f"invalid {context}") from exc

        return number, line_end + 2
