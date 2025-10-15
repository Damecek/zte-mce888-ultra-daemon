from __future__ import annotations

import asyncio
import signal
from collections.abc import Callable
from typing import Any

import pytest

from cli.commands import run as run_module


@pytest.fixture()
def anyio_backend():
    # Constrain anyio to use asyncio backend to avoid trio dependency
    return "asyncio"


class FakeZTEClient:
    def __init__(self, host: str) -> None:
        self.host = host
        self.logged_in_with: str | None = None
        self.closed = False

    def login(self, password: str) -> None:
        self.logged_in_with = password

    def close(self) -> None:
        self.closed = True


class FakeDispatcher:
    def __init__(self, **_: Any) -> None:
        self.requests: list[tuple[str, bytes | None]] = []

    def handle_request(self, topic: str, payload: bytes | None) -> None:
        self.requests.append((topic, payload))


class FakeMQTTClient:
    def __init__(self, config: Any) -> None:
        # Store config to assert root topic normalization/derivation.
        self.config = config
        self._handler: Callable[[str, bytes | None], Any] | None = None
        self.connect_calls = 0
        self.disconnect_calls = 0
        self._disconnect_event = asyncio.Event()

    def set_message_handler(self, handler: Callable[[str, bytes | None], Any]) -> None:
        self._handler = handler

    async def connect(self) -> None:
        self.connect_calls += 1

    async def disconnect(self) -> None:
        self.disconnect_calls += 1
        self._disconnect_event.set()

    async def wait_for_disconnect(self) -> None:
        await self._disconnect_event.wait()

    # Test helper to simulate incoming message
    def emit(self, topic: str, payload: bytes | None = None) -> None:
        if self._handler:
            self._handler(topic, payload)


class FakeLoop:
    def __init__(self) -> None:
        self.handlers: dict[int, Callable[[], None]] = {}

    def add_signal_handler(self, signum: int, callback: Callable[[], None]) -> None:
        self.handlers[signum] = callback


@pytest.mark.anyio
async def test_run_daemon_connects_handles_message_and_stops_on_sigint(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Drive _run_daemon through a normal connect cycle, simulate one incoming message via the MQTT handler,
    and then trigger SIGINT to request a graceful shutdown. All network I/O is mocked.
    """
    # Capture created fakes for assertions
    created: dict[str, Any] = {}

    # Patch ZTEClient constructor used by the run module
    def fake_zte_client_ctor(host: str) -> FakeZTEClient:
        created["client"] = FakeZTEClient(host)
        return created["client"]

    # Patch MQTTClient factory to return our fake and capture it
    def fake_mqtt_client_ctor(config: Any) -> FakeMQTTClient:
        fake = FakeMQTTClient(config)
        created["mqtt"] = fake
        return fake

    # Patch Dispatcher to our fake
    def fake_dispatcher_ctor(**kwargs: Any) -> FakeDispatcher:
        fake = FakeDispatcher(**kwargs)
        created["dispatcher"] = fake
        return fake

    # Replace imported symbols within the run module
    monkeypatch.setattr(run_module, "MQTTClient", fake_mqtt_client_ctor)
    monkeypatch.setattr(run_module, "Dispatcher", fake_dispatcher_ctor)
    monkeypatch.setattr(run_module.zte_client, "ZTEClient", fake_zte_client_ctor)

    # Provide a fake loop to capture the signal handler callback
    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    # Kick off the daemon in the background
    task = asyncio.create_task(
        run_module._run_daemon(
            router_host="http://192.168.0.1",
            router_password="pw",
            log_level="error",
            log_file=None,
            mqtt_host="mqtt.local",
            mqtt_port=1883,
            mqtt_username=None,
            mqtt_password=None,
            mqtt_topic="home",  # ensure effective root becomes 'home/zte'
            foreground=True,
        )
    )

    # Allow the task to run up to the wait() on stop/disconnect
    await asyncio.sleep(0)

    # Assert that construction/login happened
    assert isinstance(created.get("client"), FakeZTEClient)
    assert created["client"].host == "http://192.168.0.1"
    assert created["client"].logged_in_with == "pw"

    # Assert MQTT client was constructed with an effective root 'home/zte'
    assert isinstance(created.get("mqtt"), FakeMQTTClient)
    assert created["mqtt"].config.root_topic == "home/zte"
    assert created["mqtt"].connect_calls == 1

    # Simulate an incoming message; should delegate to Dispatcher.handle_request
    created["mqtt"].emit("home/zte/lte/get", b"{}")
    assert created["dispatcher"].requests == [("home/zte/lte/get", b"{}")]

    # Invoke the registered SIGINT handler to request stop
    assert signal.SIGINT in loop.handlers
    loop.handlers[signal.SIGINT]()  # sets the stop_event

    # Await completion and ensure disconnect happened and client was closed
    await asyncio.wait_for(task, timeout=1.0)
    assert created["mqtt"].disconnect_calls >= 1
    assert created["client"].closed is True


@pytest.mark.anyio
async def test_run_daemon_registers_both_signals_and_stops_on_sigterm(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure both SIGINT and SIGTERM are registered and triggering SIGTERM also causes a graceful exit.
    """
    created: dict[str, Any] = {}

    def fake_zte_client_ctor(host: str) -> FakeZTEClient:
        created["client"] = FakeZTEClient(host)
        return created["client"]

    def fake_mqtt_client_ctor(config: Any) -> FakeMQTTClient:
        fake = FakeMQTTClient(config)
        created["mqtt"] = fake
        return fake

    def fake_dispatcher_ctor(**kwargs: Any) -> FakeDispatcher:
        fake = FakeDispatcher(**kwargs)
        created["dispatcher"] = fake
        return fake

    monkeypatch.setattr(run_module, "MQTTClient", fake_mqtt_client_ctor)
    monkeypatch.setattr(run_module, "Dispatcher", fake_dispatcher_ctor)
    monkeypatch.setattr(run_module.zte_client, "ZTEClient", fake_zte_client_ctor)

    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    task = asyncio.create_task(
        run_module._run_daemon(
            router_host="http://192.168.0.1",
            router_password="pw",
            log_level="error",
            log_file=None,
            mqtt_host="localhost",
            mqtt_port=1883,
            mqtt_username=None,
            mqtt_password=None,
            mqtt_topic=None,  # default to 'zte'
            foreground=True,
        )
    )

    await asyncio.sleep(0)

    # Verify both signals registered
    assert signal.SIGINT in loop.handlers
    assert signal.SIGTERM in loop.handlers

    # Signal termination using SIGTERM and await shutdown
    loop.handlers[signal.SIGTERM]()
    await asyncio.wait_for(task, timeout=1.0)

    # Asserts: MQTT disconnect and client close performed
    assert created["mqtt"].disconnect_calls >= 1
    assert created["client"].closed is True
