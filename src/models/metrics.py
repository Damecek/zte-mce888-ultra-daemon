"""Data structures describing modem metric snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class NeighborCell:
    id: str
    rsrp: float
    rsrq: float


@dataclass(slots=True)
class LTEReadings:
    rsrp1: float
    sinr1: float
    rsrp2: float
    sinr2: float
    rsrp3: float
    sinr3: float
    rsrp4: float
    sinr4: float
    rsrq: float
    rssi: float
    earfcn: int
    pci: int
    bw: str


@dataclass(slots=True)
class NR5GReadings:
    rsrp1: float
    rsrp2: float
    sinr: float
    arfcn: int
    pci: int
    bw: str


@dataclass(slots=True)
class TemperatureReadings:
    a: float
    m: float
    p: float


@dataclass(slots=True)
class MetricSnapshot:
    timestamp: datetime
    host: str
    lte: LTEReadings
    nr5g: NR5GReadings
    provider: str
    cell: str
    neighbors: List[NeighborCell] = field(default_factory=list)
    connection: str = ""
    bands: str = ""
    wan_ip: str = ""
    temp: Optional[TemperatureReadings] = None


__all__ = [
    "NeighborCell",
    "LTEReadings",
    "NR5GReadings",
    "TemperatureReadings",
    "MetricSnapshot",
]
