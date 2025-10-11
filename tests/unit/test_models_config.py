from models.mqtt_config import MQTTConfig
from models.router_config import RouterConfig


def test_mqtt_config_defaults_and_lowercase_root() -> None:
    config = MQTTConfig(host="mqtt.local")

    assert config.root_topic == "zte"
    assert config.host == "mqtt.local"
    assert config.port == 1883
    assert config.qos == 0
    assert config.retain is False
    assert config.reconnect_seconds == 5

    custom = MQTTConfig(host="broker", root_topic="ZTE/Home")
    assert custom.root_topic == "zte/home"


def test_router_config_normalizes_host() -> None:
    config = RouterConfig(password="secret")
    assert config.host == "http://192.168.0.1"

    custom = RouterConfig(host="https://192.168.1.1/", password="pw")
    assert custom.host == "https://192.168.1.1"
