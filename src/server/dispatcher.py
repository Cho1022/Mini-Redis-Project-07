from __future__ import annotations

from src.core.command import Command
from src.core.response import Response
from src.storage.engine import StorageEngine


class Dispatcher:
    def __init__(self, storage: StorageEngine) -> None:
        self._storage = storage

    def dispatch(self, command: Command) -> Response:
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
        except ValueError as exc:
            return Response.error(str(exc))

        return Response.error(f"unknown command '{command.name}'")

    def _dispatch_ping(self, args: list[str]) -> Response:
        self._ensure_arity("PING", args, 0)
        return Response.simple_string("PONG")

    def _dispatch_set(self, args: list[str]) -> Response:
        self._ensure_arity("SET", args, 2)
        self._storage.set(args[0], args[1])
        return Response.simple_string("OK")

    def _dispatch_get(self, args: list[str]) -> Response:
        self._ensure_arity("GET", args, 1)
        return Response.bulk_string(self._storage.get(args[0]))

    def _dispatch_del(self, args: list[str]) -> Response:
        self._ensure_arity("DEL", args, 1)
        return Response.integer(self._storage.delete(args[0]))

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

        return Response.integer(self._storage.expire(args[0], seconds))

    def _dispatch_ttl(self, args: list[str]) -> Response:
        self._ensure_arity("TTL", args, 1)
        return Response.integer(self._storage.ttl(args[0]))

    @staticmethod
    def _ensure_arity(command_name: str, args: list[str], expected: int) -> None:
        if len(args) != expected:
            raise ValueError(f"wrong number of arguments for '{command_name.lower()}' command")
