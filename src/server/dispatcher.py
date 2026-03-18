from __future__ import annotations

from src.cluster.router import ClusterCoordinator
from src.core.command import Command
from src.core.response import Response
from src.persistence.manager import PersistenceManager
from src.storage.engine import StorageEngine


class Dispatcher:
    def __init__(
        self,
        storage: StorageEngine,
        persistence: PersistenceManager | None = None,
        cluster: ClusterCoordinator | None = None,
    ) -> None:
        self._storage = storage
        self._persistence = persistence
        self._cluster = cluster

    def dispatch(self, command: Command) -> Response:
        route_error = self._route_error(command)
        if route_error is not None:
            return Response.error(route_error)

        name = command.normalized_name()
        args = command.args

        try:
            if name == "PING":
                return self._dispatch_ping(args)
            if name == "SET":
                return self._dispatch_set(args)
            if name == "GET":
                return self._dispatch_get(args)
            if name == "DEL":
                return self._dispatch_del(args)
            if name == "EXISTS":
                return self._dispatch_exists(args)
            if name == "EXPIRE":
                return self._dispatch_expire(args)
            if name == "TTL":
                return self._dispatch_ttl(args)
            if name == "SAVE":
                return self._dispatch_save(args)
        except ValueError as exc:
            return Response.error(str(exc))

        return Response.error(f"unknown command '{command.name}'")

    def _dispatch_ping(self, args: list[str]) -> Response:
        self._ensure_arity("PING", args, 0)
        return Response.simple_string("PONG")

    def _dispatch_set(self, args: list[str]) -> Response:
        self._ensure_arity("SET", args, 2)
        self._storage.set(args[0], args[1])
        self._record_write("SET", args[0], args[1])
        return Response.simple_string("OK")

    def _dispatch_get(self, args: list[str]) -> Response:
        self._ensure_arity("GET", args, 1)
        return Response.bulk_string(self._storage.get(args[0]))

    def _dispatch_del(self, args: list[str]) -> Response:
        self._ensure_arity("DEL", args, 1)
        deleted = self._storage.delete(args[0])
        if deleted:
            self._record_write("DEL", args[0])
        return Response.integer(deleted)

    def _dispatch_exists(self, args: list[str]) -> Response:
        self._ensure_arity("EXISTS", args, 1)
        return Response.integer(self._storage.exists(args[0]))

    def _dispatch_expire(self, args: list[str]) -> Response:
        self._ensure_arity("EXPIRE", args, 2)
        try:
            seconds = int(args[1])
        except ValueError as exc:
            raise ValueError("value is not an integer or out of range") from exc

        if seconds <= 0:
            raise ValueError("value is not an integer or out of range")

        updated = self._storage.expire(args[0], seconds)
        if updated:
            self._record_write("EXPIRE", args[0], args[1])
        return Response.integer(updated)

    def _dispatch_ttl(self, args: list[str]) -> Response:
        self._ensure_arity("TTL", args, 1)
        return Response.integer(self._storage.ttl(args[0]))

    def _dispatch_save(self, args: list[str]) -> Response:
        self._ensure_arity("SAVE", args, 0)
        if self._persistence is None:
            return Response.error("persistence is not enabled")
        self._persistence.snapshot()
        return Response.simple_string("OK")

    def _record_write(self, command: str, *args: str) -> None:
        if self._persistence is not None:
            self._persistence.record_write(command, *args)

    def _route_error(self, command: Command) -> str | None:
        if self._cluster is None:
            return None
        key = command.key()
        if key is None:
            return None
        return self._cluster.moved_error(key)

    @staticmethod
    def _ensure_arity(command_name: str, args: list[str], expected: int) -> None:
        if len(args) != expected:
            raise ValueError(f"wrong number of arguments for '{command_name.lower()}' command")
