import asyncio
import socket
import threading
import time
from contextlib import closing

import httpx
import pytest
from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, Scope
from httpx import URL, AsyncClient
from uvicorn import Config
from uvicorn.main import Server


class TestApp:
    def __init__(self):
        self._counter = 0

    @property
    def counter(self):
        return self._counter

    async def __call__(self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable):
        assert scope["type"] == "http"

        if scope["path"].startswith("/ping"):
            await self.handle_ping(scope, receive, send)
        if scope["path"].startswith("/slow_response"):
            await self.slow_response(scope, receive, send)
        elif scope["path"].startswith("/sometimes_slow_response"):
            await self.handle_sometimes_slow_response(scope, receive, send)
        elif scope["path"].startswith("/bad_request"):
            await self.handle_bad_request(scope, receive, send)
        elif scope["path"].startswith("/sometimes_error"):
            await self.handle_sometimes_error(scope, receive, send)

    @staticmethod
    async def slow_response(_: Scope, __: ASGIReceiveCallable, send: ASGISendCallable):
        await asyncio.sleep(1.0)
        await send(
            {
                "type": "http.response.start",
                "status": httpx.codes.OK.value,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, world!"})

    async def handle_sometimes_slow_response(self, _: Scope, __: ASGIReceiveCallable, send: ASGISendCallable):
        self._counter += 1
        if self._counter < 3:
            await asyncio.sleep(1.0)

        await send(
            {
                "type": "http.response.start",
                "status": httpx.codes.OK.value,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, world!"})

    async def handle_ping(self, _: Scope, __: ASGIReceiveCallable, send: ASGISendCallable):
        self._counter += 1

        await send(
            {
                "type": "http.response.start",
                "status": httpx.codes.OK.value,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, world!"})

    async def handle_sometimes_error(self, _: Scope, __: ASGIReceiveCallable, send: ASGISendCallable):
        self._counter += 1

        if self._counter == 3:
            await send(
                {
                    "type": "http.response.start",
                    "status": httpx.codes.OK.value,
                    "headers": [[b"content-type", b"application/octet-stream"]],
                }
            )
            await send({"type": "http.response.body", "body": b"body"})
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": httpx.codes.BAD_REQUEST.value,
                    "headers": [[b"content-type", b"application/octet-stream"]],
                }
            )
            await send({"type": "http.response.body", "body": b"body"})

    async def handle_bad_request(self, _: Scope, __: ASGIReceiveCallable, send: ASGISendCallable):
        self._counter += 1

        await send(
            {
                "type": "http.response.start",
                "status": httpx.codes.BAD_REQUEST.value,
                "headers": [[b"content-type", b"application/octet-stream"]],
            }
        )
        await send({"type": "http.response.body", "body": b"body"})


class TestServer(Server):
    def __init__(self, config: Config):
        super().__init__(config=config)
        self.restart_requested = asyncio.Event()

    @property
    def url(self) -> URL:
        return URL(f"http://{self.config.host}:{self.config.port}/")

    def install_signal_handlers(self) -> None:
        # Disable the default installation of handlers for signals such as SIGTERM,
        # because it can only be done in the main thread.
        pass

    async def serve(self, sockets=None):
        loop = asyncio.get_event_loop()
        tasks = {
            loop.create_task(super().serve(sockets=sockets)),
            loop.create_task(self.watch_restarts()),
        }
        await asyncio.wait(tasks)

    async def restart(self) -> None:  # pragma: nocover
        # This coroutine may be called from a different thread than the one the
        # server is running on, and from an async environment that's not asyncio.
        # For this reason, we use an event to coordinate with the server
        # instead of calling shutdown()/startup() directly, and should not make
        # any asyncio-specific operations.
        self.started = False
        self.restart_requested.set()
        while not self.started:
            await asyncio.sleep(0.2)

    async def watch_restarts(self):  # pragma: nocover
        while True:
            if self.should_exit:
                return

            try:
                await asyncio.wait_for(self.restart_requested.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            self.restart_requested.clear()
            await self.shutdown()
            await self.startup()


def serve_in_thread(server: Server):
    thread = threading.Thread(target=server.run)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        yield server
    finally:
        server.should_exit = True
        thread.join()


def get_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture()
def server():
    config = Config(app=TestApp(), lifespan="off", loop="asyncio", port=get_free_port())
    server = TestServer(config=config)
    yield from serve_in_thread(server)


@pytest.fixture()
def async_client():
    yield AsyncClient(timeout=20)
