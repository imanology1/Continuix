"""Tests for the Digital Twin Engine."""

import pytest
from app.services.twin_engine import DigitalTwin, TwinNodeState, TwinEdgeState


@pytest.fixture
def twin():
    t = DigitalTwin()
    t.add_node(TwinNodeState(
        node_id="factory-1", node_type="factory",
        max_capacity=1000, current_throughput=800, utilization=0.8,
        inventory_level=5000, safety_stock=3000,
        daily_consumption=100, daily_inflow=90,
        operating_cost_per_day=10000, revenue_per_unit=50,
        country="China", region="East Asia",
    ))
    t.add_node(TwinNodeState(
        node_id="warehouse-1", node_type="warehouse",
        max_capacity=500, current_throughput=0, utilization=0,
        inventory_level=10000, safety_stock=5000,
        daily_consumption=200, daily_inflow=180,
        operating_cost_per_day=5000, revenue_per_unit=0,
        country="United States", region="North America",
    ))
    t.add_edge(TwinEdgeState(
        edge_id="route-1", source_id="factory-1", target_id="warehouse-1",
        transport_mode="ocean", base_transit_time_days=14,
        current_transit_time_days=14,
    ))
    return t


class TestTwinState:
    def test_add_nodes(self, twin):
        assert len(twin.nodes) == 2

    def test_add_edges(self, twin):
        assert len(twin.edges) == 1

    def test_snapshot_capture(self, twin):
        snap = twin.capture_snapshot()
        assert snap.day == 0
        assert snap.total_production_capacity_pct > 0

    def test_reset(self, twin):
        twin.apply_node_disruption("factory-1", 0.5)
        assert twin.nodes["factory-1"].capacity_reduction == 0.5
        twin.reset()
        assert twin.nodes["factory-1"].capacity_reduction == 0


class TestDisruptions:
    def test_node_disruption(self, twin):
        twin.apply_node_disruption("factory-1", 0.8)
        node = twin.nodes["factory-1"]
        assert node.capacity_reduction == 0.8
        assert node.current_throughput <= node.max_capacity * 0.2

    def test_full_shutdown(self, twin):
        twin.apply_node_disruption("factory-1", 1.0, operational=False)
        assert not twin.nodes["factory-1"].is_operational

    def test_edge_disruption(self, twin):
        twin.apply_edge_disruption("route-1", delay_factor=3.0)
        edge = twin.edges["route-1"]
        assert edge.delay_factor == 3.0
        assert edge.current_transit_time_days == 42.0  # 14 * 3

    def test_region_disruption(self, twin):
        affected = twin.apply_region_disruption("China", 0.7, severity=0.8)
        assert "factory-1" in affected
        assert twin.nodes["factory-1"].capacity_reduction > 0


class TestSimulationRun:
    def test_step(self, twin):
        snap = twin.step()
        assert snap.day == 1

    def test_run_multi_day(self, twin):
        snapshots = twin.run(30)
        assert len(snapshots) == 30
        assert snapshots[-1].day == 30

    def test_recovery_after_disruption(self, twin):
        twin.apply_node_disruption("factory-1", 0.5)
        twin.nodes["factory-1"].recovery_rate = 0.1
        snapshots = twin.run(10)
        # Capacity should gradually recover
        final = twin.nodes["factory-1"]
        assert final.capacity_reduction < 0.5

    def test_inventory_depletion(self, twin):
        twin.apply_node_disruption("factory-1", 1.0, operational=False)
        snapshots = twin.run(60)
        # Factory inventory should decrease when not operational
        assert twin.nodes["factory-1"].inventory_level < 5000


class TestAnalytics:
    def test_production_loss(self, twin):
        twin.apply_node_disruption("factory-1", 0.5)
        loss = twin.get_production_loss()
        assert loss["production_loss"] > 0
        assert loss["loss_pct"] > 0

    def test_revenue_impact(self, twin):
        twin.apply_node_disruption("factory-1", 0.5)
        impact = twin.get_revenue_impact()
        assert impact["daily_revenue_loss"] > 0

    def test_no_impact_at_baseline(self, twin):
        loss = twin.get_production_loss()
        assert loss["production_loss"] == 0
