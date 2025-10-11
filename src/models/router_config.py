from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit


def _normalize_host(host: str) -> str:
    value = host.strip()
    if not value:
        raise ValueError("Router host must be provided")
    if not value.startswith("http://") and not value.startswith("https://"):
        value = f"http://{value}"
    return value.rstrip("/")


@dataclass(slots=True)
class RouterConfig:
    """Configuration for the ZTE router REST client."""

    password: str
    host: str = "http://192.168.0.1"

    def __post_init__(self) -> None:
        if not self.password:
            raise ValueError("Router password is required")
        self.host = _normalize_host(self.host)
        self._ensure_local_host()

    def _ensure_local_host(self) -> None:
        parsed = urlsplit(self.host)
        hostname = parsed.hostname
        if not hostname:
            return
        try:
            address = ip_address(hostname)
        except ValueError:
            # Hostnames are allowed; assume local DNS resolution.
            return
        if not (address.is_private or address.is_loopback):
            raise ValueError("Router host must be on the local network for this release")


__all__ = ["RouterConfig"]
