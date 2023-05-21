import dataclasses
import json
from datetime import datetime
from typing import Callable, Type


@dataclasses.dataclass()
class Message:
    string: str | None
    timestamp: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()

    def serialise(self) -> str:
        payload = dataclasses.asdict(self)
        return json.dumps(payload)

    @classmethod
    def deserialise(cls, obj: str | bytes | bytearray) -> "Message":
        try:
            payload = json.loads(obj)
            message = str(payload["string"])
        except (KeyError, TypeError, ValueError):
            return cls(None)
        else:
            return cls(message)

    def __bool__(self) -> bool:
        return bool(self.string)


@dataclasses.dataclass
class Command:
    message: Message
    timeout: float = 5.0
    acks: list[Callable[[Message], bool]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Response:
    message: Message


@dataclasses.dataclass
class Error:
    message: Message
    exception: Type[Exception] = RuntimeError
