import pytest

from src.core.response import BulkString, Error, Integer, NullBulkString, SimpleString
from src.protocol.resp_encoder import RespEncoder


def test_encode_simple_string() -> None:
    encoder = RespEncoder()

    result = encoder.encode(SimpleString("PONG"))

    assert result == b"+PONG\r\n"


def test_encode_bulk_string() -> None:
    encoder = RespEncoder()

    result = encoder.encode(BulkString("kim"))

    assert result == b"$3\r\nkim\r\n"


def test_encode_bulk_string_with_unicode() -> None:
    encoder = RespEncoder()

    result = encoder.encode(BulkString("김범상"))

    encoded = "김범상".encode("utf-8")
    assert result == f"${len(encoded)}\r\n".encode("ascii") + encoded + b"\r\n"


def test_encode_null_bulk_string() -> None:
    encoder = RespEncoder()

    result = encoder.encode(NullBulkString())

    assert result == b"$-1\r\n"


def test_encode_integer() -> None:
    encoder = RespEncoder()

    result = encoder.encode(Integer(123))

    assert result == b":123\r\n"


def test_encode_error() -> None:
    encoder = RespEncoder()

    result = encoder.encode(Error("ERR wrong number of arguments"))

    assert result == b"-ERR wrong number of arguments\r\n"


def test_encode_simple_string_rejects_crlf() -> None:
    encoder = RespEncoder()

    with pytest.raises(ValueError, match="SimpleString cannot contain CR or LF"):
        encoder.encode(SimpleString("OK\r\nBAD"))


def test_encode_error_rejects_crlf() -> None:
    encoder = RespEncoder()

    with pytest.raises(ValueError, match="Error cannot contain CR or LF"):
        encoder.encode(Error("ERR bad\r\nmessage"))
