from __future__ import annotations

import asyncio
from typing import Any

import pytest

from models.mqtt_config import MQTTConfig
from models.publish_envelope import PublishEnvelope
from services.mqtt_client import MQTTClient


class FakeGMQTTClient:
    """
    Minimal fake for gmqtt.Client used to unit test MQTTClient behavior without network I/O.
    """

    def __init__(self) -> None:
        self.on_connect = None
        self.on_message = None
        self.on_disconnect = None

        self.auth: tuple[str | None, str | None] | None = None
        self.connect_calls: list[tuple[str, int, int]] = []
        self.disconnect_calls = 0
        self.subscriptions: list[tuple[str, int]] = []
        self.published: list[tuple[str, Any, int, bool]] = []

    def set_auth_credentials(self, username: str, password: str) -> None:
        self.auth = (username, password)

    async def connect(self, host: str, *, port: int, keepalive: int) -> None:
        self.connect_calls.append((host, port, keepalive))
        # Simulate immediate successful connection
        if self.on_connect:
            self.on_connect(self, {}, 0, None)

    async def disconnect(self) -> None:
        self.disconnect_calls += 1
        # Simulate immediate disconnect event
        if self.on_disconnect:
            self.on_disconnect(self, None, None)

    def subscribe(self, topic: str, qos: int) -> None:
        self.subscriptions.append((topic, qos))

    def publish(self, topic: str, payload: Any, qos: int, retain: bool) -> None:
        self.published.append((topic, payload, qos, retain))


def test_mqtt_client_connect_auth_and_subscribe() -> None:
    """
    Verify that MQTTClient.connect() sets auth when username is provided, awaits connection,
    and subscribes to '<root>/#' on connect.
    """

    async def scenario() -> None:
        cfg = MQTTConfig(
            host="broker",
            root_topic="Home/ZTE",
            port=1884,
            username="alice",
            password="pw",
        )
        fake = FakeGMQTTClient()
        client = MQTTClient(cfg, client=fake)

        await client.connect()

        # Auth credentials forwarded
        assert fake.auth == ("alice", "pw")
        # Connect invoked with expected params
        assert fake.connect_calls == [("broker", 1884, 60)]
        # Subscribe to normalized '<root>/#' with qos=0
        assert fake.subscriptions == [("home/zte/#", 0)]

        # wait_for_disconnect should block until disconnect event; verify it completes after disconnect()
        waiter = asyncio.create_task(client.wait_for_disconnect())
        # Let the loop spin briefly
        await asyncio.sleep(0)
        # Trigger disconnect and ensure waiter completes
        await client.disconnect()
        await asyncio.wait_for(waiter, timeout=0.5)

    asyncio.run(scenario())


def test_mqtt_client_publish_forwards_envelope() -> None:
    """
    Verify that MQTTClient.publish() forwards topic, payload, qos, and retain flags to the underlying client.
    Ensure an event loop exists for MQTTClient construction in a synchronous test.
    """
    cfg = MQTTConfig(host="broker")
    fake = FakeGMQTTClient()
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        client = MQTTClient(cfg, client=fake, loop=loop)

        envelope = PublishEnvelope(topic="telemetry/metric", payload={"v": 1})
        client.publish(envelope)
    finally:
        asyncio.set_event_loop(None)
        loop.close()

    assert fake.published == [("telemetry/metric", {"v": 1}, 0, False)]


def test_on_message_schedules_coroutine_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify that when the registered message handler returns a coroutine, MQTTClient schedules it
    via asyncio.create_task.
    """
    called: list[tuple[str, bytes | None]] = []
    scheduled: list[asyncio.Task[Any]] = []

    def fake_create_task(coro: Any) -> asyncio.Task[Any]:
        # Schedule the coroutine on the current running loop so we can await it
        task = asyncio.get_running_loop().create_task(coro)
        scheduled.append(task)
        return task

    monkeypatch.setattr(asyncio, "create_task", fake_create_task)

    async def scenario() -> None:
        cfg = MQTTConfig(host="broker")
        fake = FakeGMQTTClient()
        client = MQTTClient(cfg, client=fake)

        async def handler(topic: str, payload: bytes | None) -> None:
            # Simulate lightweight async processing
            await asyncio.sleep(0)
            called.append((topic, payload))

        client.set_message_handler(handler)

        # Simulate incoming message via gmqtt callback -> should schedule handler coroutine
        client._on_message(fake, "home/zte/lte/get", b"{}", 0, None)

        assert scheduled, "expected a task to be scheduled for the coroutine handler"
        # Let the scheduled task complete
        await asyncio.gather(*scheduled)

        assert called == [("home/zte/lte/get", b"{}")]

    asyncio.run(scenario())
