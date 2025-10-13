from __future__ import annotations

import asyncio
import logging
import random
import string
from collections.abc import Awaitable, Callable

from gmqtt import Client as GMQTTClient

from models.mqtt_config import MQTTConfig
from models.publish_envelope import PublishEnvelope

MessageHandler = Callable[[str, bytes | None], Awaitable[None] | None]


def _random_client_id() -> str:
    """
    Generate a random MQTT client identifier following the module's naming
    convention.

    Returns:
        str: Client identifier in the form "zte-daemon-<suffix>" where
            <suffix> is six characters chosen from lowercase letters and
            digits.
    """
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
        """
        Initialize the MQTTClient with configuration, event loop, and
        underlying GMQTT client.

        Parameters:
            config (MQTTConfig): MQTT connection and topic configuration used
                by this client.
            loop (asyncio.AbstractEventLoop | None): Optional asyncio event
                loop to use; the current loop is used if omitted.
            client (GMQTTClient | None): Optional preconfigured GMQTT client.
                If omitted, a new GMQTTClient with a random client_id is
                created.

        Description:
            Sets up internal asyncio events for connection state, a message
            handler placeholder, and binds GMQTT callbacks for connect,
            message, and disconnect handling.
        """
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
        """
        Register the asynchronous handler to process incoming MQTT messages.

        Parameters:
            handler (MessageHandler): Async callable invoked with two
                arguments `(topic, payload)` for each received message.
        """
        self._handler = handler

    async def connect(self) -> None:
        """
        Initiate a connection to the configured MQTT broker and wait until
        the client is connected.

        Uses the instance configuration (host, port, username, password) and
        clears prior disconnect state before starting the connection process.
        """
        self._logger.info(
            "Connecting to MQTT broker: "
            f"host={self._config.host} "
            f"port={self._config.port} "
            f"root={self._config.root_topic}"
        )
        self._disconnect_event.clear()
        # gmqtt does not accept username/password in connect(); set explicitly
        if self._config.username is not None:
            # Empty password is allowed; gmqtt handles None/empty internally
            self._client.set_auth_credentials(self._config.username, self._config.password or "")
        await self._client.connect(
            self._config.host,
            port=self._config.port,
            keepalive=60,
        )
        await self._connected_event.wait()

    async def disconnect(self) -> None:
        """
        Request the underlying GMQTT client to disconnect and wait until the disconnect completes.
        """
        await self._client.disconnect()

    async def wait_for_disconnect(self) -> None:
        """
        Block until the MQTT client signals it has disconnected.

        Awaits the internal disconnect event which is set when the client's disconnect handler runs.
        """
        await self._disconnect_event.wait()

    def publish(self, envelope: PublishEnvelope) -> None:
        """
        Publish a prepared MQTT envelope to its topic.

        Parameters:
            envelope (PublishEnvelope): Message envelope containing `topic`,
                `payload`, `qos`, and `retain` flags used for publication.
        """
        self._logger.debug(
            f"Publishing MQTT message: topic={envelope.topic} qos={envelope.qos} retain={envelope.retain}"
        )
        self._client.publish(envelope.topic, envelope.payload, qos=envelope.qos, retain=envelope.retain)

    # gmqtt callbacks -----------------------------------------------------------------
    def _on_connect(self, client: GMQTTClient, flags: dict[str, int], rc: int, properties: object | None) -> None:
        """
        Handle client connect event by subscribing to the configured request
        topics and marking the client as connected.

        Parameters:
            client (GMQTTClient): GMQTT client instance (ignored).
            flags (dict[str, int]): Connection flags provided by the broker (ignored).
            rc (int): Connection return code (ignored).
            properties (object | None): Optional connection properties (ignored).
        """
        del client, flags, rc, properties
        root = self._config.root_topic
        # Subscribe to all request topics under the configured root. We'll
        # filter to only '/get' messages in the dispatcher.
        request_pattern = f"{root}/#"
        self._client.subscribe(request_pattern, qos=self._config.qos)
        self._logger.info(f"Subscribed to MQTT request topics: pattern={request_pattern}")
        self._connected_event.set()

    def _on_disconnect(self, client: GMQTTClient, packet: object, exc: Exception | None = None) -> None:
        """
        Handle an MQTT client disconnection and update internal connection state.

        Logs a warning including exception info if `exc` is provided;
        otherwise logs a normal disconnect. Clears the internal connected
        event and sets the internal disconnect event to signal other tasks.

        Parameters:
            exc (Exception | None): The exception that caused the disconnect,
                if any.
        """
        del client, packet
        if exc:
            self._logger.warning("MQTT client disconnected", exc_info=exc)
        else:
            self._logger.info("MQTT client disconnected")
        self._connected_event.clear()
        self._disconnect_event.set()

    def _on_message(self, client: GMQTTClient, topic: str, payload: bytes, qos: int, properties: object) -> None:
        """
        Handle an incoming MQTT message by delegating it to the registered message handler.

        If no handler is registered the message is ignored. If the handler
        returns a coroutine it is scheduled as an asyncio task. Exceptions
        raised by the handler are caught and logged.

        Parameters:
            client (GMQTTClient): The MQTT client that received the message.
            topic (str): Topic the message was published to.
            payload (bytes): Message payload.
            qos (int): Message quality-of-service level.
            properties (object): MQTT message properties.
        """
        del client, qos, properties
        self._logger.debug(f"Received MQTT message: topic={topic}")
        if not self._handler:
            return
        try:
            maybe_awaitable = self._handler(topic, payload)
            if asyncio.iscoroutine(maybe_awaitable):
                asyncio.create_task(maybe_awaitable)
        except Exception:  # pragma: no cover - defensive logging
            self._logger.exception("Error handling MQTT message")


__all__ = ["MQTTClient"]
