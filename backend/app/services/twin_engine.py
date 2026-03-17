"""
Digital Twin Modeling Engine

Creates a computational replica of the supply chain where each node
carries dynamic state (inventory, throughput, delays) that evolves over time.

The twin is the simulation substrate — the disruption engine operates on it.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from copy import deepcopy

import numpy as np


@dataclass
class TwinNodeState:
    """Dynamic state of a supply chain node at a point in time."""
    node_id: str
    node_type: str  # supplier, factory, warehouse, port

    # Capacity
    max_capacity: float = 1000.0
    current_throughput: float = 700.0
    utilization: float = 0.7

    # Inventory (for warehouses / factories)
    inventory_level: float = 0.0
    safety_stock: float = 0.0
    daily_consumption: float = 0.0
    daily_inflow: float = 0.0

    # Financial
    operating_cost_per_day: float = 0.0
    revenue_per_unit: float = 0.0

    # Status
    is_operational: bool = True
    capacity_reduction: float = 0.0  # 0-1, applied during disruptions
    recovery_rate: float = 0.05  # per day, how fast capacity comes back

    # Risk
    risk_score: float = 0.0
    country: str = ""
    region: str = ""


@dataclass
class TwinEdgeState:
    """Dynamic state of a transport route."""
    edge_id: str
    source_id: str
    target_id: str
    transport_mode: str

    # Performance
    base_transit_time_days: float = 5.0
    current_transit_time_days: float = 5.0
    delay_factor: float = 1.0  # multiplier: 1.0 = normal

    # Capacity
    max_capacity: float = 1000.0
    current_flow: float = 0.0
    cost_per_unit: float = 1.0

    # Status
    is_operational: bool = True
    congestion_level: float = 0.0  # 0-1
    is_chokepoint: bool = False


@dataclass
class TwinSnapshot:
    """Complete state of the digital twin at a moment in time."""
    timestamp: datetime
    day: int
    nodes: dict[str, TwinNodeState]
    edges: dict[str, TwinEdgeState]
    total_production_capacity_pct: float = 100.0
    total_inventory_pct: float = 100.0
    total_revenue_per_day: float = 0.0
    total_cost_per_day: float = 0.0


class DigitalTwin:
    """
    Living computational model of the supply chain.

    Holds node/edge states and supports:
    - State evolution over time
    - Disruption application (capacity cuts, route closures)
    - Recovery modeling
    - Snapshot capture for timeline playback
    """

    def __init__(self):
        self.nodes: dict[str, TwinNodeState] = {}
        self.edges: dict[str, TwinEdgeState] = {}
        self.snapshots: list[TwinSnapshot] = []
        self.start_date: datetime = datetime.utcnow()
        self.current_day: int = 0
        self._baseline_nodes: dict[str, TwinNodeState] = {}
        self._baseline_edges: dict[str, TwinEdgeState] = {}

    def add_node(self, state: TwinNodeState) -> None:
        self.nodes[state.node_id] = state
        self._baseline_nodes[state.node_id] = deepcopy(state)

    def add_edge(self, state: TwinEdgeState) -> None:
        self.edges[state.edge_id] = state
        self._baseline_edges[state.edge_id] = deepcopy(state)

    def reset(self) -> None:
        """Reset all state to baseline."""
        self.nodes = deepcopy(self._baseline_nodes)
        self.edges = deepcopy(self._baseline_edges)
        self.snapshots = []
        self.current_day = 0

    def capture_snapshot(self) -> TwinSnapshot:
        """Capture current state as an immutable snapshot."""
        total_max_capacity = sum(n.max_capacity for n in self.nodes.values())
        total_throughput = sum(n.current_throughput for n in self.nodes.values())
        total_inventory = sum(n.inventory_level for n in self.nodes.values())
        total_safety = sum(n.safety_stock for n in self.nodes.values())
        total_revenue = sum(
            n.current_throughput * n.revenue_per_unit
            for n in self.nodes.values()
        )
        total_cost = sum(n.operating_cost_per_day for n in self.nodes.values())

        snapshot = TwinSnapshot(
            timestamp=self.start_date + timedelta(days=self.current_day),
            day=self.current_day,
            nodes=deepcopy(self.nodes),
            edges=deepcopy(self.edges),
            total_production_capacity_pct=(
                (total_throughput / total_max_capacity * 100) if total_max_capacity > 0 else 0
            ),
            total_inventory_pct=(
                (total_inventory / total_safety * 100) if total_safety > 0 else 100
            ),
            total_revenue_per_day=total_revenue,
            total_cost_per_day=total_cost,
        )
        self.snapshots.append(snapshot)
        return snapshot

    # --- Disruption Application ---

    def apply_node_disruption(
        self, node_id: str, capacity_reduction: float, operational: bool = True
    ) -> None:
        """
        Reduce a node's capacity. capacity_reduction is 0-1 (0.8 = 80% reduction).
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.capacity_reduction = min(capacity_reduction, 1.0)
            node.is_operational = operational
            effective = node.max_capacity * (1 - node.capacity_reduction)
            node.current_throughput = min(node.current_throughput, effective)
            node.utilization = (
                node.current_throughput / node.max_capacity
                if node.max_capacity > 0 else 0
            )

    def apply_edge_disruption(
        self, edge_id: str, delay_factor: float = 2.0, operational: bool = True
    ) -> None:
        """Apply delays or shut down a route."""
        if edge_id in self.edges:
            edge = self.edges[edge_id]
            edge.is_operational = operational
            edge.delay_factor = delay_factor
            edge.current_transit_time_days = edge.base_transit_time_days * delay_factor

    def apply_region_disruption(
        self, country: str, capacity_reduction: float, severity: float = 0.5
    ) -> list[str]:
        """Disrupt all nodes in a country. Returns affected node IDs."""
        affected = []
        for nid, node in self.nodes.items():
            if node.country == country:
                actual_reduction = capacity_reduction * severity
                self.apply_node_disruption(nid, actual_reduction, operational=(severity < 1.0))
                affected.append(nid)
        return affected

    # --- Daily Evolution ---

    def step(self) -> TwinSnapshot:
        """
        Advance the twin by one day.
        Handles:
        - Inventory consumption
        - Production output
        - Route transit
        - Gradual recovery
        """
        self.current_day += 1

        for node in self.nodes.values():
            if not node.is_operational:
                # No production, only consumption
                node.inventory_level = max(0, node.inventory_level - node.daily_consumption)
                continue

            # Recovery: gradually restore capacity
            if node.capacity_reduction > 0:
                node.capacity_reduction = max(0, node.capacity_reduction - node.recovery_rate)
                effective_cap = node.max_capacity * (1 - node.capacity_reduction)
                node.current_throughput = min(node.current_throughput, effective_cap)
                if node.capacity_reduction == 0:
                    node.current_throughput = node.max_capacity * node.utilization

            # Inventory: consume and replenish
            produced = node.current_throughput / 30  # daily production (monthly capacity / 30)
            node.inventory_level = max(
                0, node.inventory_level - node.daily_consumption + produced + node.daily_inflow
            )

        # Edge recovery
        for edge in self.edges.values():
            if not edge.is_operational:
                continue
            if edge.delay_factor > 1.0:
                edge.delay_factor = max(1.0, edge.delay_factor - 0.02)
                edge.current_transit_time_days = edge.base_transit_time_days * edge.delay_factor

        return self.capture_snapshot()

    def run(self, days: int) -> list[TwinSnapshot]:
        """Run the twin forward for N days, capturing daily snapshots."""
        results = []
        for _ in range(days):
            results.append(self.step())
        return results

    # --- Analytics ---

    def get_inventory_depletion_day(self, node_id: str) -> Optional[int]:
        """Estimate when a node's inventory hits zero based on current consumption."""
        node = self.nodes.get(node_id)
        if not node or node.daily_consumption <= 0:
            return None
        net_daily = node.daily_consumption - (node.current_throughput / 30) - node.daily_inflow
        if net_daily <= 0:
            return None  # Not depleting
        days = node.inventory_level / net_daily
        return self.current_day + int(days)

    def get_production_loss(self) -> dict:
        """Compare current production to baseline."""
        baseline_production = sum(n.current_throughput for n in self._baseline_nodes.values())
        current_production = sum(n.current_throughput for n in self.nodes.values())
        loss = baseline_production - current_production

        return {
            "baseline_daily_production": baseline_production,
            "current_daily_production": current_production,
            "production_loss": loss,
            "loss_pct": (loss / baseline_production * 100) if baseline_production > 0 else 0,
        }

    def get_revenue_impact(self) -> dict:
        """Calculate revenue impact of disruptions."""
        baseline_revenue = sum(
            n.current_throughput * n.revenue_per_unit
            for n in self._baseline_nodes.values()
        )
        current_revenue = sum(
            n.current_throughput * n.revenue_per_unit
            for n in self.nodes.values()
        )
        daily_loss = baseline_revenue - current_revenue

        return {
            "baseline_daily_revenue": baseline_revenue,
            "current_daily_revenue": current_revenue,
            "daily_revenue_loss": daily_loss,
            "loss_pct": (daily_loss / baseline_revenue * 100) if baseline_revenue > 0 else 0,
        }
