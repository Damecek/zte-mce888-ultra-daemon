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

    @classmethod
    def from_topic_for_root(cls, topic: str, root: str) -> MetricRequest:
        """Parse a topic using an expected root and support nested metrics.

        This aligns MQTT topic -> metric translation with the `zte read` command
        identifiers, e.g. 'lte/rsrp1' -> 'lte.rsrp1'.
        """
        parsed = topics.parse_request_topic_for_root(topic, root)
        return cls(
            topic=parsed.request_topic,
            root=parsed.root,
            metric=parsed.metric,
            is_aggregate=parsed.is_aggregate,
        )


__all__ = ["MetricRequest"]
