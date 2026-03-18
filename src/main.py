from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from src.cluster.router import ClusterCoordinator, Node
from src.persistence.manager import PersistenceConfig, PersistenceManager
from src.protocol.resp_encoder import RespEncoder
from src.protocol.resp_parser import RespParser
from src.server.dispatcher import Dispatcher
from src.server.tcp_server import AsyncRedisServer
from src.storage.engine import StorageEngine


def build_server(
    host: str,
    port: int,
    data_dir: str | Path = ".",
    cluster_nodes: list[Node] | None = None,
    current_node_name: str = "node-1",
    snapshot_interval: int = 0,
    snapshot_on_shutdown: bool = True,
) -> AsyncRedisServer:
    storage = StorageEngine()
    persistence = PersistenceManager(storage, PersistenceConfig(data_dir=Path(data_dir)))
    persistence.restore()

    current_node = Node(name=current_node_name, host=host, port=port)
    nodes = cluster_nodes or [current_node]
    cluster = ClusterCoordinator(current_node=current_node, nodes=nodes)

    dispatcher = Dispatcher(storage, persistence=persistence, cluster=cluster)
    parser = RespParser()
    encoder = RespEncoder()
    return AsyncRedisServer(
        host=host,
        port=port,
        parser=parser,
        encoder=encoder,
        dispatcher=dispatcher,
        snapshot_callback=persistence.snapshot,
        snapshot_interval=snapshot_interval,
        snapshot_on_shutdown=snapshot_on_shutdown,
    )


async def run_server(
    host: str,
    port: int,
    data_dir: str | Path = ".",
    snapshot_interval: int = 0,
    snapshot_on_shutdown: bool = True,
) -> None:
    server = build_server(
        host,
        port,
        data_dir=data_dir,
        snapshot_interval=snapshot_interval,
        snapshot_on_shutdown=snapshot_on_shutdown,
    )
    await server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Mini Redis TCP server.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=6379, help="Port to bind to.")
    parser.add_argument("--data-dir", default=".", help="Directory for dump.rdb and appendonly.aof.")
    parser.add_argument(
        "--snapshot-interval",
        type=int,
        default=0,
        help="Automatic RDB snapshot interval in seconds. 0 disables periodic snapshots.",
    )
    parser.add_argument(
        "--disable-shutdown-snapshot",
        action="store_true",
        help="Disable automatic snapshot when the server shuts down.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(
        run_server(
            args.host,
            args.port,
            data_dir=args.data_dir,
            snapshot_interval=args.snapshot_interval,
            snapshot_on_shutdown=not args.disable_shutdown_snapshot,
        )
    )


if __name__ == "__main__":
    main()
