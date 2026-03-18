from src.cluster.router import ClusterRouter, Node


def test_hash_slot_is_stable_for_same_key() -> None:
    router = ClusterRouter()

    assert router.hash_slot("user:1") == router.hash_slot("user:1")


def test_route_returns_same_node_for_same_key() -> None:
    router = ClusterRouter()
    nodes = [
        Node(name="node-a", host="127.0.0.1", port=7000),
        Node(name="node-b", host="127.0.0.1", port=7001),
        Node(name="node-c", host="127.0.0.1", port=7002),
    ]

    first = router.route("user:1", nodes)
    second = router.route("user:1", nodes)

    assert first == second
