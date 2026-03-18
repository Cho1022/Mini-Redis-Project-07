import asyncio
from pathlib import Path

from src.main import build_server


async def _send_command(host: str, port: int, payload: bytes) -> bytes:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(payload)
    await writer.drain()
    response = await reader.read(4096)
    writer.close()
    await writer.wait_closed()
    return response


async def _exercise_server_flow(tmp_path: Path) -> None:
    server = build_server("127.0.0.1", 0, data_dir=tmp_path)
    await server.start()

    try:
        port = server.port

        assert await _send_command("127.0.0.1", port, b"*1\r\n$4\r\nPING\r\n") == b"+PONG\r\n"
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*3\r\n$3\r\nSET\r\n$6\r\nuser:1\r\n$3\r\nkim\r\n",
        ) == b"+OK\r\n"
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*2\r\n$3\r\nGET\r\n$6\r\nuser:1\r\n",
        ) == b"$3\r\nkim\r\n"
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*2\r\n$6\r\nEXISTS\r\n$6\r\nuser:1\r\n",
        ) == b":1\r\n"
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*3\r\n$6\r\nEXPIRE\r\n$6\r\nuser:1\r\n$1\r\n5\r\n",
        ) == b":1\r\n"
        assert await _send_command("127.0.0.1", port, b"*1\r\n$4\r\nSAVE\r\n") == b"+OK\r\n"

        ttl_response = await _send_command(
            "127.0.0.1",
            port,
            b"*2\r\n$3\r\nTTL\r\n$6\r\nuser:1\r\n",
        )
        assert ttl_response.startswith(b":")

        assert await _send_command(
            "127.0.0.1",
            port,
            b"*2\r\n$3\r\nDEL\r\n$6\r\nuser:1\r\n",
        ) == b":1\r\n"
    finally:
        await server.close()


async def _exercise_fragmented_request(tmp_path: Path) -> None:
    server = build_server("127.0.0.1", 0, data_dir=tmp_path)
    await server.start()

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
        writer.write(b"*1\r\n$4\r\nPI")
        await writer.drain()
        await asyncio.sleep(0.05)
        writer.write(b"NG\r\n")
        await writer.drain()

        response = await reader.read(4096)
        assert response == b"+PONG\r\n"

        writer.close()
        await writer.wait_closed()
    finally:
        await server.close()


async def _exercise_multiple_commands_in_one_buffer(tmp_path: Path) -> None:
    server = build_server("127.0.0.1", 0, data_dir=tmp_path)
    await server.start()

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
        writer.write(
            b"*1\r\n$4\r\nPING\r\n"
            b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
            b"*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n"
        )
        await writer.drain()

        response = await reader.read(4096)
        assert response == b"+PONG\r\n+OK\r\n$5\r\nvalue\r\n"

        writer.close()
        await writer.wait_closed()
    finally:
        await server.close()


async def _exercise_restart_recovery(tmp_path: Path) -> None:
    first_server = build_server("127.0.0.1", 0, data_dir=tmp_path)
    await first_server.start()

    try:
        port = first_server.port
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*3\r\n$3\r\nSET\r\n$9\r\nprofile:1\r\n$3\r\nkim\r\n",
        ) == b"+OK\r\n"
        assert await _send_command("127.0.0.1", port, b"*1\r\n$4\r\nSAVE\r\n") == b"+OK\r\n"
    finally:
        await first_server.close()

    second_server = build_server("127.0.0.1", 0, data_dir=tmp_path)
    await second_server.start()
    try:
        restored = await _send_command(
            "127.0.0.1",
            second_server.port,
            b"*2\r\n$3\r\nGET\r\n$9\r\nprofile:1\r\n",
        )
        assert restored == b"$3\r\nkim\r\n"
    finally:
        await second_server.close()


async def _exercise_periodic_snapshot_and_aof_cleanup(tmp_path: Path) -> None:
    server = build_server("127.0.0.1", 0, data_dir=tmp_path, snapshot_interval=1)
    await server.start()

    try:
        port = server.port
        assert await _send_command(
            "127.0.0.1",
            port,
            b"*3\r\n$3\r\nSET\r\n$8\r\nauto:key\r\n$5\r\nvalue\r\n",
        ) == b"+OK\r\n"

        await asyncio.sleep(1.2)

        assert (tmp_path / "dump.rdb").exists()
        assert not (tmp_path / "appendonly.aof").exists()
    finally:
        await server.close()


async def _exercise_shutdown_snapshot_and_aof_cleanup(tmp_path: Path) -> None:
    server = build_server("127.0.0.1", 0, data_dir=tmp_path, snapshot_on_shutdown=True)
    await server.start()

    port = server.port
    assert await _send_command(
        "127.0.0.1",
        port,
        b"*3\r\n$3\r\nSET\r\n$8\r\nstop:key\r\n$5\r\nvalue\r\n",
    ) == b"+OK\r\n"

    await server.close()

    assert (tmp_path / "dump.rdb").exists()
    assert not (tmp_path / "appendonly.aof").exists()


def test_tcp_server_end_to_end_flow(tmp_path: Path) -> None:
    asyncio.run(_exercise_server_flow(tmp_path))


def test_tcp_server_handles_fragmented_request(tmp_path: Path) -> None:
    asyncio.run(_exercise_fragmented_request(tmp_path))


def test_tcp_server_handles_multiple_commands_in_one_buffer(tmp_path: Path) -> None:
    asyncio.run(_exercise_multiple_commands_in_one_buffer(tmp_path))


def test_tcp_server_restores_data_after_restart(tmp_path: Path) -> None:
    asyncio.run(_exercise_restart_recovery(tmp_path))


def test_tcp_server_takes_periodic_snapshot_and_cleans_aof(tmp_path: Path) -> None:
    asyncio.run(_exercise_periodic_snapshot_and_aof_cleanup(tmp_path))


def test_tcp_server_snapshots_on_shutdown_and_cleans_aof(tmp_path: Path) -> None:
    asyncio.run(_exercise_shutdown_snapshot_and_aof_cleanup(tmp_path))
