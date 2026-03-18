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
    """
    Route a key to a node using a stable hash-slot calculation.

    This is a lightweight educational version of Redis cluster routing that is
    good enough to explain scale-out decisions in the project demo.
    """

    def hash_slot(self, key: str) -> int:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return int(digest, 16) % TOTAL_HASH_SLOTS

    def route(self, key: str, nodes: list[Node]) -> Node:
        if not nodes:
            raise ValueError("At least one node is required for routing")

        slot = self.hash_slot(key)
        index = slot % len(nodes)
        return nodes[index]
