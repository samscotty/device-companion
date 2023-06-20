import dataclasses
import json
from datetime import datetime
from typing import Callable, Type


@dataclasses.dataclass
class Message:
    payload: str | None
    timestamp: str = dataclasses.field(init=False)

    def serialise(self) -> str:
        """Serialise message to a JSON formatted `str`."""
        obj = dataclasses.asdict(self)
        return json.dumps(obj)

    @classmethod
    def deserialise(cls, obj: str | bytes | bytearray) -> "Message":
        """Deserialise JSON object to a `Message`."""
        try:
            message = json.loads(obj)
            payload = str(message["payload"])
        except (KeyError, TypeError, ValueError):
            return cls(None)
        else:
            return cls(payload)

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()

    def __bool__(self) -> bool:
        return bool(self.payload)


@dataclasses.dataclass
class Response:
    message: Message


@dataclasses.dataclass
class Acknowledgement:
    matchers: list[Callable[[Response], bool]] = dataclasses.field(default_factory=list)
    timeout: float = 5.0

    def __post_init__(self):
        if not self.matchers or self.timeout < 0:
            self.timeout = 0.0

    def __bool__(self) -> bool:
        return bool(self.matchers)


@dataclasses.dataclass
class Command:
    message: Message
    ack: Acknowledgement = Acknowledgement()


@dataclasses.dataclass
class Error:
    message: Message
    exception: Type[Exception] = RuntimeError
