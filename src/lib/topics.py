from __future__ import annotations

from dataclasses import dataclass


def _normalize_segment(segment: str) -> str:
    value = segment.strip()
    if not value:
        raise ValueError("Topic segments must not be empty")
    return value.lower()


def normalize_topic(topic: str) -> str:
    """Normalize an MQTT topic path to lowercase segments."""

    segments = [part for part in topic.replace("\\", "/").split("/") if part.strip()]
    if not segments:
        raise ValueError("Topic cannot be empty")
    return "/".join(_normalize_segment(part) for part in segments)


def build_request_topic(root: str, metric: str) -> str:
    root_norm = normalize_topic(root)
    metric_norm = _normalize_segment(metric)
    return f"{root_norm}/{metric_norm}/get"


def build_response_topic(root: str, metric: str) -> str:
    root_norm = normalize_topic(root)
    # Support nested metric identifiers separated by '.' by mapping them to
    # path segments in the response topic so that a request like
    #   zte/lte/rsrp1/get
    # yields a response published to
    #   zte/lte/rsrp1
    # Single-segment metrics (e.g., 'provider') are preserved as-is.
    metric_path = "/".join(_normalize_segment(part) for part in metric.split("."))
    return f"{root_norm}/{metric_path}"


@dataclass(slots=True)
class ParsedTopic:
    request_topic: str
    root: str
    metric: str
    is_aggregate: bool


def parse_request_topic(topic: str) -> ParsedTopic:
    normalized = normalize_topic(topic)
    parts = normalized.split("/")
    if len(parts) < 3 or parts[-1] != "get":
        raise ValueError(f"Unsupported request topic: {topic}")
    metric = parts[-2]
    root = "/".join(parts[:-2])
    if not root:
        raise ValueError("Request topic must include a root prefix")
    is_aggregate = metric == "lte"
    return ParsedTopic(
        request_topic=normalized,
        root=root,
        metric=metric,
        is_aggregate=is_aggregate,
    )


def parse_request_topic_for_root(topic: str, root: str) -> ParsedTopic:
    """Parse a request topic using a known root prefix.

    Supports nested metric paths (e.g., 'lte/rsrp1') which are converted to
    dot-separated identifiers (e.g., 'lte.rsrp1') to align with the CLI/read
    mapping used throughout the codebase.
    """
    normalized = normalize_topic(topic)
    root_norm = normalize_topic(root)
    parts = normalized.split("/")
    root_parts = root_norm.split("/")

    if len(parts) < 2 or parts[-1] != "get":
        raise ValueError(f"Unsupported request topic: {topic}")

    # Require the topic to start with the expected root prefix
    if parts[: len(root_parts)] != root_parts:
        raise ValueError("Request topic does not match expected root prefix")

    metric_parts = parts[len(root_parts) : -1]
    # If no metric segment is present beyond the configured root, this denotes
    # an aggregate request for the top-level 'zte' group (root includes '/zte').
    if not metric_parts:
        metric_ident = "zte"
    else:
        # Join nested path to a dot-identifier used by metrics map
        metric_ident = ".".join(metric_parts)

    is_aggregate = metric_ident in {"lte", "zte"}

    return ParsedTopic(
        request_topic=normalized,
        root=root_norm,
        metric=metric_ident,
        is_aggregate=is_aggregate,
    )


def response_topic_from_request(topic: str) -> str:
    parsed = parse_request_topic(topic)
    return build_response_topic(parsed.root, parsed.metric)


__all__ = [
    "ParsedTopic",
    "build_request_topic",
    "build_response_topic",
    "normalize_topic",
    "parse_request_topic_for_root",
    "parse_request_topic",
    "response_topic_from_request",
]
