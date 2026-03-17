"""Dashboard and metrics API routes."""

from fastapi import APIRouter

from app.api.dependencies import get_platform
from app.schemas.supply_chain import DashboardMetrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get executive dashboard metrics."""
    platform = get_platform()

    nodes = platform.graph.get_all_nodes()
    edges = platform.graph.get_all_edges()

    suppliers = [n for n in nodes if n.get("node_type") in ("supplier", "factory")]
    facilities = [n for n in nodes if n.get("node_type") in ("warehouse", "port", "distribution_center")]

    # Score all suppliers for risk
    assessments = []
    for s in suppliers:
        a = platform.risk_engine.score_supplier(
            supplier_id=s["id"], name=s["label"],
            country=s["country"], tier=s.get("tier", "tier_1"),
        )
        assessments.append(a)

    high_risk = sum(1 for a in assessments if a.overall >= 50)
    avg_risk = sum(a.overall for a in assessments) / max(len(assessments), 1)

    # Revenue at risk (from twin)
    revenue_impact = platform.twin.get_revenue_impact()

    # Inventory health
    total_inventory = sum(n.inventory_level for n in platform.twin.nodes.values())
    total_safety = sum(n.safety_stock for n in platform.twin.nodes.values())
    inventory_health = (total_inventory / total_safety * 100) if total_safety > 0 else 100

    # Avg lead time from edges
    transit_times = [e.get("transit_time_days", 0) for e in edges]
    avg_lead_time = sum(transit_times) / max(len(transit_times), 1)

    # Resilience score
    resilience = platform.graph.calculate_resilience_score()

    # Count unique products (using a rough proxy from twin nodes)
    product_count = len([n for n in platform.twin.nodes.values() if n.daily_consumption > 0])

    return DashboardMetrics(
        total_suppliers=len(suppliers),
        total_facilities=len(facilities),
        total_routes=len(edges),
        total_products=product_count,
        avg_risk_score=round(avg_risk, 1),
        revenue_at_risk_usd=revenue_impact["daily_revenue_loss"] * 30,
        suppliers_at_high_risk=high_risk,
        inventory_health_pct=round(min(inventory_health, 100), 1),
        avg_lead_time_days=round(avg_lead_time, 1),
        network_resilience_score=resilience,
    )


@router.get("/country-exposure")
async def get_country_exposure():
    """Get supply chain exposure by country."""
    platform = get_platform()
    concentration = platform.graph.get_country_concentration()
    total = platform.graph.node_count

    exposure = []
    for country, count in sorted(concentration.items(), key=lambda x: x[1], reverse=True):
        risk = platform.risk_engine.score_supplier(
            supplier_id="aggregate", name=f"{country} aggregate",
            country=country, tier="tier_1",
        )
        exposure.append({
            "country": country,
            "node_count": count,
            "pct_of_network": round(count / total * 100, 1),
            "risk_score": risk.overall,
            "classification": platform.risk_engine.classify_risk(risk.overall),
        })

    return exposure


@router.get("/inventory-status")
async def get_inventory_status():
    """Get inventory health across all facilities."""
    platform = get_platform()

    inventory_data = []
    for nid, node in platform.twin.nodes.items():
        if node.safety_stock <= 0:
            continue

        days_of_supply = (
            node.inventory_level / node.daily_consumption
            if node.daily_consumption > 0 else float("inf")
        )
        health_pct = (node.inventory_level / node.safety_stock * 100) if node.safety_stock > 0 else 100
        depletion_day = platform.twin.get_inventory_depletion_day(nid)

        status = "healthy"
        if health_pct < 50:
            status = "critical"
        elif health_pct < 80:
            status = "warning"

        graph_node = platform.graph.get_node(nid)
        inventory_data.append({
            "node_id": nid,
            "name": graph_node["label"] if graph_node else nid,
            "country": node.country,
            "inventory_level": node.inventory_level,
            "safety_stock": node.safety_stock,
            "health_pct": round(health_pct, 1),
            "days_of_supply": round(days_of_supply, 1) if days_of_supply != float("inf") else None,
            "daily_consumption": node.daily_consumption,
            "depletion_day": depletion_day,
            "status": status,
        })

    inventory_data.sort(key=lambda x: x["health_pct"])
    return inventory_data
