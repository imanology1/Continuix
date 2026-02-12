"""
Disruption Simulation Engine

The core ROI driver. Runs what-if scenarios against the digital twin
and produces impact forecasts with confidence intervals.

Supports 5 MVP scenario types:
1. Geopolitical (sanctions, strait closures)
2. Natural disaster (earthquake, hurricane, flooding)
3. Operational (factory fire, labor strike)
4. Logistics (port congestion, canal blockage)
5. Demand shock (sudden demand surge or drop)
"""

import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np

from app.services.graph_engine import SupplyChainGraph
from app.services.twin_engine import DigitalTwin, TwinSnapshot


@dataclass
class DisruptionScenario:
    disruption_type: str
    severity: float  # 0-1
    duration_days: int
    affected_countries: list[str] = field(default_factory=list)
    affected_node_ids: list[str] = field(default_factory=list)
    affected_edge_ids: list[str] = field(default_factory=list)
    demand_change_pct: float = 0.0  # positive = surge, negative = drop
    description: str = ""


@dataclass
class SimulationOutput:
    scenario_id: str
    disruption_type: str
    severity: float
    duration_days: int

    # Impact metrics
    revenue_at_risk_usd: float = 0.0
    revenue_at_risk_pct: float = 0.0
    production_delay_days: float = 0.0
    affected_supplier_count: int = 0
    affected_facility_count: int = 0
    affected_route_count: int = 0
    inventory_depletion_day: Optional[int] = None
    customer_fulfillment_risk_pct: float = 0.0
    cost_escalation_pct: float = 0.0
    recovery_time_days: float = 0.0

    # Timeline
    daily_snapshots: list[dict] = field(default_factory=list)

    # Monte Carlo
    confidence_interval: float = 0.0
    p10_revenue_loss: float = 0.0
    p50_revenue_loss: float = 0.0
    p90_revenue_loss: float = 0.0

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


# --- Disruption Profiles ---

DISRUPTION_PROFILES = {
    # Geopolitical
    "sanctions": {
        "capacity_reduction_range": (0.7, 1.0),
        "delay_factor_range": (2.0, 5.0),
        "recovery_rate": 0.01,
        "cost_escalation": 0.30,
    },
    "strait_closure": {
        "capacity_reduction_range": (0.3, 0.8),
        "delay_factor_range": (3.0, 10.0),
        "recovery_rate": 0.02,
        "cost_escalation": 0.50,
    },
    "trade_embargo": {
        "capacity_reduction_range": (0.8, 1.0),
        "delay_factor_range": (5.0, 15.0),
        "recovery_rate": 0.005,
        "cost_escalation": 0.40,
    },
    "tariff": {
        "capacity_reduction_range": (0.0, 0.1),
        "delay_factor_range": (1.1, 1.5),
        "recovery_rate": 0.1,
        "cost_escalation": 0.25,
    },

    # Natural disaster
    "earthquake": {
        "capacity_reduction_range": (0.5, 1.0),
        "delay_factor_range": (2.0, 8.0),
        "recovery_rate": 0.02,
        "cost_escalation": 0.20,
    },
    "hurricane": {
        "capacity_reduction_range": (0.4, 0.9),
        "delay_factor_range": (2.0, 6.0),
        "recovery_rate": 0.03,
        "cost_escalation": 0.15,
    },
    "flooding": {
        "capacity_reduction_range": (0.3, 0.8),
        "delay_factor_range": (1.5, 4.0),
        "recovery_rate": 0.04,
        "cost_escalation": 0.10,
    },

    # Operational
    "factory_fire": {
        "capacity_reduction_range": (0.8, 1.0),
        "delay_factor_range": (1.0, 1.5),
        "recovery_rate": 0.01,
        "cost_escalation": 0.10,
    },
    "labor_strike": {
        "capacity_reduction_range": (0.5, 0.9),
        "delay_factor_range": (1.2, 2.0),
        "recovery_rate": 0.05,
        "cost_escalation": 0.15,
    },
    "bankruptcy": {
        "capacity_reduction_range": (1.0, 1.0),
        "delay_factor_range": (1.0, 1.0),
        "recovery_rate": 0.0,
        "cost_escalation": 0.50,
    },

    # Logistics
    "port_congestion": {
        "capacity_reduction_range": (0.1, 0.4),
        "delay_factor_range": (2.0, 5.0),
        "recovery_rate": 0.05,
        "cost_escalation": 0.20,
    },
    "canal_blockage": {
        "capacity_reduction_range": (0.2, 0.6),
        "delay_factor_range": (3.0, 8.0),
        "recovery_rate": 0.04,
        "cost_escalation": 0.35,
    },
    "shipping_shortage": {
        "capacity_reduction_range": (0.2, 0.5),
        "delay_factor_range": (1.5, 3.0),
        "recovery_rate": 0.03,
        "cost_escalation": 0.25,
    },

    # Demand shock
    "demand_surge": {
        "capacity_reduction_range": (0.0, 0.0),
        "delay_factor_range": (1.0, 1.5),
        "recovery_rate": 0.1,
        "cost_escalation": 0.15,
    },
}


