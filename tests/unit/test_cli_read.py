from __future__ import annotations

import click
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
        # Allow Click to capture exceptions so we can assert wrapping behavior
        catch_exceptions=True,
    )
    # Expect ClickException wrapping the underlying KeyError from metric resolution
    assert result.exit_code != 0
    assert isinstance(result.exception, click.ClickException) or isinstance(result.exception, Exception)
    # When wrapped, __cause__ should hold the original KeyError
    if isinstance(result.exception, click.ClickException):
        assert isinstance(result.exception.__cause__, KeyError)
        assert str(result.exception.__cause__) in {"'foo.bar'", "foo.bar"}
    else:
        # Fallback assertion if Click surfaces the underlying error directly
        assert isinstance(result.exception, KeyError)
        assert str(result.exception) in {"'foo.bar'", "foo.bar"}
