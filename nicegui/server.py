from __future__ import annotations

import multiprocessing
import socket
import time
from threading import Thread
from typing import List, Optional

import uvicorn

from . import core, storage
from .native import native


class CustomServerConfig(uvicorn.Config):
    storage_secret: Optional[str] = None
    method_queue: Optional[multiprocessing.Queue] = None
    response_queue: Optional[multiprocessing.Queue] = None


class Server(uvicorn.Server):
    instance: Server

    @classmethod
    def create_singleton(cls, config: CustomServerConfig) -> None:
        """Create a singleton instance of the server."""
        cls.instance = cls(config=config)

    def run(self, sockets: Optional[List[socket.socket]] = None) -> None:
        self.instance = self
        assert isinstance(self.config, CustomServerConfig)
        if self.config.method_queue is not None and self.config.response_queue is not None:
            core.app.native.main_window = native.WindowProxy()
            native.method_queue = self.config.method_queue
            native.response_queue = self.config.response_queue

        storage.set_storage_secret(self.config.storage_secret)
        super().run(sockets=sockets)


class ThreadedServer(Server):
    thread: Thread

    def run_in_thread(self, sockets: Optional[List[socket.socket]] = None) -> None:
        self.thread = Thread(target=self.run, args=[sockets])
        self.thread.start()
        while not self.started:
            time.sleep(1e-03)

    def stop(self):
        self.should_exit = True
        self.thread.join()
