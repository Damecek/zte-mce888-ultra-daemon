from datetime import UTC, datetime
from unittest.mock import patch

from models.daemon_state import DaemonState


def test_daemon_state_transitions_and_tracking() -> None:
    state = DaemonState()
    assert state.connected is False
    assert state.failures == 0
    assert state.last_seen_request_topic is None
    assert state.last_publish_time is None

    state.mark_connected()
    assert state.connected is True

    state.record_request("zte/provider/get")
    assert state.last_seen_request_topic == "zte/provider/get"

    with patch("models.daemon_state.datetime", autospec=True) as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        state.record_publish()

    assert state.last_publish_time == datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert state.failures == 0

    state.record_failure()
    state.record_failure()
    assert state.failures == 2

    state.mark_disconnected()
    assert state.connected is False
