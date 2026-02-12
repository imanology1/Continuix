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
            # --- Original 5 ---
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
            # --- 15 New Scenarios ---
            {
                "id": "korea_fab_fire",
                "name": "Korea Fab Fire",
                "description": "Major fire at Korean semiconductor fab disrupting display and chip supply",
                "disruption_type": "factory_fire",
                "severity": 0.85,
                "duration_days": 45,
                "affected_countries": ["South Korea"],
            },
            {
                "id": "global_pandemic",
                "name": "Global Pandemic Wave",
                "description": "Pandemic wave causing factory shutdowns across manufacturing hubs",
                "disruption_type": "pandemic",
                "severity": 0.6,
                "duration_days": 120,
                "affected_countries": ["China", "Vietnam", "India", "Mexico"],
            },
            {
                "id": "china_rare_earth_ban",
                "name": "China Rare Earth Export Ban",
                "description": "China restricts rare earth exports critical for electronics manufacturing",
                "disruption_type": "export_controls",
                "severity": 0.75,
                "duration_days": 365,
                "affected_countries": ["China"],
            },
            {
                "id": "logistics_ransomware",
                "name": "Logistics Ransomware Attack",
                "description": "Ransomware disables major shipping carrier booking and tracking systems",
                "disruption_type": "ransomware",
                "severity": 0.8,
                "duration_days": 21,
                "affected_countries": [],
            },
            {
                "id": "vietnam_flooding",
                "name": "Vietnam Monsoon Flooding",
                "description": "Monsoon flooding submerges PCB assembly facilities in northern Vietnam",
                "disruption_type": "flooding",
                "severity": 0.7,
                "duration_days": 30,
                "affected_countries": ["Vietnam"],
            },
            {
                "id": "malacca_strait_closure",
                "name": "Malacca Strait Closure",
                "description": "Military tensions close Strait of Malacca disrupting raw material routes",
                "disruption_type": "strait_closure",
                "severity": 0.65,
                "duration_days": 60,
                "affected_countries": [],
            },
            {
                "id": "european_energy_crisis",
                "name": "European Energy Crisis",
                "description": "Natural gas shortage causing rolling blackouts in German manufacturing",
                "disruption_type": "energy_crisis",
                "severity": 0.55,
                "duration_days": 150,
                "affected_countries": ["Germany"],
            },
            {
                "id": "mexico_labor_strike",
                "name": "Mexico Labor Strike",
                "description": "Nationwide labor strike halting assembly operations across Mexico",
                "disruption_type": "labor_strike",
                "severity": 0.7,
                "duration_days": 28,
                "affected_countries": ["Mexico"],
            },
            {
                "id": "taiwan_supplier_bankruptcy",
                "name": "Taiwan Supplier Bankruptcy",
                "description": "Key semiconductor wafer supplier files for bankruptcy removing capacity",
                "disruption_type": "bankruptcy",
                "severity": 1.0,
                "duration_days": 180,
                "affected_countries": [],
            },
            {
                "id": "india_grid_failure",
                "name": "India Power Grid Failure",
                "description": "Cascading power grid failure disrupts Indian assembly hub operations",
                "disruption_type": "power_grid_failure",
                "severity": 0.8,
                "duration_days": 14,
                "affected_countries": ["India"],
            },
            {
                "id": "panama_canal_drought",
                "name": "Panama Canal Drought",
                "description": "Severe drought restricts Panama Canal transit reducing shipping throughput",
                "disruption_type": "drought",
                "severity": 0.5,
                "duration_days": 90,
                "affected_countries": [],
            },
            {
                "id": "us_china_trade_embargo",
                "name": "US-China Trade Embargo",
                "description": "Full trade embargo cutting off all direct Chinese supplier relationships",
                "disruption_type": "trade_embargo",
                "severity": 0.85,
                "duration_days": 365,
                "affected_countries": ["China"],
            },
            {
                "id": "australia_wildfire",
                "name": "Australia Wildfire Season",
                "description": "Catastrophic wildfire disrupts Australian lithium mining and ports",
                "disruption_type": "wildfire",
                "severity": 0.75,
                "duration_days": 45,
                "affected_countries": ["Australia"],
            },
            {
                "id": "global_recession",
                "name": "Global Recession",
                "description": "Recession triggers 40% demand collapse causing inventory buildup pressure",
                "disruption_type": "demand_collapse",
                "severity": 0.6,
                "duration_days": 180,
                "affected_countries": [],
            },
            {
                "id": "port_cyberattack",
                "name": "Port Systems Cyberattack",
                "description": "Coordinated cyberattack disables port management at Shenzhen and Kaohsiung",
                "disruption_type": "cyberattack",
                "severity": 0.7,
                "duration_days": 10,
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
