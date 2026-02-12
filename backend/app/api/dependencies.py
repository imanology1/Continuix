"""
Shared dependencies for API routes.

Manages the singleton platform instance that holds the graph, twin, and risk engines.
"""

from dataclasses import dataclass
from typing import Optional

from app.services.graph_engine import SupplyChainGraph
from app.services.twin_engine import DigitalTwin
from app.services.risk_engine import RiskEngine


@dataclass
class Platform:
    """Central container for all engine instances."""
    graph: SupplyChainGraph
    twin: DigitalTwin
    risk_engine: RiskEngine


_platform: Optional[Platform] = None


def init_platform(graph: SupplyChainGraph, twin: DigitalTwin, risk_engine: RiskEngine) -> Platform:
    global _platform
    _platform = Platform(graph=graph, twin=twin, risk_engine=risk_engine)
    return _platform


def get_platform() -> Platform:
    if _platform is None:
        raise RuntimeError("Platform not initialized. Call init_platform() first.")
    return _platform
