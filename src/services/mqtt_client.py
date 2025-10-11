from __future__ import annotations

import asyncio
import logging
import random
import string
from collections.abc import Awaitable, Callable

from gmqtt import Client as GMQTTClient

from lib import topics
from models.mqtt_config import MQTTConfig
from models.publish_envelope import PublishEnvelope

MessageHandler = Callable[[str, bytes | None], Awaitable[None] | None]


def _random_client_id() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"zte-daemon-{suffix}"


class MQTTClient:
    """Async wrapper around gmqtt with contract-specific defaults."""

    def __init__(
        self,
        config: MQTTConfig,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        client: GMQTTClient | None = None,
    ) -> None:
        self._config = config
        self._loop = loop or asyncio.get_event_loop()
        self._client = client or GMQTTClient(client_id=_random_client_id())
        self._logger = logging.getLogger("zte_daemon.mqtt_client")
        self._handler: MessageHandler | None = None
        self._connected_event = asyncio.Event()
        self._disconnect_event = asyncio.Event()

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def set_message_handler(self, handler: MessageHandler) -> None:
        self._handler = handler

    async def connect(self) -> None:
        self._logger.info(
            "Connecting to MQTT broker",
            extra={"host": self._config.host, "port": self._config.port, "root": self._config.root_topic},
        )
        self._disconnect_event.clear()
        await self._client.connect(
            self._config.host,
            port=self._config.port,
            keepalive=None,
            username=self._config.username,
            password=self._config.password,
        )
        await self._connected_event.wait()

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def wait_for_disconnect(self) -> None:
        await self._disconnect_event.wait()

    def publish(self, envelope: PublishEnvelope) -> None:
        self._logger.debug(
            "Publishing MQTT message",
            extra={"topic": envelope.topic, "qos": envelope.qos, "retain": envelope.retain},
        )
        self._client.publish(envelope.topic, envelope.payload, qos=envelope.qos, retain=envelope.retain)

    # gmqtt callbacks -----------------------------------------------------------------
    def _on_connect(self, client: GMQTTClient, flags: dict[str, int], rc: int, properties: object | None) -> None:
        del client, flags, rc, properties
        root = self._config.root_topic
        request_pattern = topics.build_request_topic(root, "+")
        lte_topic = topics.build_request_topic(root, "lte")
        self._client.subscribe(request_pattern, qos=self._config.qos)
        self._client.subscribe(lte_topic, qos=self._config.qos)
        self._logger.info("Subscribed to MQTT request topics", extra={"pattern": request_pattern})
        self._connected_event.set()

    def _on_disconnect(self, client: GMQTTClient, packet: object, exc: Exception | None = None) -> None:
        del client, packet
        if exc:
            self._logger.warning("MQTT client disconnected", exc_info=exc)
        else:
            self._logger.info("MQTT client disconnected")
        self._connected_event.clear()
        self._disconnect_event.set()

    def _on_message(self, client: GMQTTClient, topic: str, payload: bytes, qos: int, properties: object) -> None:
        del client, qos, properties
        self._logger.debug("Received MQTT message", extra={"topic": topic})
        if not self._handler:
            return
        try:
            maybe_awaitable = self._handler(topic, payload)
            if asyncio.iscoroutine(maybe_awaitable):
                asyncio.create_task(maybe_awaitable)
        except Exception:  # pragma: no cover - defensive logging
            self._logger.exception("Error handling MQTT message")


__all__ = ["MQTTClient"]
