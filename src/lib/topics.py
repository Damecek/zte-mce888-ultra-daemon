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
    metric_norm = _normalize_segment(metric)
    return f"{root_norm}/{metric_norm}"


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


def response_topic_from_request(topic: str) -> str:
    parsed = parse_request_topic(topic)
    return build_response_topic(parsed.root, parsed.metric)


__all__ = [
    "ParsedTopic",
    "build_request_topic",
    "build_response_topic",
    "normalize_topic",
    "parse_request_topic",
    "response_topic_from_request",
]
