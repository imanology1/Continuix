"""Disruption simulation API routes."""

from fastapi import APIRouter, HTTPException

from app.api.dependencies import get_platform
from app.schemas.supply_chain import SimulationRequest, SimulationResult, SimulationImpact, SimulationTimelinePoint
from app.services.simulation_engine import SimulationEngine, DisruptionScenario

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/run", response_model=SimulationResult)
async def run_simulation(request: SimulationRequest):
    """
    Run a custom disruption simulation.

    Configure disruption type, affected region/suppliers, duration, and severity.
    Returns impact analysis with timeline, revenue at risk, and recommendations.
    """
    platform = get_platform()
    engine = SimulationEngine(platform.twin, platform.graph)

    scenario = DisruptionScenario(
        disruption_type=request.disruption_type,
        severity=request.severity,
        duration_days=request.duration_days,
        affected_countries=[request.affected_country] if request.affected_country else [],
        affected_node_ids=[str(sid) for sid in request.affected_supplier_ids],
        affected_edge_ids=[str(rid) for rid in request.affected_route_ids],
        demand_change_pct=request.demand_change_pct,
    )

    if request.affected_region:
        # Map region to countries
        region_countries = _region_to_countries(request.affected_region)
        scenario.affected_countries.extend(region_countries)

    output = engine.run_scenario(scenario, request.monte_carlo_runs)

    return _output_to_response(output, platform)


@router.get("/presets")
async def list_preset_scenarios():
    """List available preset disruption scenarios."""
    return {
        "scenarios": [
            {
                "id": "taiwan_strait_closure",
                "name": "Taiwan Strait Closure",
                "description": "90-day closure affecting semiconductor supply chains",
                "disruption_type": "strait_closure",
                "severity": 0.8,
                "duration_days": 90,
                "affected_countries": ["Taiwan", "China"],
            },
            {
                "id": "suez_canal_blockage",
                "name": "Suez Canal Blockage",
                "description": "14-day blockage disrupting Europe-Asia shipping",
                "disruption_type": "canal_blockage",
                "severity": 0.7,
                "duration_days": 14,
                "affected_countries": [],
            },
            {
                "id": "japan_earthquake",
                "name": "Japan Earthquake",
                "description": "Major earthquake affecting Japanese manufacturing",
                "disruption_type": "earthquake",
                "severity": 0.9,
                "duration_days": 60,
                "affected_countries": ["Japan"],
            },
            {
                "id": "china_sanctions",
                "name": "China Trade Sanctions",
                "description": "180-day sanctions restricting Chinese supplier access",
                "disruption_type": "sanctions",
                "severity": 0.6,
                "duration_days": 180,
                "affected_countries": ["China"],
            },
            {
                "id": "demand_surge",
                "name": "Demand Surge",
                "description": "50% demand surge from unexpected market shock",
                "disruption_type": "demand_surge",
                "severity": 0.5,
                "duration_days": 45,
                "affected_countries": [],
            },
        ]
    }


@router.post("/presets/{scenario_id}", response_model=SimulationResult)
async def run_preset_scenario(scenario_id: str):
    """Run a preset disruption scenario."""
    platform = get_platform()
    engine = SimulationEngine(platform.twin, platform.graph)

    try:
        output = engine.run_preset_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _output_to_response(output, platform)


def _output_to_response(output, platform) -> SimulationResult:
    from datetime import datetime

    # Find alternative suppliers from affected nodes
    affected_node_ids = [
        s["day"] for s in output.daily_snapshots[:1]
    ] if output.daily_snapshots else []

    timeline = [
        SimulationTimelinePoint(
            day=s["day"],
            inventory_level_pct=s["inventory_level_pct"],
            production_capacity_pct=s["production_capacity_pct"],
            revenue_impact_usd=s["revenue_impact_usd"],
            cumulative_loss_usd=s["cumulative_loss_usd"],
        )
        for s in output.daily_snapshots
    ]

    return SimulationResult(
        id=output.scenario_id,
        disruption_type=output.disruption_type,
        severity=output.severity,
        duration_days=output.duration_days,
        impact=SimulationImpact(
            revenue_at_risk_usd=output.revenue_at_risk_usd,
            revenue_at_risk_pct=output.revenue_at_risk_pct,
            production_delay_days=output.production_delay_days,
            affected_supplier_count=output.affected_supplier_count,
            affected_facility_count=output.affected_facility_count,
            affected_route_count=output.affected_route_count,
            inventory_depletion_day=output.inventory_depletion_day,
            customer_fulfillment_risk_pct=output.customer_fulfillment_risk_pct,
            cost_escalation_pct=output.cost_escalation_pct,
            recovery_time_days=output.recovery_time_days,
        ),
        timeline=timeline,
        affected_suppliers=[],
        alternative_suppliers=[],
        confidence_interval=output.confidence_interval,
        recommendations=output.recommendations,
        computed_at=datetime.utcnow(),
    )


def _region_to_countries(region: str) -> list[str]:
    region_map = {
        "East Asia": ["China", "Japan", "South Korea", "Taiwan"],
        "Southeast Asia": ["Vietnam", "Thailand", "Malaysia", "Indonesia", "Singapore"],
        "South Asia": ["India"],
        "Europe": ["Germany", "Netherlands", "United Kingdom"],
        "North America": ["United States", "Mexico", "Canada"],
        "Oceania": ["Australia"],
        "Middle East": ["Saudi Arabia", "UAE", "Turkey"],
    }
    return region_map.get(region, [])
