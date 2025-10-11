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
        self.connected = True

    def mark_disconnected(self) -> None:
        self.connected = False

    def record_request(self, topic: str) -> None:
        self.last_seen_request_topic = topic

    def record_publish(self) -> None:
        self.last_publish_time = datetime.now(UTC)
        self.failures = 0

    def record_failure(self) -> None:
        self.failures += 1


__all__ = ["DaemonState"]
