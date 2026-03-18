import asyncio
import logging

from src.core.exceptions import NeedMoreData, ProtocolError
from src.core.response import Response


LOGGER = logging.getLogger(__name__)


class AsyncRedisServer:
    def __init__(self, host: str, port: int, parser, encoder, dispatcher) -> None:
        self._host = host
        self._port = port
        self._parser = parser
        self._encoder = encoder
        self._dispatcher = dispatcher

    async def serve_forever(self) -> None:
        server = await asyncio.start_server(self.handle_client, self._host, self._port)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        LOGGER.info("Mini Redis server listening on %s", addresses)
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        buffer = b""
        LOGGER.info("Client connected: %s", peer)

        try:
            while not reader.at_eof():
                chunk = await reader.read(4096)
                if not chunk:
                    break
                buffer += chunk

                while buffer:
                    try:
                        command, consumed = self._parser.parse(buffer)
                    except NeedMoreData:
                        break
                    except ProtocolError as exc:
                        await self._send_response(writer, Response.error(str(exc)))
                        buffer = b""
                        break

                    buffer = buffer[consumed:]
                    response = self._dispatcher.dispatch(command)
                    await self._send_response(writer, response)
        except Exception:
            LOGGER.exception("Unexpected error while handling client %s", peer)
        finally:
            writer.close()
            await writer.wait_closed()
            LOGGER.info("Client disconnected: %s", peer)

    async def _send_response(self, writer: asyncio.StreamWriter, response: Response) -> None:
        writer.write(self._encoder.encode(response))
        await writer.drain()
