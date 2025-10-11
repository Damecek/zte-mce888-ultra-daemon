from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlsplit


def _normalize_host(host: str) -> str:
    """
    Normalize a router host string into a URL with a scheme and no trailing slash.
    
    Parameters:
        host (str): Host or URL provided by the user. Leading/trailing whitespace is ignored.
    
    Returns:
        str: The normalized host URL. If the input lacked a scheme, `http://` is prepended; the returned string never ends with a `/`.
    
    Raises:
        ValueError: If `host` is empty or contains only whitespace ("Router host must be provided").
    """
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
        """
        Validate the dataclass configuration, normalize the host, and enforce locality constraints after initialization.
        
        Ensures a non-empty `password` and normalizes `self.host` to a URL form without a trailing slash. Also enforces that the configured host, when expressed as an IP address, is on the local network (private or loopback) for this release.
        
        Raises:
            ValueError: If `password` is empty (`"Router password is required"`), or if the host is an IP address that is not private or loopback (`"Router host must be on the local network for this release"`).
        """
        if not self.password:
            raise ValueError("Router password is required")
        self.host = _normalize_host(self.host)
        self._ensure_local_host()

    def _ensure_local_host(self) -> None:
        """
        Validate that the configured host is local when represented as an IP address.
        
        If the parsed hostname is an IP address, ensure it is either private or loopback; allow non-IP hostnames (assumed resolved via local DNS) and do nothing when no hostname is present.
        
        Raises:
            ValueError: If the host is an IP address that is neither private nor loopback.
        """
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