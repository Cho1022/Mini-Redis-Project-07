from __future__ import annotations

import argparse
import asyncio
import logging

from src.protocol.resp_encoder import RespEncoder
from src.protocol.resp_parser import RespParser
from src.server.dispatcher import Dispatcher
from src.server.tcp_server import AsyncRedisServer
from src.storage.engine import StorageEngine


def build_server(host: str, port: int) -> AsyncRedisServer:
    storage = StorageEngine()
    dispatcher = Dispatcher(storage)
    parser = RespParser()
    encoder = RespEncoder()
    return AsyncRedisServer(host=host, port=port, parser=parser, encoder=encoder, dispatcher=dispatcher)


async def run_server(host: str, port: int) -> None:
    server = build_server(host, port)
    await server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mini Redis TCP server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=6379, help="Port to bind to.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()
