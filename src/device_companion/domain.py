import dataclasses
from datetime import datetime
from typing import Callable, Type


@dataclasses.dataclass
class Message:
    string: str
    timestamp: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()

    def serialise(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Command:
    message: Message
    timeout: float = 5.0
    acks: list[Callable[[str], bool]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Response:
    message: Message


@dataclasses.dataclass
class Error:
    message: Message
    exception: Type[Exception] = RuntimeError
