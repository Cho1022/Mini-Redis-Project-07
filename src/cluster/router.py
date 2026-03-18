from __future__ import annotations

import hashlib
from dataclasses import dataclass


TOTAL_HASH_SLOTS = 16384


@dataclass(frozen=True, slots=True)
class Node:
    """Logical cluster node used by the router."""

    name: str
    host: str
    port: int


class ClusterRouter:
    def hash_slot(self, key: str) -> int:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return int(digest, 16) % TOTAL_HASH_SLOTS

    def route(self, key: str, nodes: list[Node]) -> Node:
        if not nodes:
            raise ValueError("At least one node is required for routing")

        slot = self.hash_slot(key)
        index = slot % len(nodes)
        return nodes[index]


class ClusterCoordinator:
    """Decides whether the current node owns a given key."""

    def __init__(self, current_node: Node, nodes: list[Node], router: ClusterRouter | None = None) -> None:
        self.current_node = current_node
        self.nodes = nodes
        self.router = router or ClusterRouter()

    def owner_for_key(self, key: str) -> Node:
        return self.router.route(key, self.nodes)

    def is_local_key(self, key: str) -> bool:
        owner = self.owner_for_key(key)
        return owner == self.current_node

    def moved_error(self, key: str) -> str | None:
        owner = self.owner_for_key(key)
        if owner == self.current_node:
            return None
        slot = self.router.hash_slot(key)
        return f"MOVED {slot} {owner.host}:{owner.port}"
