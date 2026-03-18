from src.cluster.router import ClusterCoordinator, Node
from src.core.command import Command
from src.core.response import BulkString, Error, Integer, NullBulkString, SimpleString
from src.server.dispatcher import Dispatcher
from src.storage.engine import StorageEngine


def test_dispatcher_connects_core_commands() -> None:
    dispatcher = Dispatcher(StorageEngine())

    assert dispatcher.dispatch(Command("PING", [])).value == "PONG"
    assert dispatcher.dispatch(Command("SET", ["user:1", "kim"])).value == "OK"

    get_response = dispatcher.dispatch(Command("GET", ["user:1"]))
    assert isinstance(get_response, BulkString)
    assert get_response.value == "kim"

    exists_response = dispatcher.dispatch(Command("EXISTS", ["user:1"]))
    assert isinstance(exists_response, Integer)
    assert exists_response.value == 1

    expire_response = dispatcher.dispatch(Command("EXPIRE", ["user:1", "5"]))
    assert isinstance(expire_response, Integer)
    assert expire_response.value == 1

    ttl_response = dispatcher.dispatch(Command("TTL", ["user:1"]))
    assert isinstance(ttl_response, Integer)
    assert ttl_response.value >= 0

    del_response = dispatcher.dispatch(Command("DEL", ["user:1"]))
    assert isinstance(del_response, Integer)
    assert del_response.value == 1

    missing_response = dispatcher.dispatch(Command("GET", ["user:1"]))
    assert isinstance(missing_response, NullBulkString)


def test_dispatcher_ping_returns_simple_string() -> None:
    response = Dispatcher(StorageEngine()).dispatch(Command("PING", []))

    assert isinstance(response, SimpleString)
    assert response.value == "PONG"


def test_dispatcher_returns_moved_for_remote_key() -> None:
    local = Node(name="node-a", host="127.0.0.1", port=7000)
    remote = Node(name="node-b", host="127.0.0.1", port=7001)
    cluster = ClusterCoordinator(current_node=local, nodes=[local, remote])
    dispatcher = Dispatcher(StorageEngine(), cluster=cluster)

    remote_key = next(
        key for key in (f"user:{index}" for index in range(100))
        if not cluster.is_local_key(key)
    )
    response = dispatcher.dispatch(Command("GET", [remote_key]))

    assert isinstance(response, Error)
    assert response.message.startswith("MOVED ")
