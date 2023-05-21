from abc import ABC, abstractmethod
from contextlib import contextmanager
from random import randint
from threading import Thread
from time import sleep
from typing import Iterator

from .domain import Command, Message, Response
from .mqtt import MqttClient
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


class MqttDevice(Device):

    """Device that sends and recieves messages via an MQTT broker.

    Args:
        mqtt: MQTT client.
        name: Unique name for the device.
        topic: Name of the root topic level.

    """

    def __init__(self, mqtt: MqttClient, name: str, topic: str | None = None) -> None:
        super().__init__()
        self.mqtt = mqtt

        assert name, "Device name cannot be an empty string"
        self._name = name
        self._topic = topic or "devices"

        # Consumer handler
        self.mqtt.observe(self._handle_message)

    @property
    def name(self) -> str:
        """Name of the current device."""
        return self._name

    @property
    def topic(self) -> str:
        """Name of the root topic level."""
        return self._topic

    def _send(self, command: Command) -> None:
        self.mqtt.publish(f"{self.topic}/{self.name}/commands", command.message.serialise())

    def _receive(self, response: Response) -> None:
        ...

    def connect(self) -> None:
        """Connect the MQTT client."""
        self.mqtt.connect()
        # Subscribe to the response topic
        self.mqtt.subscribe(f"{self.topic}/{self.name}/responses")

    def disconnect(self) -> None:
        """Disconnect the MQTT client."""
        self.mqtt.disconnect()

    def is_connected(self) -> bool:
        """Check connection status of the MQTT client."""
        return self.mqtt.is_connected()

    def _handle_message(self, payload: str | bytes | bytearray) -> None:
        response = Response(Message.deserialise(payload))
        self.receive(response)


@contextmanager
def connection(device: Device) -> Iterator[Device]:
    device.connect()
    try:
        yield device
    finally:
        device.disconnect()
