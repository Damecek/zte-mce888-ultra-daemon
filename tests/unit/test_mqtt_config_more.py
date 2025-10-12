from __future__ import annotations

import pytest

from models.mqtt_config import MQTTConfig


def test_mqtt_config_rejects_empty_host() -> None:
    with pytest.raises(ValueError, match="MQTT host must be provided"):
        MQTTConfig(host="   ")


@pytest.mark.parametrize("value", ["mqtt://localhost", "http://127.0.0.1", "https://broker"])
def test_mqtt_config_rejects_scheme_in_host(value: str) -> None:
    with pytest.raises(ValueError, match="must not include a protocol scheme"):
        MQTTConfig(host=value)


@pytest.mark.parametrize("port", [0, 65536])
def test_mqtt_config_rejects_out_of_range_port(port: int) -> None:
    with pytest.raises(ValueError, match="MQTT port must be in the range 1-65535"):
        MQTTConfig(host="mqtt.local", port=port)


def test_mqtt_config_rejects_nonzero_qos_and_retain_true() -> None:
    with pytest.raises(ValueError, match="MQTT QoS must be 0"):
        MQTTConfig(host="mqtt.local", qos=1)

    with pytest.raises(ValueError, match="MQTT retain flag must be False"):
        MQTTConfig(host="mqtt.local", retain=True)


def test_mqtt_config_root_topic_normalization_and_empty_rejection() -> None:
    # Normalization keeps non-empty segments, trims spaces, lowercases
    cfg = MQTTConfig(host="mqtt.local", root_topic="  Home/ZTE  ")
    assert cfg.root_topic == "home/zte"

    # Empty/whitespace root collapses to empty -> rejected
    with pytest.raises(ValueError, match="MQTT root topic cannot be empty"):
        MQTTConfig(host="mqtt.local", root_topic=" /  / ")


def test_mqtt_config_enforces_local_or_loopback_ip() -> None:
    # Public IP is rejected
    with pytest.raises(ValueError, match="must resolve to a local or loopback address"):
        MQTTConfig(host="8.8.8.8")


def test_mqtt_config_allows_host_with_port_suffix_and_private_ip() -> None:
    # Host with explicit :port should be accepted and preserved
    cfg = MQTTConfig(host="192.168.0.10:1883", root_topic="ZTE")
    assert cfg.host == "192.168.0.10:1883"
    # Root still normalized
    assert cfg.root_topic == "zte"


def test_mqtt_config_allows_hostname_without_ip_validation() -> None:
    # Non-IP hostnames are allowed; _ensure_local_network skips validation
    cfg = MQTTConfig(host="mybroker.local")
    assert cfg.host == "mybroker.local"
    assert cfg.root_topic == "zte"
