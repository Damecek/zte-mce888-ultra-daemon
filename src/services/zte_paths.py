from __future__ import annotations

GOFORM_GET = "/goform/goform_get_cmd_process"
GOFORM_SET = "/goform/goform_set_cmd_process"


def build_get_multi_cmd_path(cmds: str) -> str:
    """Build a GET path for multi_data=1 queries to goform_get_cmd_process."""
    return f"{GOFORM_GET}?cmd={cmds}&multi_data=1"


NEIGHBORS_CMD = "ngbr_cell_info"


def neighbors_path() -> str:
    """Return the GET path used to fetch neighbor cell info."""
    return build_get_multi_cmd_path(NEIGHBORS_CMD)


__all__ = [
    "GOFORM_GET",
    "GOFORM_SET",
    "NEIGHBORS_CMD",
    "build_get_multi_cmd_path",
    "neighbors_path",
]
