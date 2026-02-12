"""Supply chain network graph API routes."""

from fastapi import APIRouter

from app.api.dependencies import get_platform
from app.schemas.supply_chain import NetworkGraph, GraphNode, GraphEdge

router = APIRouter(prefix="/network", tags=["network"])


@router.get("/graph", response_model=NetworkGraph)
async def get_network_graph():
    """Get the full supply chain network graph for visualization."""
    platform = get_platform()

    nodes = []
    for n in platform.graph.get_all_nodes():
        nodes.append(GraphNode(
            id=n["id"],
            label=n["label"],
            type=n["node_type"],
            country=n["country"],
            latitude=n["latitude"],
            longitude=n["longitude"],
            risk_score=n.get("risk_score", 0),
            tier=n.get("tier"),
            is_critical=n.get("is_critical", False),
        ))

    edges = []
    for e in platform.graph.get_all_edges():
        edges.append(GraphEdge(
            id=e.get("id", f"{e['source']}-{e['target']}"),
            source=e["source"],
            target=e["target"],
            transport_mode=e["transport_mode"],
            transit_time_days=e["transit_time_days"],
            disruption_probability=e.get("disruption_probability", 0.05),
            is_chokepoint=e.get("is_chokepoint", False),
        ))

    spofs = platform.graph.find_single_points_of_failure()

    # Find critical paths from deepest tier to distribution centers
    critical_paths = []
    tier3_nodes = platform.graph.get_nodes_by_type("supplier")
    dc_nodes = platform.graph.get_nodes_by_type("distribution_center")
    for t3 in tier3_nodes[:3]:
        for dc in dc_nodes[:2]:
            path = platform.graph.find_shortest_supply_path(t3["id"], dc["id"])
            if path and len(path) > 2:
                critical_paths.append(path)

    return NetworkGraph(
        nodes=nodes,
        edges=edges,
        critical_paths=critical_paths,
        single_points_of_failure=spofs,
    )


@router.get("/metrics")
async def get_network_metrics():
    """Get network topology and health metrics."""
    platform = get_platform()
    metrics = platform.graph.get_network_metrics()
    resilience = platform.graph.calculate_resilience_score()
    concentration = platform.graph.get_country_concentration()

    return {
        **metrics,
        "resilience_score": resilience,
        "country_concentration": concentration,
    }


@router.get("/vulnerabilities")
async def get_network_vulnerabilities():
    """Identify network vulnerabilities: SPOFs, bridges, concentrations."""
    platform = get_platform()

    spofs = platform.graph.find_single_points_of_failure()
    bridges = platform.graph.find_bridge_routes()
    concentration = platform.graph.get_country_concentration()

    # Analyze each SPOF
    spof_details = []
    for node_id in spofs:
        node = platform.graph.get_node(node_id)
        impact = platform.graph.simulate_node_failure(node_id)
        if node:
            spof_details.append({
                "node_id": node_id,
                "name": node.get("label", "Unknown"),
                "country": node.get("country", "Unknown"),
                "type": node.get("node_type", "Unknown"),
                "downstream_affected": impact["affected_count"],
                "criticality": platform.graph.calculate_node_criticality(node_id),
            })

    # Find over-concentrated countries
    total_nodes = platform.graph.node_count
    high_concentration = {
        country: count
        for country, count in concentration.items()
        if count / total_nodes > 0.15
    }

    return {
        "single_points_of_failure": spof_details,
        "bridge_routes": [
            {"source": s, "target": t} for s, t in bridges
        ],
        "geographic_concentration": high_concentration,
        "total_nodes": total_nodes,
    }
