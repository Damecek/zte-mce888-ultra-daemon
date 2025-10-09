from __future__ import annotations

import json

from click.testing import CliRunner

from cli.zte import cli
from services import zte_client


class DummyClient:
    def __init__(self, host: str, **_: object) -> None:  # pragma: no cover - simple wiring
        pass

    def login(self, password: str) -> None:  # pragma: no cover - simple wiring
        pass

    def request(self, path: str, method: str, payload=None, expects: str = "json"):
        # Provide ngbr_cell_info in semicolon-separated format: freq,pci,rsrq,rsrp,rssi
        return {"ngbr_cell_info": "1800,123,5,-95,-60;3500,456,8,-105,-70"}


def test_read_neighbors_root_lists_array(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)
    result = runner.invoke(
        cli,
        [
            "read",
            "neighbors",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list) and len(data) == 2
    assert set(data[0].keys()) == {"id", "rsrp", "rsrq", "freq", "rssi"}


def test_read_neighbors_index_and_field(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)

    # Index only -> prints JSON object
    result_obj = runner.invoke(
        cli,
        [
            "read",
            "neighbors[1]",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
        ],
        catch_exceptions=False,
    )
    assert result_obj.exit_code == 0
    obj = json.loads(result_obj.output)
    assert obj["id"] == 456 and obj["rsrp"] == -105

    # Field selector -> prints scalar value
    result_field = runner.invoke(
        cli,
        [
            "read",
            "neighbors[0].id",
            "--router-host",
            "192.168.0.1",
            "--router-password",
            "pw",
        ],
        catch_exceptions=False,
    )
    assert result_field.exit_code == 0
    assert result_field.output.strip() == "123"


def test_read_neighbors_selector_errors(monkeypatch) -> None:
    runner = CliRunner()
    monkeypatch.setattr(zte_client, "ZTEClient", DummyClient)

    # Out of range index
    res_oob = runner.invoke(
        cli,
        ["read", "neighbors[5]", "--router-host", "x", "--router-password", "pw"],
        catch_exceptions=False,
    )
    assert res_oob.exit_code != 0
    assert "out of range" in res_oob.output.lower()

    # Unknown field
    res_field = runner.invoke(
        cli,
        ["read", "neighbors[0].foo", "--router-host", "x", "--router-password", "pw"],
        catch_exceptions=False,
    )
    assert res_field.exit_code != 0
    assert "unknown neighbor field" in res_field.output.lower()

    # Unsupported selector pattern
    res_sel = runner.invoke(
        cli,
        ["read", "neighbors.foo", "--router-host", "x", "--router-password", "pw"],
        catch_exceptions=False,
    )
    assert res_sel.exit_code != 0
    assert "unsupported neighbors selector" in res_sel.output.lower()
