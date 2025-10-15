from __future__ import annotations

from click.testing import CliRunner

from cli.zte import cli
from services import zte_client


class DummyClient:
    def __init__(self, host: str, **_: object) -> None:  # pragma: no cover - simple wiring
        pass

    def login(self, password: str) -> None:  # pragma: no cover - simple wiring
        pass

    def request(self, path: str, method: str, payload=None, expects: str = "json"):
        # Always return a fixed metric value
        return {"lte_rsrp_1": -85}


def test_read_listen_polls_and_exits_on_keyboard_interrupt(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)

    # Cause the loop to exit after the first emission
    call_count = {"n": 0}

    def _sleep(_: float) -> None:
        call_count["n"] += 1
        raise KeyboardInterrupt

    monkeypatch.setattr("cli.commands.read.time.sleep", _sleep)

    result = runner.invoke(
        cli,
        [
            "read",
            "lte.rsrp1",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
            "--listen",
        ],
        catch_exceptions=False,
    )

    # One line printed before KeyboardInterrupt stops the loop
    assert result.exit_code == 0
    out = result.output.strip().splitlines()
    assert any("lte.rsrp1" in line and "-85" in line for line in out)
    # Ensure our sleep patch was actually hit
    assert call_count["n"] == 1
