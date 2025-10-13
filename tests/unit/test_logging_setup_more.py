from __future__ import annotations

import logging
from pathlib import Path

import pytest

from lib import logging_setup


def test_structured_formatter_appends_error_summary(capsys: pytest.CaptureFixture[str]) -> None:
    """
    Ensure StructuredFormatter includes a concise error summary when exc_info is present.
    """
    logger = logging_setup.get_logger("error")
    # Emit an exception and ensure the formatter appends a single-line error summary.
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("During operation")

    # Flush handlers to ensure output is written
    for h in list(logger.handlers):
        try:
            h.flush()  # type: ignore[attr-defined]
        except Exception:
            pass

    out = capsys.readouterr().err
    # Expect pattern: "<ts> ERROR zte_daemon: During operation | error=ValueError: boom"
    assert "During operation" in out
    assert "error=ValueError: boom" in out


def test_get_logger_sets_external_loggers_and_root_level() -> None:
    """
    Verify get_logger() configures external loggers and root logger according to the chosen level,
    and that the app logger does not propagate.
    """
    logger = logging_setup.get_logger("info")
    assert logger.propagate is False

    # External libraries are leveled and set to propagate to root
    for name in ("httpx", "httpcore", "urllib3"):
        ext = logging.getLogger(name)
        assert ext.level == logging.INFO
        assert ext.propagate is True

    # Root logger aligned to the chosen app level
    root = logging.getLogger()
    assert root.level == logging.INFO


def test_get_logger_with_file_handler_writes_to_disk(tmp_path: Path) -> None:
    """
    When a log_file path is provided, get_logger() creates the parent directory and writes to the file.
    """
    log_dir = tmp_path / "nested" / "logs"
    log_file = log_dir / "app.log"
    logger = logging_setup.get_logger("info", log_file=log_file)

    # Emit a log line and ensure it lands in the file handler
    message = "Hello file logs"
    logger.info(message)

    # Flush handlers to ensure content is written
    for h in list(logger.handlers):
        try:
            h.flush()  # type: ignore[attr-defined]
        except Exception:
            pass

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert message in content


def test_configure_is_idempotent() -> None:
    """
    Calling configure() multiple times should short-circuit on subsequent calls.
    This drives the early-return branch.
    """
    # First call applies basicConfig
    logging_setup.configure()
    # Second call should be a no-op and must not raise
    logging_setup.configure()
