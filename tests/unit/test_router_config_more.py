from __future__ import annotations

import pytest

from models.router_config import RouterConfig


def test_password_required_raises_value_error() -> None:
    """
    RouterConfig requires a non-empty password.
    """
    with pytest.raises(ValueError, match="Router password is required"):
        RouterConfig(password="")


@pytest.mark.parametrize(
    ("raw_host", "expected"),
    [
        ("192.168.1.1", "http://192.168.1.1"),
        ("https://192.168.1.1/", "https://192.168.1.1"),
        ("http://192.168.1.1/", "http://192.168.1.1"),
        (" 192.168.1.1/ ", "http://192.168.1.1"),
    ],
)
def test_host_normalization_adds_scheme_and_strips_trailing_slash(raw_host: str, expected: str) -> None:
    """
    Host is normalized by adding http:// when missing and removing any trailing slash.
    Existing https:// scheme is preserved.
    """
    cfg = RouterConfig(host=raw_host, password="pw")
    assert cfg.host == expected


def test_empty_host_raises_value_error() -> None:
    """
    An empty or whitespace-only host is rejected during normalization.
    """
    with pytest.raises(ValueError, match="Router host must be provided"):
        RouterConfig(host="   ", password="pw")


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "localhost",  # hostname (non-IP) is allowed and normalized to http://
        "192.168.1.5",
        "10.0.0.2",
        "172.16.0.10",
    ],
)
def test_local_network_enforcement_allows_private_and_loopback(host: str) -> None:
    """
    Loopback and RFC1918 private address space hosts are accepted.
    Non-IP hostnames are also permitted (assumed locally resolvable).
    """
    cfg = RouterConfig(host=host, password="pw")
    # Ensure normalization added scheme for bare hosts/hostnames
    assert cfg.host.startswith("http://") or cfg.host.startswith("https://")


@pytest.mark.parametrize("host", ["8.8.8.8", "1.1.1.1"])
def test_public_ip_is_rejected(host: str) -> None:
    """
    Public IP addresses are rejected to enforce local-only operation in this release.
    """
    with pytest.raises(ValueError, match="Router host must be on the local network for this release"):
        RouterConfig(host=host, password="pw")


def test_hostname_without_scheme_is_allowed_and_normalized() -> None:
    """
    Non-IP hostnames are allowed and normalized by prepending http:// and removing trailing slash.
    """
    cfg = RouterConfig(host="myrouter.local/", password="pw")
    assert cfg.host == "http://myrouter.local"
