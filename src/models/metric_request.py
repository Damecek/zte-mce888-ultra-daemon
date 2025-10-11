from __future__ import annotations

from dataclasses import dataclass

from lib import topics


@dataclass(slots=True)
class MetricRequest:
    """Represents a normalized MQTT metric request."""

    topic: str
    root: str
    metric: str
    is_aggregate: bool

    @classmethod
    def from_topic(cls, topic: str) -> MetricRequest:
        parsed = topics.parse_request_topic(topic)
        return cls(
            topic=parsed.request_topic,
            root=parsed.root,
            metric=parsed.metric,
            is_aggregate=parsed.is_aggregate,
        )


__all__ = ["MetricRequest"]
