import dataclasses
from collections import deque
from threading import Event, Thread

from .communication import Command, Error, Message, Response


@dataclasses.dataclass
class WatchedCommand:
    command: Command
    event: Event = dataclasses.field(default_factory=Event, init=False)

    def seen(self) -> bool:
        """Check if an acknowledgement has been received before the timeout."""
        return self.event.wait(self.command.ack.timeout)

    def acknowledge(self) -> None:
        """Acknowledge watched command."""
        self.event.set()


class AckWatcher:

    """Watch for device acknowledgements.

    Waits for a device to inform of the state of a previously received message.
    If ACKs have been specified for a command and none were received in the
    expected interval, a timeout error is raised.

    """

    def __init__(self) -> None:
        self._queue: deque[WatchedCommand] = deque()

    def _watch(self, watched: WatchedCommand) -> None:
        if watched.seen():
            return None

        self._queue.clear()
        self(Error(Message(f"{watched.command.message.payload} not acknowledged"), TimeoutError))

    def __call__(self, communication: Command | Response | Error) -> None:
        if isinstance(communication, Error):
            raise communication.exception(communication.message.payload)
        elif isinstance(communication, Command):
            # Do not watch if the command has no acknowledgements
            if not communication.ack:
                return None

            watched = WatchedCommand(communication)
            self._queue.append(watched)
            thread = Thread(target=self._watch, args=(watched,))
            thread.start()
            thread.join()
            return None
        elif not self._queue:
            return None

        # Get the next watched command from the queue
        watched = self._queue.popleft()

        for matcher in watched.command.ack.matchers:
            if matcher(communication):
                watched.acknowledge()
                break
        else:
            # Return to priority in the queue if no matches
            self._queue.appendleft(watched)
