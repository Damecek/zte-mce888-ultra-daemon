from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from cli import zte as cli_module
from services import zte_client


def test_discover_relative_target_writes_markdown_and_snapshot(monkeypatch) -> None:
    runner = CliRunner()

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, password: str) -> None:  # pragma: no cover - wiring
            return None

        def request(self, path: str, method: str, payload=None, expects: str = "json"):
            # Return small JSON so it's embedded in Markdown and snapshot
            return {"status": "ok", "list": [1, 2]}

    monkeypatch.setattr(zte_client, "ZTEClient", Client)

    with runner.isolated_filesystem():
        # Use relative path to ensure command resolves it under CWD
        target_rel = Path("docs") / "discover" / "rel-example.md"
        result = runner.invoke(
            cli_module.cli,
            [
                "discover",
                "--router-host",
                "http://192.168.0.1",
                "--router-password",
                "pw",
                "--path",
                "goform/test",
                "--target-file",
                str(target_rel),
            ],
        )

        assert result.exit_code == 0, result.output
        md_path = Path.cwd() / target_rel
        assert md_path.exists()
        md_text = md_path.read_text()
        assert "# Discover Example:" in md_text
        assert '"status": "ok"' in md_text

        # Verify a snapshot JSON was written alongside markdown
        snap_dir = md_path.parent
        snapshots = sorted(snap_dir.glob("*-rel-example.json"))
        assert snapshots, "expected a saved snapshot next to markdown"
        snap = json.loads(snapshots[-1].read_text())
        assert snap["request"]["method"] in {"GET", "POST"}
        assert snap["response"]["status"] == "ok"
