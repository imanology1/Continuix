"""Optimization and alternative sourcing API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import get_platform
from app.services.optimization_engine import OptimizationEngine
from app.services.simulation_engine import SimulationEngine, DisruptionScenario

router = APIRouter(prefix="/optimization", tags=["optimization"])


class OptimizationRequest(BaseModel):
    disrupted_node_ids: list[str] = []
    disrupted_country: str | None = None
    disruption_type: str = "port_congestion"
    severity: float = Field(ge=0.0, le=1.0, default=0.5)
    duration_days: int = Field(ge=1, le=365, default=30)
    optimization_weights: dict[str, float] | None = None


@router.post("/analyze")
async def run_optimization(request: OptimizationRequest):
    """
    Run optimization analysis for a disruption scenario.
    Returns alternative suppliers, inventory adjustments, and strategic recommendations.
    """
    platform = get_platform()
    opt_engine = OptimizationEngine(platform.graph, platform.risk_engine)

    # Resolve disrupted nodes
    disrupted_ids = list(request.disrupted_node_ids)
    if request.disrupted_country:
        country_nodes = platform.graph.get_nodes_by_country(request.disrupted_country)
        disrupted_ids.extend(n["id"] for n in country_nodes)

    if not disrupted_ids:
        return {"error": "No disrupted nodes specified. Provide node IDs or a country."}

    # Build inventory data from twin
    nodes_inventory = {}
    for nid in disrupted_ids:
        twin_node = platform.twin.nodes.get(nid)
        graph_node = platform.graph.get_node(nid)
        if twin_node and twin_node.daily_consumption > 0:
            nodes_inventory[nid] = {
                "safety_stock": twin_node.safety_stock,
                "daily_consumption": twin_node.daily_consumption,
                "product_name": graph_node["label"] if graph_node else nid,
                "facility_name": graph_node["label"] if graph_node else nid,
                "unit_cost": twin_node.revenue_per_unit * 0.6,
                "product_id": nid,
            }

    result = opt_engine.optimize_sourcing_strategy(
        disrupted_node_ids=disrupted_ids,
        disruption_type=request.disruption_type,
        severity=request.severity,
        duration_days=request.duration_days,
        nodes_inventory=nodes_inventory,
    )

    return {
        "scenario": result.scenario,
        "alternative_suppliers": [
            {
                "id": a.supplier_id,
                "name": a.supplier_name,
                "country": a.country,
                "region": a.region,
                "score": a.score,
                "cost_change_pct": a.cost_change_pct,
                "lead_time_change_days": a.lead_time_change_days,
                "capacity_available_pct": a.capacity_available_pct,
                "risk_score": a.risk_score,
                "rationale": a.rationale,
            }
            for a in result.alternative_suppliers
        ],
        "inventory_recommendations": [
            {
                "facility_id": r.facility_id,
                "facility_name": r.facility_name,
                "product_name": r.product_name,
                "current_safety_stock": r.current_safety_stock,
                "recommended_safety_stock": r.recommended_safety_stock,
                "change_pct": r.change_pct,
                "estimated_cost_impact": r.estimated_cost_impact,
                "rationale": r.rationale,
            }
            for r in result.inventory_recommendations
        ],
        "cost_impact_summary": result.cost_impact_summary,
        "risk_reduction_summary": result.risk_reduction_summary,
        "recommendations": result.recommendations,
    }


@router.get("/alternatives/{node_id}")
async def get_alternatives_for_node(node_id: str):
    """Find alternative suppliers for a specific node."""
    platform = get_platform()
    opt_engine = OptimizationEngine(platform.graph, platform.risk_engine)

    alternatives = opt_engine.find_alternative_suppliers([node_id])

    node = platform.graph.get_node(node_id)
    return {
        "disrupted_node": {
            "id": node_id,
            "name": node["label"] if node else "Unknown",
            "country": node["country"] if node else "Unknown",
        },
        "alternatives": [
            {
                "id": a.supplier_id,
                "name": a.supplier_name,
                "country": a.country,
                "score": a.score,
                "cost_change_pct": a.cost_change_pct,
                "lead_time_change_days": a.lead_time_change_days,
                "capacity_available_pct": a.capacity_available_pct,
                "risk_score": a.risk_score,
                "rationale": a.rationale,
            }
            for a in alternatives
        ],
    }
