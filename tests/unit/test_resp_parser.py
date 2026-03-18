import pytest

from src.protocol.resp_parser import (
    IncompleteRESPError,
    RespParser,
    RespProtocolError,
)


def test_parse_ping_command() -> None:
    parser = RespParser()
    raw = b"*1\r\n$4\r\nPING\r\n"

    command = parser.parse_command(raw)

    assert command.name == "PING"
    assert command.args == []


def test_parse_set_command() -> None:
    parser = RespParser()
    raw = b"*3\r\n$3\r\nSET\r\n$6\r\nuser:1\r\n$3\r\nkim\r\n"

    command = parser.parse_command(raw)

    assert command.name == "SET"
    assert command.args == ["user:1", "kim"]


def test_parse_get_command() -> None:
    parser = RespParser()
    raw = b"*2\r\n$3\r\nGET\r\n$6\r\nuser:1\r\n"

    command = parser.parse_command(raw)

    assert command.name == "GET"
    assert command.args == ["user:1"]


def test_parse_unicode_bulk_string() -> None:
    parser = RespParser()
    raw = (
        b"*3\r\n"
        b"$3\r\nSET\r\n"
        b"$6\r\nuser:1\r\n"
        b"$9\r\n\xea\xb9\x80\xeb\xb2\x94\xec\x83\x81\r\n"
    )

    command = parser.parse_command(raw)

    assert command.name == "SET"
    assert command.args == ["user:1", "김범상"]


def test_parse_one_returns_consumed_bytes() -> None:
    parser = RespParser()
    raw = b"*1\r\n$4\r\nPING\r\nEXTRA"

    result = parser.parse_one(raw)

    assert result.command.name == "PING"
    assert result.command.args == []
    assert result.consumed == len(b"*1\r\n$4\r\nPING\r\n")


def test_parse_command_rejects_trailing_data() -> None:
    parser = RespParser()
    raw = b"*1\r\n$4\r\nPING\r\nEXTRA"

    with pytest.raises(RespProtocolError, match="trailing data"):
        parser.parse_command(raw)


def test_parse_rejects_non_array_request() -> None:
    parser = RespParser()
    raw = b"+PING\r\n"

    with pytest.raises(RespProtocolError, match="expected RESP array"):
        parser.parse_command(raw)


def test_parse_rejects_empty_array() -> None:
    parser = RespParser()
    raw = b"*0\r\n"

    with pytest.raises(RespProtocolError, match="array length must be greater than zero"):
        parser.parse_command(raw)


def test_parse_rejects_invalid_array_length() -> None:
    parser = RespParser()
    raw = b"*x\r\n"

    with pytest.raises(RespProtocolError, match="invalid array length"):
        parser.parse_command(raw)


def test_parse_rejects_invalid_bulk_length() -> None:
    parser = RespParser()
    raw = b"*1\r\n$x\r\nPING\r\n"

    with pytest.raises(RespProtocolError, match="invalid bulk string length"):
        parser.parse_command(raw)


def test_parse_rejects_null_bulk_string_in_request() -> None:
    parser = RespParser()
    raw = b"*1\r\n$-1\r\n"

    with pytest.raises(RespProtocolError, match="null bulk string is not allowed"):
        parser.parse_command(raw)


def test_parse_raises_incomplete_when_bulk_not_fully_received() -> None:
    parser = RespParser()
    raw = b"*1\r\n$4\r\nPIN"

    with pytest.raises(IncompleteRESPError, match="bulk string data not fully received"):
        parser.parse_one(raw)


def test_parse_raises_incomplete_when_crlf_missing() -> None:
    parser = RespParser()
    raw = b"*1"

    with pytest.raises(IncompleteRESPError, match="missing CRLF after array length"):
        parser.parse_one(raw)


def test_parse_rejects_missing_bulk_prefix() -> None:
    parser = RespParser()
    raw = b"*1\r\n!4\r\nPING\r\n"

    with pytest.raises(RespProtocolError, match="expected bulk string"):
        parser.parse_command(raw)


def test_parse_rejects_invalid_utf8() -> None:
    parser = RespParser()
    raw = b"*1\r\n$2\r\n\xff\xff\r\n"

    with pytest.raises(RespProtocolError, match="invalid UTF-8"):
        parser.parse_command(raw)
