from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class DaemonState:
    """Tracks daemon connectivity, last request, and publish history."""

    connected: bool = False
    last_seen_request_topic: str | None = None
    last_publish_time: datetime | None = None
    failures: int = 0

    def mark_connected(self) -> None:
        """
        Mark the daemon as connected.
        """
        self.connected = True

    def mark_disconnected(self) -> None:
        """
        Mark the daemon as disconnected by setting its connectivity state to False.
        """
        self.connected = False

    def record_request(self, topic: str) -> None:
        """
        Record the topic of the most recent request.

        Parameters:
            topic (str): Topic string to store as the last seen request.
        """
        self.last_seen_request_topic = topic

    def record_publish(self) -> None:
        """
        Record a successful publish by updating the last publish timestamp and resetting the failure count.

        Sets the instance's last_publish_time to the current UTC time and sets failures to 0.
        """
        self.last_publish_time = datetime.now(UTC)
        self.failures = 0

    def record_failure(self) -> None:
        """
        Increment the object's failure count by one.

        This records a failed operation (such as a failed publish) by increasing the `failures` counter.
        """
        self.failures += 1


__all__ = ["DaemonState"]
