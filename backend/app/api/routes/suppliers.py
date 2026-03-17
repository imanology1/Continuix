"""Supplier management API routes."""

from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.api.dependencies import get_platform
from app.schemas.supply_chain import SupplierResponse, GraphNode

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(
    tier: str | None = None,
    country: str | None = None,
    is_critical: bool | None = None,
):
    """List all suppliers with optional filtering."""
    platform = get_platform()
    nodes = platform.graph.get_all_nodes()

    suppliers = []
    for node in nodes:
        if node.get("node_type") not in ("supplier", "factory"):
            continue
        if tier and node.get("tier") != tier:
            continue
        if country and node.get("country") != country:
            continue
        if is_critical is not None and node.get("is_critical") != is_critical:
            continue

        risk = platform.risk_engine.score_supplier(
            supplier_id=node["id"],
            name=node["label"],
            country=node["country"],
            tier=node.get("tier", "tier_1"),
        )

        suppliers.append(_node_to_supplier_response(node, risk))

    return suppliers


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: str):
    """Get detailed supplier information."""
    platform = get_platform()
    node = platform.graph.get_node(supplier_id)
    if not node:
        raise HTTPException(status_code=404, detail="Supplier not found")

    risk = platform.risk_engine.score_supplier(
        supplier_id=node["id"],
        name=node["label"],
        country=node["country"],
        tier=node.get("tier", "tier_1"),
    )

    # Add dependency analysis
    upstream = platform.graph.get_upstream_suppliers(supplier_id)
    downstream = platform.graph.get_downstream_dependents(supplier_id)
    criticality = platform.graph.calculate_node_criticality(supplier_id)

    response = _node_to_supplier_response(node, risk)
    return {
        **response.model_dump(),
        "upstream_supplier_count": len(upstream),
        "downstream_dependent_count": len(downstream),
        "criticality_score": criticality,
        "risk_factors": risk.factors,
    }


@router.get("/{supplier_id}/dependencies")
async def get_supplier_dependencies(supplier_id: str, max_depth: int = 3):
    """Get upstream and downstream dependencies for a supplier."""
    platform = get_platform()
    node = platform.graph.get_node(supplier_id)
    if not node:
        raise HTTPException(status_code=404, detail="Supplier not found")

    upstream = platform.graph.get_upstream_suppliers(supplier_id, max_depth)
    downstream = platform.graph.get_downstream_dependents(supplier_id, max_depth)

    return {
        "supplier_id": supplier_id,
        "upstream": [platform.graph.get_node(uid) for uid in upstream],
        "downstream": [platform.graph.get_node(did) for did in downstream],
    }


def _node_to_supplier_response(node: dict, risk) -> SupplierResponse:
    from datetime import datetime
    return SupplierResponse(
        id=UUID(int=hash(node["id"]) % (2**128)),
        name=node["label"],
        tier=node.get("tier", "tier_1"),
        country=node["country"],
        region=node.get("region", ""),
        latitude=node.get("latitude", 0),
        longitude=node.get("longitude", 0),
        overall_risk_score=risk.overall,
        geopolitical_risk=risk.geopolitical,
        climate_risk=risk.climate,
        financial_risk=risk.financial,
        cyber_risk=risk.cyber,
        logistics_risk=risk.logistics,
        is_critical=node.get("is_critical", False),
        reliability_score=0.9,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
