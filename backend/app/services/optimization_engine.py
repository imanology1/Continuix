"""
Optimization & Alternative Sourcing Engine

When disruption occurs, recommends:
- Replacement suppliers
- Regional sourcing shifts
- Nearshoring options
- Dual sourcing strategies
- Safety stock adjustments

Uses multi-objective scoring (cost, lead time, capacity, risk, ESG).
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from app.services.graph_engine import SupplyChainGraph
from app.services.risk_engine import RiskEngine, RiskAssessment


@dataclass
class SourcingAlternative:
    supplier_id: str
    supplier_name: str
    country: str
    region: str
    score: float  # 0-100, higher is better
    cost_change_pct: float  # positive = more expensive
    lead_time_change_days: float
    capacity_available_pct: float  # how much spare capacity
    risk_score: float
    rationale: list[str] = field(default_factory=list)


@dataclass
class InventoryRecommendation:
    facility_id: str
    facility_name: str
    product_id: str
    product_name: str
    current_safety_stock: float
    recommended_safety_stock: float
    change_pct: float
    estimated_cost_impact: float
    rationale: str


@dataclass
class OptimizationResult:
    scenario: str
    alternative_suppliers: list[SourcingAlternative]
    inventory_recommendations: list[InventoryRecommendation]
    cost_impact_summary: dict
    risk_reduction_summary: dict
    recommendations: list[str]


class OptimizationEngine:
    """
    Multi-objective optimization for supply chain resilience.
    """

    def __init__(self, graph: SupplyChainGraph, risk_engine: RiskEngine):
        self.graph = graph
        self.risk_engine = risk_engine

    def find_alternative_suppliers(
        self,
        disrupted_node_ids: list[str],
        optimization_weights: Optional[dict] = None,
    ) -> list[SourcingAlternative]:
        """
        Find and rank alternative suppliers for disrupted nodes.
        Considers: cost, lead time, capacity, political stability, risk.
        """
        if optimization_weights is None:
            optimization_weights = {
                "cost": 0.25,
                "lead_time": 0.20,
                "capacity": 0.25,
                "risk": 0.30,
            }

        all_nodes = self.graph.get_all_nodes()
        disrupted_set = set(disrupted_node_ids)

        # Collect disrupted node attributes
        disrupted_countries = set()
        disrupted_regions = set()
        for nid in disrupted_node_ids:
            node = self.graph.get_node(nid)
            if node:
                disrupted_countries.add(node.get("country", ""))
                disrupted_regions.add(node.get("region", ""))

        # Find candidates: active nodes NOT in disrupted set and preferably not in same country
        candidates = []
        for node in all_nodes:
            if node["id"] in disrupted_set:
                continue
            if node.get("node_type") not in ("supplier", "factory"):
                continue

            country = node.get("country", "")
            region = node.get("region", "")
            capacity = node.get("capacity", 0)
            utilization = node.get("utilization", 0)
            risk_score = node.get("risk_score", 50)

            # Available capacity
            available_capacity = capacity * (1 - utilization) if capacity > 0 else 0
            capacity_pct = (available_capacity / capacity * 100) if capacity > 0 else 0

            # Score components
            # Geographic diversity: prefer suppliers NOT in disrupted countries
            geo_bonus = 20 if country not in disrupted_countries else 0
            region_bonus = 10 if region not in disrupted_regions else 0

            # Lower risk = better
            risk_component = max(0, 100 - risk_score)

            # Capacity: more available = better
            capacity_component = min(capacity_pct, 100)

            # Cost estimate: different region = higher cost (proxy)
            cost_change = 0.0
            if country not in disrupted_countries:
                cost_change = 8.0  # ~8% premium for regional shift
            if region not in disrupted_regions:
                cost_change = 15.0  # ~15% for different region

            # Lead time estimate
            lead_time_change = 0.0
            if country not in disrupted_countries:
                lead_time_change = 5.0  # days
            if region not in disrupted_regions:
                lead_time_change = 12.0

            # Composite score
            score = (
                risk_component * optimization_weights["risk"]
                + capacity_component * optimization_weights["capacity"]
                + max(0, 100 - cost_change * 3) * optimization_weights["cost"]
                + max(0, 100 - lead_time_change * 3) * optimization_weights["lead_time"]
                + geo_bonus + region_bonus
            )

            rationale = []
            if country not in disrupted_countries:
                rationale.append(f"Geographic diversification: {country}")
            if capacity_pct > 20:
                rationale.append(f"{capacity_pct:.0f}% spare capacity available")
            if risk_score < 30:
                rationale.append("Low overall risk profile")
            if risk_score >= 50:
                rationale.append(f"Moderate-to-high risk score ({risk_score:.0f})")

            candidates.append(SourcingAlternative(
                supplier_id=node["id"],
                supplier_name=node.get("label", "Unknown"),
                country=country,
                region=region,
                score=round(score, 1),
                cost_change_pct=round(cost_change, 1),
                lead_time_change_days=round(lead_time_change, 1),
                capacity_available_pct=round(capacity_pct, 1),
                risk_score=round(risk_score, 1),
                rationale=rationale,
            ))

        # Sort by score descending
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:10]

    def recommend_inventory_adjustments(
        self,
        disrupted_node_ids: list[str],
        disruption_duration_days: int,
        severity: float,
        nodes_inventory: dict[str, dict],  # node_id -> {safety_stock, daily_consumption, product_name, ...}
    ) -> list[InventoryRecommendation]:
        """
        Recommend safety stock adjustments based on disruption scenario.
        """
        recommendations = []

        for node_id, inv_data in nodes_inventory.items():
            current_safety = inv_data.get("safety_stock", 0)
            daily_consumption = inv_data.get("daily_consumption", 0)
            product_name = inv_data.get("product_name", "Unknown")
            facility_name = inv_data.get("facility_name", "Unknown")
            unit_cost = inv_data.get("unit_cost", 1.0)

            if daily_consumption <= 0:
                continue

            # How many days of buffer do we need?
            buffer_days = disruption_duration_days * severity * 1.2  # 20% safety margin
            needed_safety = daily_consumption * buffer_days

            if needed_safety > current_safety:
                change_pct = ((needed_safety - current_safety) / max(current_safety, 1)) * 100
                cost_impact = (needed_safety - current_safety) * unit_cost

                rationale = (
                    f"Current safety stock covers {current_safety / daily_consumption:.0f} days. "
                    f"Disruption requires {buffer_days:.0f} days of buffer. "
                    f"Increase by {needed_safety - current_safety:.0f} units."
                )

                recommendations.append(InventoryRecommendation(
                    facility_id=node_id,
                    facility_name=facility_name,
                    product_id=inv_data.get("product_id", ""),
                    product_name=product_name,
                    current_safety_stock=current_safety,
                    recommended_safety_stock=round(needed_safety, 0),
                    change_pct=round(change_pct, 1),
                    estimated_cost_impact=round(cost_impact, 2),
                    rationale=rationale,
                ))

        # Sort by cost impact descending (highest impact first)
        recommendations.sort(key=lambda x: x.estimated_cost_impact, reverse=True)
        return recommendations

    def optimize_sourcing_strategy(
        self,
        disrupted_node_ids: list[str],
        disruption_type: str,
        severity: float,
        duration_days: int,
        nodes_inventory: dict[str, dict],
    ) -> OptimizationResult:
        """
        Full optimization: find alternatives + inventory adjustments + strategy recommendations.
        """
        alternatives = self.find_alternative_suppliers(disrupted_node_ids)
        inventory_recs = self.recommend_inventory_adjustments(
            disrupted_node_ids, duration_days, severity, nodes_inventory
        )

        # Cost impact summary
        total_inventory_cost = sum(r.estimated_cost_impact for r in inventory_recs)
        avg_sourcing_premium = (
            np.mean([a.cost_change_pct for a in alternatives]) if alternatives else 0
        )

        # Risk reduction estimate
        current_avg_risk = np.mean([a.risk_score for a in alternatives]) if alternatives else 0
        best_alt_risk = min((a.risk_score for a in alternatives), default=0)

        cost_summary = {
            "additional_safety_stock_cost": round(total_inventory_cost, 2),
            "avg_sourcing_premium_pct": round(float(avg_sourcing_premium), 1),
            "estimated_disruption_savings": round(total_inventory_cost * 3, 2),  # 3x ROI estimate
        }

        risk_summary = {
            "current_network_exposure": round(float(current_avg_risk), 1),
            "best_alternative_risk": round(float(best_alt_risk), 1),
            "estimated_risk_reduction_pct": round(
                float((current_avg_risk - best_alt_risk) / max(current_avg_risk, 1) * 100), 1
            ),
        }

        # Strategy recommendations
        strategy_recs = self._generate_strategy_recommendations(
            disruption_type, severity, duration_days,
            alternatives, inventory_recs
        )

        return OptimizationResult(
            scenario=f"{disruption_type} (severity: {severity}, duration: {duration_days}d)",
            alternative_suppliers=alternatives,
            inventory_recommendations=inventory_recs,
            cost_impact_summary=cost_summary,
            risk_reduction_summary=risk_summary,
            recommendations=strategy_recs,
        )

    def _generate_strategy_recommendations(
        self,
        disruption_type: str,
        severity: float,
        duration_days: int,
        alternatives: list[SourcingAlternative],
        inventory_recs: list[InventoryRecommendation],
    ) -> list[str]:
        """Generate high-level strategic recommendations."""
        recs = []

        # Dual sourcing
        if alternatives:
            top = alternatives[0]
            recs.append(
                f"Activate dual-sourcing with {top.supplier_name} ({top.country}). "
                f"Score: {top.score:.0f}/100, {top.capacity_available_pct:.0f}% spare capacity."
            )

        # Geographic diversification
        countries = set(a.country for a in alternatives[:3])
        if len(countries) > 1:
            recs.append(
                f"Diversify across {', '.join(countries)} to reduce geographic concentration."
            )

        # Nearshoring
        nearshore_alts = [a for a in alternatives if a.lead_time_change_days < 7]
        if nearshore_alts:
            recs.append(
                f"Nearshoring option: {nearshore_alts[0].supplier_name} with "
                f"only {nearshore_alts[0].lead_time_change_days:.0f} days additional lead time."
            )

        # Inventory
        if inventory_recs:
            total_cost = sum(r.estimated_cost_impact for r in inventory_recs)
            recs.append(
                f"Increase safety stock across {len(inventory_recs)} products. "
                f"Estimated cost: ${total_cost:,.0f}. "
                f"Provides buffer for {duration_days}-day disruption."
            )

        # Severity-based
        if severity > 0.7:
            recs.append(
                "HIGH SEVERITY: Recommend immediate executive briefing and "
                "activation of business continuity playbook."
            )

        if duration_days > 90:
            recs.append(
                "Extended disruption window. Evaluate permanent sourcing shifts "
                "rather than temporary measures."
            )

        return recs
