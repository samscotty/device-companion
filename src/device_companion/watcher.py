from collections import deque
from dataclasses import dataclass
from threading import Event, Thread

from .domain import Command, Error, Message, Response


@dataclass
class WatchedCommand:
    command: Command
    event: Event


class AckWatcher:
    def __init__(self) -> None:
        self._queue: deque[WatchedCommand] = deque()

    def _watch(self, watched: WatchedCommand) -> None:
        if not watched.event.wait(watched.command.timeout):
            self._queue.clear()
            self(Error(Message(f"{watched.command.message.string} not acknowledged"), TimeoutError))

    def __call__(self, communication: Command | Response | Error) -> None:
        if isinstance(communication, Error):
            raise communication.exception(communication.message.string)
        elif isinstance(communication, Command):
            # Do not watch if the command has no acknowledgements
            if not communication.acks:
                return None

            event = Event()
            command = WatchedCommand(communication, event)
            self._queue.append(command)
            thread = Thread(target=self._watch, args=(command,))
            thread.start()
            thread.join()
            return None
        elif not self._queue:
            return None

        # Get the next watched command from the queue
        watched = self._queue.popleft()

        for ack in watched.command.acks:
            if ack(communication.message):
                watched.event.set()
                break
        else:
            # Return to priority in the queue if no matches
            self._queue.appendleft(watched)
