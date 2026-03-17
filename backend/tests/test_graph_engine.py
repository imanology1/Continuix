"""Tests for the Supply Chain Graph Engine."""

import pytest
from app.services.graph_engine import SupplyChainGraph, NodeData, EdgeData


@pytest.fixture
def sample_graph():
    g = SupplyChainGraph()
    g.add_node(NodeData(
        id="s1", label="Supplier A", node_type="supplier",
        country="Taiwan", region="East Asia", latitude=24.0, longitude=120.0,
        tier="tier_2", risk_score=45, capacity=10000, utilization=0.8, is_critical=True,
    ))
    g.add_node(NodeData(
        id="s2", label="Supplier B", node_type="supplier",
        country="South Korea", region="East Asia", latitude=37.0, longitude=127.0,
        tier="tier_2", risk_score=25, capacity=8000, utilization=0.7,
    ))
    g.add_node(NodeData(
        id="f1", label="Factory X", node_type="factory",
        country="China", region="East Asia", latitude=22.5, longitude=114.0,
        tier="tier_1", risk_score=35, capacity=15000, utilization=0.85,
    ))
    g.add_node(NodeData(
        id="dc1", label="US Distribution", node_type="distribution_center",
        country="United States", region="North America", latitude=39.0, longitude=-84.0,
        risk_score=10, capacity=20000, utilization=0.6,
    ))
    g.add_edge(EdgeData(id="e1", source="s1", target="f1", transport_mode="ocean", transit_time_days=3))
    g.add_edge(EdgeData(id="e2", source="s2", target="f1", transport_mode="ocean", transit_time_days=5))
    g.add_edge(EdgeData(id="e3", source="f1", target="dc1", transport_mode="ocean", transit_time_days=14))
    return g


class TestGraphConstruction:
    def test_add_nodes(self, sample_graph):
        assert sample_graph.node_count == 4

    def test_add_edges(self, sample_graph):
        assert sample_graph.edge_count == 3

    def test_get_node(self, sample_graph):
        node = sample_graph.get_node("s1")
        assert node is not None
        assert node["label"] == "Supplier A"
        assert node["country"] == "Taiwan"

    def test_get_nonexistent_node(self, sample_graph):
        assert sample_graph.get_node("nonexistent") is None


class TestDependencyAnalysis:
    def test_upstream_suppliers(self, sample_graph):
        upstream = sample_graph.get_upstream_suppliers("dc1")
        assert "f1" in upstream
        assert "s1" in upstream
        assert "s2" in upstream

    def test_downstream_dependents(self, sample_graph):
        downstream = sample_graph.get_downstream_dependents("s1")
        assert "f1" in downstream
        assert "dc1" in downstream

    def test_dependency_depth(self, sample_graph):
        depth = sample_graph.get_dependency_depth("s1")
        assert depth == 2  # s1 -> f1 -> dc1

    def test_upstream_with_max_depth(self, sample_graph):
        upstream = sample_graph.get_upstream_suppliers("dc1", max_depth=1)
        assert "f1" in upstream
        assert "s1" not in upstream  # s1 is 2 hops away


class TestVulnerabilityAnalysis:
    def test_single_points_of_failure(self, sample_graph):
        spofs = sample_graph.find_single_points_of_failure()
        assert "f1" in spofs  # f1 is the only path from suppliers to DC

    def test_node_criticality(self, sample_graph):
        criticality = sample_graph.calculate_node_criticality("f1")
        assert criticality > 0

    def test_country_concentration(self, sample_graph):
        concentration = sample_graph.get_country_concentration()
        assert concentration["Taiwan"] == 1
        assert concentration["China"] == 1

    def test_node_failure_simulation(self, sample_graph):
        impact = sample_graph.simulate_node_failure("f1")
        assert impact["affected_count"] == 1  # dc1 is downstream
        assert "dc1" in impact["directly_affected"]

    def test_region_disruption(self, sample_graph):
        impact = sample_graph.simulate_region_disruption("China")
        assert impact["directly_affected_nodes"] == 1  # f1
        assert impact["downstream_affected_nodes"] == 1  # dc1


class TestPathAnalysis:
    def test_shortest_path(self, sample_graph):
        path = sample_graph.find_shortest_supply_path("s1", "dc1")
        assert path == ["s1", "f1", "dc1"]

    def test_no_path(self, sample_graph):
        path = sample_graph.find_shortest_supply_path("dc1", "s1")
        assert path is None  # reverse direction


class TestNetworkMetrics:
    def test_metrics(self, sample_graph):
        metrics = sample_graph.get_network_metrics()
        assert metrics["node_count"] == 4
        assert metrics["edge_count"] == 3
        assert metrics["density"] > 0

    def test_resilience_score(self, sample_graph):
        score = sample_graph.calculate_resilience_score()
        assert 0 <= score <= 100
