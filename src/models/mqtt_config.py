from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address


def _normalize_root(topic: str) -> str:
    """
    Normalize an MQTT root topic string.

    Parameters:
        topic (str): Topic string that may include leading/trailing
            whitespace and '/'-separated segments.

    Returns:
        normalized (str): Lowercased topic with empty segments removed and
            segments joined by '/'.

    Raises:
        ValueError: If the normalized topic is empty.
    """
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
        """
        Perform post-initialization validation and normalization of MQTT
        configuration.

        Strips whitespace from `host`, validates presence and that it does not
        include a protocol scheme, ensures `port` is within 1-65535,
        normalizes `root_topic`, enforces that `qos` equals 0 and `retain` is
        False, and verifies the configured host resolves to a loopback or
        private address when expressed as an IP.

        Raises:
            ValueError: If `host` is empty after trimming.
            ValueError: If `host` contains a protocol scheme (contains "://").
            ValueError: If `port` is not in the range 1-65535.
            ValueError: If `qos` is not 0.
            ValueError: If `retain` is True.
            ValueError: If the host parses to a public (non-private, non-loopback) IP address.
        """
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
        """
        Validate that the configured MQTT host resolves to a local or
        loopback IP address.

        If the configured host is an IP address (a trailing ":port" is
        ignored), it must be a private or loopback address; hostnames are
        accepted but not resolved or validated here.

        Raises:
            ValueError: If the host is an IP address that is neither private nor loopback.
        """
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
