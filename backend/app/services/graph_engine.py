"""
Supply Chain Graph Engine

Builds and analyzes the supply chain as a directed graph using NetworkX.
Provides:
- Multi-tier supplier network construction
- Critical path identification
- Single point of failure detection
- Dependency heatmaps
- Failure propagation analysis
"""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

import networkx as nx


@dataclass
class NodeData:
    id: str
    label: str
    node_type: str  # supplier, factory, warehouse, port, distribution_center
    country: str
    region: str
    latitude: float
    longitude: float
    tier: Optional[str] = None
    risk_score: float = 0.0
    capacity: float = 0.0
    utilization: float = 0.0
    is_critical: bool = False


@dataclass
class EdgeData:
    id: str
    source: str
    target: str
    transport_mode: str
    transit_time_days: float
    cost_per_unit: float = 0.0
    capacity: float = 0.0
    disruption_probability: float = 0.05
    is_chokepoint: bool = False


class SupplyChainGraph:
    """
    Directed graph representation of a supply chain network.
    Nodes are suppliers/facilities, edges are transport routes.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, data: NodeData) -> None:
        self.graph.add_node(data.id, **{
            "label": data.label,
            "node_type": data.node_type,
            "country": data.country,
            "region": data.region,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "tier": data.tier,
            "risk_score": data.risk_score,
            "capacity": data.capacity,
            "utilization": data.utilization,
            "is_critical": data.is_critical,
        })

    def add_edge(self, data: EdgeData) -> None:
        self.graph.add_edge(data.source, data.target, **{
            "id": data.id,
            "transport_mode": data.transport_mode,
            "transit_time_days": data.transit_time_days,
            "cost_per_unit": data.cost_per_unit,
            "capacity": data.capacity,
            "disruption_probability": data.disruption_probability,
            "is_chokepoint": data.is_chokepoint,
        })

    def remove_node(self, node_id: str) -> None:
        if self.graph.has_node(node_id):
            self.graph.remove_node(node_id)

    def remove_edge(self, source: str, target: str) -> None:
        if self.graph.has_edge(source, target):
            self.graph.remove_edge(source, target)

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_node(self, node_id: str) -> Optional[dict]:
        if self.graph.has_node(node_id):
            return {"id": node_id, **self.graph.nodes[node_id]}
        return None

    def get_all_nodes(self) -> list[dict]:
        return [{"id": n, **self.graph.nodes[n]} for n in self.graph.nodes]

    def get_all_edges(self) -> list[dict]:
        return [
            {"source": u, "target": v, **self.graph.edges[u, v]}
            for u, v in self.graph.edges
        ]

    # --- Tier Analysis ---

    def get_nodes_by_tier(self, tier: str) -> list[dict]:
        return [
            {"id": n, **self.graph.nodes[n]}
            for n in self.graph.nodes
            if self.graph.nodes[n].get("tier") == tier
        ]

    def get_nodes_by_country(self, country: str) -> list[dict]:
        return [
            {"id": n, **self.graph.nodes[n]}
            for n in self.graph.nodes
            if self.graph.nodes[n].get("country") == country
        ]

    def get_nodes_by_type(self, node_type: str) -> list[dict]:
        return [
            {"id": n, **self.graph.nodes[n]}
            for n in self.graph.nodes
            if self.graph.nodes[n].get("node_type") == node_type
        ]

    # --- Dependency Analysis ---

    def get_upstream_suppliers(self, node_id: str, max_depth: Optional[int] = None) -> list[str]:
        """Get all suppliers feeding into a node (predecessors)."""
        if not self.graph.has_node(node_id):
            return []
        ancestors = nx.ancestors(self.graph, node_id)
        if max_depth is not None:
            ancestors = {
                a for a in ancestors
                if nx.shortest_path_length(self.graph, a, node_id) <= max_depth
            }
        return list(ancestors)

    def get_downstream_dependents(self, node_id: str, max_depth: Optional[int] = None) -> list[str]:
        """Get all nodes that depend on this supplier (successors)."""
        if not self.graph.has_node(node_id):
            return []
        descendants = nx.descendants(self.graph, node_id)
        if max_depth is not None:
            descendants = {
                d for d in descendants
                if nx.shortest_path_length(self.graph, node_id, d) <= max_depth
            }
        return list(descendants)

    def get_dependency_depth(self, node_id: str) -> int:
        """How many tiers deep the dependency chain goes from this node."""
        if not self.graph.has_node(node_id):
            return 0
        descendants = nx.descendants(self.graph, node_id)
        if not descendants:
            return 0
        return max(
            nx.shortest_path_length(self.graph, node_id, d)
            for d in descendants
        )

    # --- Critical Path Analysis ---

    def find_critical_paths(self, source: str, sink: str, weight: str = "transit_time_days") -> list[list[str]]:
        """Find the longest (critical) path between source and sink by weighted attribute."""
        if not (self.graph.has_node(source) and self.graph.has_node(sink)):
            return []
        try:
            all_paths = list(nx.all_simple_paths(self.graph, source, sink))
        except nx.NetworkXError:
            return []

        if not all_paths:
            return []

        def path_weight(path: list[str]) -> float:
            return sum(
                self.graph.edges[path[i], path[i + 1]].get(weight, 0)
                for i in range(len(path) - 1)
            )

        all_paths.sort(key=path_weight, reverse=True)
        return all_paths[:5]

    def find_shortest_supply_path(self, source: str, target: str, weight: str = "transit_time_days") -> Optional[list[str]]:
        """Find lowest-cost/fastest path between two nodes."""
        try:
            return nx.shortest_path(self.graph, source, target, weight=weight)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # --- Vulnerability Analysis ---

    def find_single_points_of_failure(self) -> list[str]:
        """
        Identify nodes whose removal disconnects the graph.
        These are articulation points in the underlying undirected graph.
        """
        undirected = self.graph.to_undirected()
        return list(nx.articulation_points(undirected))

    def find_bridge_routes(self) -> list[tuple[str, str]]:
        """Identify edges whose removal disconnects parts of the network."""
        undirected = self.graph.to_undirected()
        return list(nx.bridges(undirected))

    def calculate_node_criticality(self, node_id: str) -> float:
        """
        Score how critical a node is based on:
        - Degree centrality (connectivity)
        - Betweenness centrality (flow importance)
        - Whether it's a single point of failure
        """
        if not self.graph.has_node(node_id):
            return 0.0

        degree_centrality = nx.degree_centrality(self.graph).get(node_id, 0)
        betweenness = nx.betweenness_centrality(self.graph).get(node_id, 0)
        is_spof = node_id in self.find_single_points_of_failure()

        score = (degree_centrality * 30) + (betweenness * 40) + (30 if is_spof else 0)
        return min(score, 100.0)

    def get_country_concentration(self) -> dict[str, int]:
        """Return count of nodes per country to identify geographic concentration risk."""
        concentration: dict[str, int] = {}
        for n in self.graph.nodes:
            country = self.graph.nodes[n].get("country", "Unknown")
            concentration[country] = concentration.get(country, 0) + 1
        return concentration

    # --- Impact Propagation ---

    def simulate_node_failure(self, failed_node_id: str) -> dict:
        """
        Simulate the removal of a node and measure impact on the network.
        Returns affected downstream nodes and disconnected subgraphs.
        """
        if not self.graph.has_node(failed_node_id):
            return {"affected_nodes": [], "disconnected_components": 0}

        downstream = self.get_downstream_dependents(failed_node_id)

        test_graph = self.graph.copy()
        test_graph.remove_node(failed_node_id)

        undirected = test_graph.to_undirected()
        components = list(nx.connected_components(undirected))

        return {
            "failed_node": failed_node_id,
            "directly_affected": list(self.graph.successors(failed_node_id)),
            "total_downstream_affected": downstream,
            "affected_count": len(downstream),
            "disconnected_components": len(components),
            "original_components": 1 if nx.is_weakly_connected(self.graph) else len(
                list(nx.weakly_connected_components(self.graph))
            ),
        }

    def simulate_region_disruption(self, country: str) -> dict:
        """Simulate all nodes in a country going offline."""
        affected_nodes = self.get_nodes_by_country(country)
        affected_ids = [n["id"] for n in affected_nodes]

        all_downstream = set()
        for node_id in affected_ids:
            all_downstream.update(self.get_downstream_dependents(node_id))
        all_downstream -= set(affected_ids)

        return {
            "disrupted_country": country,
            "directly_affected_nodes": len(affected_ids),
            "downstream_affected_nodes": len(all_downstream),
            "total_impact": len(affected_ids) + len(all_downstream),
            "affected_node_ids": affected_ids,
            "downstream_node_ids": list(all_downstream),
        }

    # --- Metrics ---

    def get_network_metrics(self) -> dict:
        """Compute overall network health and topology metrics."""
        if self.graph.number_of_nodes() == 0:
            return {
                "node_count": 0, "edge_count": 0,
                "density": 0, "is_connected": False,
                "avg_clustering": 0, "avg_path_length": 0,
            }

        undirected = self.graph.to_undirected()
        is_connected = nx.is_connected(undirected)

        avg_path_length = 0.0
        if is_connected and undirected.number_of_nodes() > 1:
            avg_path_length = nx.average_shortest_path_length(undirected)

        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": is_connected,
            "avg_clustering": nx.average_clustering(undirected),
            "avg_path_length": avg_path_length,
            "weakly_connected_components": nx.number_weakly_connected_components(self.graph),
        }

    def calculate_resilience_score(self) -> float:
        """
        Composite resilience score (0-100) based on:
        - Network redundancy (multiple paths)
        - Geographic diversification
        - Low single-point-of-failure count
        - Edge connectivity
        """
        if self.graph.number_of_nodes() < 2:
            return 0.0

        metrics = self.get_network_metrics()
        spof_count = len(self.find_single_points_of_failure())
        country_count = len(self.get_country_concentration())
        node_count = metrics["node_count"]

        # Redundancy: higher density = more alternative paths
        density_score = min(metrics["density"] * 100, 25)

        # Geographic diversity: more countries = less concentration
        geo_score = min((country_count / max(node_count, 1)) * 100, 25)

        # SPOF ratio: fewer SPOFs relative to nodes = more resilient
        spof_ratio = spof_count / max(node_count, 1)
        spof_score = max(0, 25 - (spof_ratio * 100))

        # Connectivity
        connectivity_score = 25 if metrics["is_connected"] else 0

        return round(density_score + geo_score + spof_score + connectivity_score, 1)
