from __future__ import annotations

import pytest
from click.testing import CliRunner

from cli.zte import cli
from services import zte_client


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_read_command_returns_metric_value(runner: CliRunner, monkeypatch) -> None:
    class DummyClient:
        def __init__(self, host: str, **_: object) -> None:
            pass

        def login(self, password: str) -> None:
            pass

        def request(self, path: str, method: str, payload=None, expects: str = "json"):
            return {"lte_rsrp_1": -85}

    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)
    result = runner.invoke(
        cli,
        [
            "read",
            "lte.rsrp1",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    output = result.output
    assert "lte.rsrp1" in output
    assert "-85" in output
    assert "Telekom" not in output  # ensure metric-specific


def test_read_command_rejects_unknown_metric(runner: CliRunner, monkeypatch) -> None:
    class DummyClient:
        def __init__(self, host: str, **_: object) -> None:
            pass

        def login(self, password: str) -> None:
            pass

        def request(self, path: str, method: str, payload=None, expects: str = "json"):
            return {}

    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)
    result = runner.invoke(
        cli,
        [
            "read",
            "foo.bar",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Unknown metric identifier" in result.output
