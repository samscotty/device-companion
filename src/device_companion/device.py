from abc import ABC, abstractmethod
from contextlib import contextmanager
from random import randint
from threading import Thread
from time import sleep
from typing import Iterator

from .domain import Command, Message, Response
from .watcher import AckWatcher


class Device(ABC):
    def __init__(self) -> None:
        self.watcher = AckWatcher()
        ...

    def send(self, command: Command) -> None:
        self._send(command)
        self.watcher(command)

    def receive(self, response: Response) -> None:
        self._receive(response)
        self.watcher(response)

    @abstractmethod
    def _send(self, command: Command) -> None:
        ...

    @abstractmethod
    def _receive(self, response: Response) -> None:
        ...

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...


class DummyDevice(Device):
    def __init__(self) -> None:
        super().__init__()
        self._connected: bool = False

    def _send(self, command: Command) -> None:
        # Generate a standard response;
        response = Response(Message("ACK"))
        Thread(target=self.receive, args=(response,)).start()

    def _receive(self, response: Response) -> None:
        # Simulate some intermittent spam
        for _ in range(randint(0, 5)):
            self.watcher(Response(Message("IDLE")))
        # Simulate waiting for the response
        sleep(randint(1, 10))

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected


@contextmanager
def connection(device: Device) -> Iterator[Device]:
    device.connect()
    try:
        yield device
    finally:
        device.disconnect()
