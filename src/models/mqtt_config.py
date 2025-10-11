from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address


def _normalize_root(topic: str) -> str:
    segments = [segment.strip() for segment in topic.strip().split("/") if segment.strip()]
    if not segments:
        raise ValueError("MQTT root topic cannot be empty")
    return "/".join(segment.lower() for segment in segments)


@dataclass(slots=True)
class MQTTConfig:
    """Runtime configuration for MQTT connectivity."""

    host: str
    root_topic: str = "zte"
    port: int = 1883
    username: str | None = None
    password: str | None = None
    qos: int = 0
    retain: bool = False
    reconnect_seconds: int = 5

    def __post_init__(self) -> None:
        self.host = self.host.strip()
        if not self.host:
            raise ValueError("MQTT host must be provided")
        if "://" in self.host:
            raise ValueError("MQTT host must not include a protocol scheme (plaintext only)")
        if self.port <= 0 or self.port >= 65536:
            raise ValueError("MQTT port must be in the range 1-65535")
        self.root_topic = _normalize_root(self.root_topic)
        # QoS and retain are part of the contract for this feature; enforce eagerly
        if self.qos != 0:
            raise ValueError("MQTT QoS must be 0 for this daemon")
        if self.retain:
            raise ValueError("MQTT retain flag must be False for this daemon")
        self._ensure_local_network()

    def _ensure_local_network(self) -> None:
        host = self.host
        # Strip potential port suffix if provided as host:port
        if ":" in host:
            host = host.split(":", 1)[0]
        try:
            address = ip_address(host)
        except ValueError:
            # Hostnames are allowed; caller should ensure local resolution.
            return
        if not (address.is_private or address.is_loopback):
            raise ValueError("MQTT host must resolve to a local or loopback address for this release")


__all__ = ["MQTTConfig"]
