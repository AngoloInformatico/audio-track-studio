"""Lifecycle-managed local Uvicorn server used by the desktop window."""

import asyncio
import socket
from contextlib import suppress
from threading import Thread
from time import monotonic, sleep

import uvicorn

from backend.main import app


class DesktopServerError(RuntimeError):
    """Raised when the embedded local server cannot start or stop."""


class DesktopServer:
    """Run FastAPI on a random loopback port without exposing it to the LAN."""

    def __init__(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(128)
        self.port = int(self._socket.getsockname()[1])
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            log_config=None,
            access_log=False,
            lifespan="on",
        )
        self._server = uvicorn.Server(config)
        self._thread = Thread(target=self._serve, name="ats-local-api", daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self, timeout_seconds: float = 15.0) -> None:
        self._thread.start()
        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            if self._server.started:
                return
            if not self._thread.is_alive():
                break
            sleep(0.05)
        self.stop()
        raise DesktopServerError("Il servizio locale non è riuscito ad avviarsi.")

    def stop(self, timeout_seconds: float = 10.0) -> None:
        self._server.should_exit = True
        if self._thread.is_alive():
            self._thread.join(timeout_seconds)
        if self._thread.is_alive():
            self._server.force_exit = True
            self._thread.join(2.0)
        with suppress(OSError):
            self._socket.close()

    def _serve(self) -> None:
        asyncio.run(self._server.serve(sockets=[self._socket]))
