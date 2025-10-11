from __future__ import annotations

from dataclasses import dataclass


def _normalize_segment(segment: str) -> str:
    """
    Normalize a single topic segment by trimming surrounding whitespace and converting it to lowercase.
    
    Parameters:
        segment (str): The topic segment to normalize.
    
    Returns:
        str: The normalized segment in lowercase.
    
    Raises:
        ValueError: If the segment is empty or contains only whitespace.
    """
    value = segment.strip()
    if not value:
        raise ValueError("Topic segments must not be empty")
    return value.lower()


def normalize_topic(topic: str) -> str:
    """
    Canonicalize an MQTT-like topic into lowercase, slash-separated, non-empty segments.
    
    Parameters:
        topic (str): Topic string; backslashes are treated as slashes, segments separated by '/' (or '\'), and segments containing only whitespace are ignored.
    
    Returns:
        str: Normalized topic where each segment is lowercased and segments are joined by a single '/'.
    
    Raises:
        ValueError: If no segments remain after normalization (message: "Topic cannot be empty").
    """

    segments = [part for part in topic.replace("\\", "/").split("/") if part.strip()]
    if not segments:
        raise ValueError("Topic cannot be empty")
    return "/".join(_normalize_segment(part) for part in segments)


def build_request_topic(root: str, metric: str) -> str:
    """
    Builds a request topic by joining a normalized root and metric with a trailing "get" segment.
    
    Parameters:
        root (str): Root topic prefix to normalize into slash-separated, lowercase segments.
        metric (str): Metric segment to normalize (lowercased, must be non-empty).
    
    Returns:
        request_topic (str): A normalized request topic string in the form "<root>/<metric>/get".
    """
    root_norm = normalize_topic(root)
    metric_norm = _normalize_segment(metric)
    return f"{root_norm}/{metric_norm}/get"


def build_response_topic(root: str, metric: str) -> str:
    """
    Constructs a normalized response topic from a root prefix and a metric segment.
    
    Parameters:
        root (str): Topic root to normalize into slash-separated, lowercase segments.
        metric (str): Single topic segment to normalize (must be non-empty after trimming).
    
    Returns:
        str: The response topic in the form "<normalized_root>/<normalized_metric>".
    
    Raises:
        ValueError: If `root` is empty or contains no valid segments, or if `metric` is empty after normalization.
    """
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
    """
    Parse a request topic into its normalized components and validate its structure.
    
    The input topic is normalized before parsing; the function extracts the root prefix, the metric name,
    and whether the metric represents an aggregate (`"lte"`). The returned `ParsedTopic.request_topic`
    contains the normalized topic.
    
    Parameters:
    	topic (str): The request topic to parse.
    
    Returns:
    	ParsedTopic: Container with fields:
    		- request_topic: normalized topic string
    		- root: slash-separated root prefix (one or more segments)
    		- metric: metric segment immediately before the trailing "get"
    		- is_aggregate: `true` if `metric` equals `"lte"`, `false` otherwise
    
    Raises:
    	ValueError: If the topic does not end with `/get` or has fewer than three segments.
    	ValueError: If the parsed root prefix is empty.
    """
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
    """
    Derive the corresponding response topic for a given request topic.
    
    Parameters:
        topic (str): The request topic to parse and convert.
    
    Returns:
        str: The normalized response topic corresponding to the request.
    
    Raises:
        ValueError: If the supplied topic is not a supported request topic.
    """
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