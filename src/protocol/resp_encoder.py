from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from src.core.response import BulkString, Error, Integer, NullBulkString, Response, SimpleString
except ImportError:
    class Response:
        pass

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


class RespEncoder:
    """Encode internal response objects into RESP bytes."""

    CRLF = b"\r\n"

    def encode(self, response: Response | Any) -> bytes:
        if isinstance(response, SimpleString) or self._is_named_type(response, "SimpleString"):
            return self._encode_simple_string(response.value)

        if isinstance(response, BulkString) or self._is_named_type(response, "BulkString"):
            return self._encode_bulk_string(response.value)

        if isinstance(response, NullBulkString) or self._is_named_type(response, "NullBulkString"):
            return b"$-1\r\n"

        if isinstance(response, Integer) or self._is_named_type(response, "Integer"):
            return self._encode_integer(response.value)

        if isinstance(response, Error) or self._is_named_type(response, "Error"):
            return self._encode_error(response.message)

        raise TypeError(f"unsupported response type: {type(response).__name__}")

    def _encode_simple_string(self, value: str) -> bytes:
        self._validate_no_crlf(value, "SimpleString")
        return b"+" + value.encode("utf-8") + self.CRLF

    def _encode_bulk_string(self, value: str) -> bytes:
        encoded = value.encode("utf-8")
        return b"$" + str(len(encoded)).encode("ascii") + self.CRLF + encoded + self.CRLF

    def _encode_integer(self, value: int) -> bytes:
        return b":" + str(value).encode("ascii") + self.CRLF

    def _encode_error(self, message: str) -> bytes:
        self._validate_no_crlf(message, "Error")
        return b"-" + message.encode("utf-8") + self.CRLF

    @staticmethod
    def _validate_no_crlf(value: str, type_name: str) -> None:
        if "\r" in value or "\n" in value:
            raise ValueError(f"{type_name} cannot contain CR or LF")

    @staticmethod
    def _is_named_type(response: Any, type_name: str) -> bool:
        return type(response).__name__ == type_name
