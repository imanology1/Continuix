"""Risk intelligence API routes."""

from fastapi import APIRouter

from app.api.dependencies import get_platform
from app.schemas.supply_chain import RiskScore, RiskSummary

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/summary", response_model=RiskSummary)
async def get_risk_summary():
    """Get aggregated risk summary across the entire supply chain."""
    platform = get_platform()
    assessments = _score_all_entities(platform)

    summary = platform.risk_engine.compute_network_risk_summary(assessments)

    # Build risk by tier
    risk_by_tier: dict[str, list[float]] = {}
    for a in assessments:
        node = platform.graph.get_node(a.entity_id)
        if node:
            tier = node.get("tier", "infrastructure")
            risk_by_tier.setdefault(tier, []).append(a.overall)

    risk_by_tier_avg = {k: round(sum(v) / len(v), 1) for k, v in risk_by_tier.items()}

    top_risks = sorted(assessments, key=lambda a: a.overall, reverse=True)[:10]

    return RiskSummary(
        total_suppliers=summary["total_entities"],
        high_risk_count=summary["high_risk"],
        medium_risk_count=summary["medium_risk"],
        low_risk_count=summary["low_risk"],
        average_risk_score=summary["avg_score"],
        top_risks=[
            RiskScore(
                entity_id=_str_to_uuid(a.entity_id),
                entity_type=a.entity_type,
                entity_name=a.entity_name,
                overall_score=a.overall,
                geopolitical=a.geopolitical,
                climate=a.climate,
                financial=a.financial,
                cyber=a.cyber,
                logistics=a.logistics,
                trend="stable",
            )
            for a in top_risks
        ],
        risk_by_country=summary["by_country"],
        risk_by_tier=risk_by_tier_avg,
    )


@router.get("/scores")
async def get_all_risk_scores():
    """Get risk scores for every entity in the supply chain."""
    platform = get_platform()
    assessments = _score_all_entities(platform)

    return [
        {
            "entity_id": a.entity_id,
            "entity_type": a.entity_type,
            "entity_name": a.entity_name,
            "country": a.country,
            "overall": a.overall,
            "geopolitical": a.geopolitical,
            "climate": a.climate,
            "financial": a.financial,
            "cyber": a.cyber,
            "logistics": a.logistics,
            "classification": platform.risk_engine.classify_risk(a.overall),
            "factors": a.factors,
        }
        for a in assessments
    ]


@router.get("/by-country")
async def get_risk_by_country():
    """Get aggregated risk scores by country."""
    platform = get_platform()
    assessments = _score_all_entities(platform)

    by_country: dict[str, dict] = {}
    for a in assessments:
        if a.country not in by_country:
            by_country[a.country] = {
                "country": a.country,
                "entity_count": 0,
                "avg_risk": 0,
                "max_risk": 0,
                "scores": [],
            }
        by_country[a.country]["entity_count"] += 1
        by_country[a.country]["scores"].append(a.overall)

    result = []
    for country, data in by_country.items():
        scores = data.pop("scores")
        data["avg_risk"] = round(sum(scores) / len(scores), 1)
        data["max_risk"] = round(max(scores), 1)
        data["classification"] = platform.risk_engine.classify_risk(data["avg_risk"])
        result.append(data)

    result.sort(key=lambda x: x["avg_risk"], reverse=True)
    return result


@router.get("/alerts")
async def get_risk_alerts():
    """Get active risk alerts for high-risk entities."""
    platform = get_platform()
    assessments = _score_all_entities(platform)

    alerts = []
    for a in assessments:
        if a.overall >= 40:
            severity = "critical" if a.overall >= 60 else "warning"
            for factor in a.factors:
                alerts.append({
                    "severity": severity,
                    "entity_id": a.entity_id,
                    "entity_name": a.entity_name,
                    "entity_type": a.entity_type,
                    "country": a.country,
                    "risk_score": a.overall,
                    "message": factor,
                })

    alerts.sort(key=lambda x: x["risk_score"], reverse=True)
    return alerts


def _score_all_entities(platform):
    """Score all nodes in the network."""
    assessments = []
    for node in platform.graph.get_all_nodes():
        node_type = node.get("node_type", "supplier")
        if node_type in ("supplier", "factory"):
            a = platform.risk_engine.score_supplier(
                supplier_id=node["id"],
                name=node["label"],
                country=node["country"],
                tier=node.get("tier", "tier_1"),
            )
        else:
            a = platform.risk_engine.score_facility(
                facility_id=node["id"],
                name=node["label"],
                country=node["country"],
                facility_type=node_type,
                utilization=node.get("utilization", 0.7),
            )
        assessments.append(a)
    return assessments


def _str_to_uuid(s: str):
    from uuid import UUID
    return UUID(int=hash(s) % (2**128))
