from __future__ import annotations

from dataclasses import dataclass


class Response:
    @staticmethod
    def simple_string(value: str) -> SimpleString:
        return SimpleString(value)

    @staticmethod
    def bulk_string(value: str | None) -> BulkString | NullBulkString:
        if value is None:
            return NullBulkString()
        return BulkString(value)

    @staticmethod
    def integer(value: int) -> Integer:
        return Integer(value)

    @staticmethod
    def error(message: str) -> Error:
        normalized = message if message.startswith("ERR ") or message.startswith("MOVED ") else f"ERR {message}"
        return Error(normalized)


@dataclass(slots=True)
class SimpleString(Response):
    value: str


@dataclass(slots=True)
class BulkString(Response):
    value: str


@dataclass(slots=True)
class Integer(Response):
    value: int


@dataclass(slots=True)
class Error(Response):
    message: str


@dataclass(slots=True)
class NullBulkString(Response):
    pass
