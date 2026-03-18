from __future__ import annotations

import argparse
import socket
from typing import Iterable


def encode_command(*parts: str) -> bytes:
    encoded_parts = [part.encode("utf-8") for part in parts]
    chunks = [f"*{len(encoded_parts)}\r\n".encode("ascii")]
    for part in encoded_parts:
        chunks.append(f"${len(part)}\r\n".encode("ascii"))
        chunks.append(part + b"\r\n")
    return b"".join(chunks)


def run_commands(host: str, port: int, commands: Iterable[list[str]]) -> list[bytes]:
    responses: list[bytes] = []
    with socket.create_connection((host, port), timeout=5) as sock:
        for command in commands:
            payload = encode_command(*command)
            sock.sendall(payload)
            responses.append(sock.recv(4096))
    return responses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send RESP commands to the Mini Redis server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host.")
    parser.add_argument("--port", type=int, default=6379, help="Server port.")
    parser.add_argument(
        "commands",
        nargs="+",
        help="Commands separated by ';' and parts separated by spaces. Example: \"PING\" \"SET user:1 kim\"",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command_groups = [segment.split() for segment in args.commands]
    responses = run_commands(args.host, args.port, command_groups)
    for response in responses:
        print(response.decode("utf-8", errors="replace").rstrip())


if __name__ == "__main__":
    main()