class SimulationEngine:
    """
    Runs disruption scenarios against the digital twin and graph engine.
    Produces impact forecasts, timelines, and recommendations.
    """

    def __init__(self, twin: DigitalTwin, graph: SupplyChainGraph):
        self.twin = twin
        self.graph = graph

    def run_scenario(self, scenario: DisruptionScenario, monte_carlo_runs: int = 500) -> SimulationOutput:
        """Execute a full disruption simulation."""
        profile = DISRUPTION_PROFILES.get(scenario.disruption_type, DISRUPTION_PROFILES["port_congestion"])

        # Run Monte Carlo for confidence intervals
        mc_losses = self._monte_carlo(scenario, profile, monte_carlo_runs)

        # Run deterministic simulation for timeline
        self.twin.reset()
        affected_nodes, affected_edges = self._apply_disruption(scenario, profile, scenario.severity)

        # Capture baseline before disruption takes effect
        baseline = self.twin.capture_snapshot()

        # Run the twin forward
        snapshots = self.twin.run(scenario.duration_days + 60)  # +60 for recovery observation

        # Compute impact
        output = self._compute_impact(
            scenario, profile, baseline, snapshots,
            affected_nodes, affected_edges, mc_losses
        )

        # Generate recommendations
        output.recommendations = self._generate_recommendations(
            scenario, affected_nodes, output
        )

        self.twin.reset()
        return output

    def _apply_disruption(
        self, scenario: DisruptionScenario, profile: dict, severity: float
    ) -> tuple[list[str], list[str]]:
        """Apply disruption to twin nodes and edges."""
        cap_lo, cap_hi = profile["capacity_reduction_range"]
        delay_lo, delay_hi = profile["delay_factor_range"]

        capacity_reduction = cap_lo + (cap_hi - cap_lo) * severity
        delay_factor = delay_lo + (delay_hi - delay_lo) * severity

        affected_nodes = []
        affected_edges = []

        # Apply to specific nodes
        for node_id in scenario.affected_node_ids:
            self.twin.apply_node_disruption(
                node_id, capacity_reduction, operational=(capacity_reduction < 1.0)
            )
            if node_id in self.twin.nodes:
                self.twin.nodes[node_id].recovery_rate = profile["recovery_rate"]
            affected_nodes.append(node_id)

        # Apply to regions/countries
        for country in scenario.affected_countries:
            region_affected = self.twin.apply_region_disruption(
                country, capacity_reduction, severity
            )
            affected_nodes.extend(region_affected)

        # Apply to edges
        for edge_id in scenario.affected_edge_ids:
            self.twin.apply_edge_disruption(edge_id, delay_factor)
            affected_edges.append(edge_id)

        # Propagate through graph: downstream nodes face reduced inflow
        all_downstream = set()
        for node_id in affected_nodes:
            downstream = self.graph.get_downstream_dependents(node_id)
            all_downstream.update(downstream)

        for downstream_id in all_downstream:
            if downstream_id not in affected_nodes and downstream_id in self.twin.nodes:
                # Downstream nodes get partial impact
                propagated_reduction = capacity_reduction * 0.5
                self.twin.nodes[downstream_id].daily_inflow *= (1 - propagated_reduction)

        # Demand shock handling
        if scenario.demand_change_pct != 0:
            for node in self.twin.nodes.values():
                if node.daily_consumption > 0:
                    node.daily_consumption *= (1 + scenario.demand_change_pct)

        return list(set(affected_nodes)), affected_edges

    def _monte_carlo(
        self, scenario: DisruptionScenario, profile: dict, runs: int
    ) -> np.ndarray:
        """Run Monte Carlo simulation for revenue loss distribution."""
        rng = np.random.default_rng(42)
        losses = np.zeros(runs)

        cap_lo, cap_hi = profile["capacity_reduction_range"]
        baseline_revenue = sum(
            n.current_throughput * n.revenue_per_unit
            for n in self.twin.nodes.values()
        )

        for i in range(runs):
            # Vary severity
            severity = np.clip(
                rng.normal(scenario.severity, 0.15), 0.1, 1.0
            )
            capacity_reduction = cap_lo + (cap_hi - cap_lo) * severity

            # Vary duration
            duration = max(1, int(rng.normal(scenario.duration_days, scenario.duration_days * 0.2)))

            # Estimate affected fraction of network
            if scenario.affected_countries:
                affected_fraction = sum(
                    1 for n in self.twin.nodes.values()
                    if n.country in scenario.affected_countries
                ) / max(len(self.twin.nodes), 1)
            elif scenario.affected_node_ids:
                affected_fraction = len(scenario.affected_node_ids) / max(len(self.twin.nodes), 1)
            else:
                affected_fraction = severity * 0.3  # generic estimate

            daily_loss = baseline_revenue * affected_fraction * capacity_reduction
            losses[i] = daily_loss * duration

        return losses

    def _compute_impact(
        self,
        scenario: DisruptionScenario,
        profile: dict,
        baseline: TwinSnapshot,
        snapshots: list[TwinSnapshot],
        affected_nodes: list[str],
        affected_edges: list[str],
        mc_losses: np.ndarray,
    ) -> SimulationOutput:
        """Compute impact metrics from simulation results."""
        revenue_impact = self.twin.get_revenue_impact()

        # Find inventory depletion point
        depletion_day = None
        for snap in snapshots:
            if snap.total_inventory_pct < 10:
                depletion_day = snap.day
                break

        # Find recovery point (when production capacity returns to >90%)
        recovery_day = scenario.duration_days
        for snap in snapshots:
            if snap.day > scenario.duration_days and snap.total_production_capacity_pct > 90:
                recovery_day = snap.day
                break

        # Build timeline for frontend
        daily_timeline = []
        cumulative_loss = 0.0
        for snap in snapshots:
            daily_loss = max(0, baseline.total_revenue_per_day - snap.total_revenue_per_day)
            cumulative_loss += daily_loss
            daily_timeline.append({
                "day": snap.day,
                "inventory_level_pct": snap.total_inventory_pct,
                "production_capacity_pct": snap.total_production_capacity_pct,
                "revenue_impact_usd": daily_loss,
                "cumulative_loss_usd": cumulative_loss,
            })

        total_revenue_loss = cumulative_loss
        baseline_total = baseline.total_revenue_per_day * (scenario.duration_days + 60)

        # Affected counts
        supplier_count = len([
            n for n in affected_nodes
            if self.twin.nodes.get(n, None) and self.twin.nodes[n].node_type == "supplier"
        ])
        facility_count = len(affected_nodes) - supplier_count

        return SimulationOutput(
            scenario_id=str(uuid.uuid4()),
            disruption_type=scenario.disruption_type,
            severity=scenario.severity,
            duration_days=scenario.duration_days,
            revenue_at_risk_usd=total_revenue_loss,
            revenue_at_risk_pct=(total_revenue_loss / baseline_total * 100) if baseline_total > 0 else 0,
            production_delay_days=float(recovery_day - scenario.duration_days),
            affected_supplier_count=supplier_count,
            affected_facility_count=facility_count,
            affected_route_count=len(affected_edges),
            inventory_depletion_day=depletion_day,
            customer_fulfillment_risk_pct=min(100, revenue_impact["loss_pct"] * 1.2),
            cost_escalation_pct=profile["cost_escalation"] * scenario.severity * 100,
            recovery_time_days=float(recovery_day),
            daily_snapshots=daily_timeline,
            confidence_interval=0.90,
            p10_revenue_loss=float(np.percentile(mc_losses, 10)),
            p50_revenue_loss=float(np.percentile(mc_losses, 50)),
            p90_revenue_loss=float(np.percentile(mc_losses, 90)),
        )

    def _generate_recommendations(
        self,
        scenario: DisruptionScenario,
        affected_nodes: list[str],
        output: SimulationOutput,
    ) -> list[str]:
        """Generate actionable recommendations based on simulation results."""
        recs = []

        # High revenue risk
        if output.revenue_at_risk_pct > 10:
            recs.append(
                f"CRITICAL: {output.revenue_at_risk_pct:.1f}% of revenue at risk. "
                "Activate business continuity plan and notify executive leadership."
            )

        # Single-source dependency
        spofs = self.graph.find_single_points_of_failure()
        affected_spofs = [n for n in affected_nodes if n in spofs]
        if affected_spofs:
            recs.append(
                f"{len(affected_spofs)} single-point-of-failure supplier(s) affected. "
                "Prioritize dual-sourcing for these nodes."
            )

        # Inventory at risk
        if output.inventory_depletion_day and output.inventory_depletion_day < scenario.duration_days:
            recs.append(
                f"Inventory depletes by day {output.inventory_depletion_day}. "
                "Increase safety stock at key warehouses or expedite alternative sourcing."
            )

        # Geographic concentration
        if scenario.affected_countries:
            country_concentration = self.graph.get_country_concentration()
            for country in scenario.affected_countries:
                count = country_concentration.get(country, 0)
                total = self.graph.node_count
                if total > 0 and count / total > 0.3:
                    recs.append(
                        f"High geographic concentration: {count}/{total} nodes in {country}. "
                        "Consider nearshoring or regional diversification."
                    )

        # Route alternatives
        if output.affected_route_count > 0:
            recs.append(
                "Evaluate alternative shipping routes. Consider air freight for "
                "critical components during disruption window."
            )

        # Cost management
        if output.cost_escalation_pct > 20:
            recs.append(
                f"Expected cost escalation of {output.cost_escalation_pct:.0f}%. "
                "Lock in spot contracts now and negotiate with backup logistics providers."
            )

        # Recovery planning
        if output.recovery_time_days > scenario.duration_days * 1.5:
            recs.append(
                f"Recovery extends {output.recovery_time_days:.0f} days beyond disruption. "
                "Pre-position recovery inventory and establish rapid-response supplier agreements."
            )

        if not recs:
            recs.append("Impact within acceptable tolerance. Continue monitoring risk indicators.")

        return recs

    def run_preset_scenario(self, scenario_name: str) -> SimulationOutput:
        """Run one of the 5 preset MVP scenarios."""
        presets = {
            "taiwan_strait_closure": DisruptionScenario(
                disruption_type="strait_closure",
                severity=0.8,
                duration_days=90,
                affected_countries=["Taiwan", "China"],
                description="Taiwan Strait closure affecting semiconductor supply",
            ),
            "suez_canal_blockage": DisruptionScenario(
                disruption_type="canal_blockage",
                severity=0.7,
                duration_days=14,
                affected_countries=[],
                description="Suez Canal blockage disrupting Europe-Asia shipping",
            ),
            "japan_earthquake": DisruptionScenario(
                disruption_type="earthquake",
                severity=0.9,
                duration_days=60,
                affected_countries=["Japan"],
                description="Major earthquake affecting Japanese manufacturing",
            ),
            "china_sanctions": DisruptionScenario(
                disruption_type="sanctions",
                severity=0.6,
                duration_days=180,
                affected_countries=["China"],
                description="Trade sanctions restricting Chinese supplier access",
            ),
            "demand_surge": DisruptionScenario(
                disruption_type="demand_surge",
                severity=0.5,
                duration_days=45,
                demand_change_pct=0.5,
                description="50% demand surge from market shock",
            ),
        }

        scenario = presets.get(scenario_name)
        if not scenario:
            raise ValueError(
                f"Unknown preset: {scenario_name}. Available: {list(presets.keys())}"
            )
        return self.run_scenario(scenario)
