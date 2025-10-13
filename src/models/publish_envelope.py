from __future__ import annotations

from dataclasses import dataclass

from lib import topics


@dataclass(slots=True)
class PublishEnvelope:
    """Container describing an outbound MQTT publish operation."""

    topic: str
    payload: object
    qos: int = 0
    retain: bool = False

    def __post_init__(self) -> None:
        """
        Normalize the topic and enforce publish contract constraints after initialization.
        
        Normalizes the instance's topic and validates that `qos` is equal to 0 and `retain` is False.
        
        Raises:
            ValueError: If `qos` is not 0.
            ValueError: If `retain` is True.
        """
        self.topic = topics.normalize_topic(self.topic)
        if self.qos != 0:
            raise ValueError("Publish QoS must be 0 per contract")
        if self.retain:
            raise ValueError("Publish retain flag must be False per contract")


__all__ = ["PublishEnvelope"]