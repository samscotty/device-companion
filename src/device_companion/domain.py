import dataclasses
from abc import ABC
from datetime import datetime
from typing import Callable, Type


@dataclasses.dataclass
class Communication(ABC):
    timestamp: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()


@dataclasses.dataclass
class Command(Communication):
    string: str
    timeout: float = 5.0
    acks: list[Callable[[str], bool]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Response(Communication):
    string: str


@dataclasses.dataclass
class Error(Communication):
    string: str
    exception: Type[Exception] = RuntimeError
