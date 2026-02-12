"""Tests for the Disruption Simulation Engine."""

import pytest
from app.services.graph_engine import SupplyChainGraph, NodeData, EdgeData
from app.services.twin_engine import DigitalTwin, TwinNodeState, TwinEdgeState
from app.services.simulation_engine import SimulationEngine, DisruptionScenario


@pytest.fixture
def engines():
    graph = SupplyChainGraph()
    twin = DigitalTwin()

    # Build a small but realistic network
    for nid, label, ntype, country, tier, cap, util, rev, cons, inflow, inv, ss in [
        ("s1", "Taiwan Chips", "supplier", "Taiwan", "tier_2", 5000, 0.9, 80, 0, 0, 20000, 10000),
        ("s2", "Korea Display", "supplier", "South Korea", "tier_2", 3000, 0.75, 40, 0, 0, 15000, 8000),
        ("f1", "China Assembly", "factory", "China", "tier_1", 4000, 0.85, 200, 800, 750, 5000, 2500),
        ("dc1", "US DC", "distribution_center", "United States", None, 6000, 0.6, 400, 1500, 1400, 50000, 25000),
    ]:
        graph.add_node(NodeData(
            id=nid, label=label, node_type=ntype, country=country,
            region="Test", latitude=0, longitude=0, tier=tier,
            risk_score=30, capacity=cap, utilization=util,
        ))
        twin.add_node(TwinNodeState(
            node_id=nid, node_type=ntype,
            max_capacity=cap, current_throughput=cap * util,
            utilization=util, inventory_level=inv, safety_stock=ss,
            daily_consumption=cons, daily_inflow=inflow,
            revenue_per_unit=rev, country=country, region="Test",
        ))

    for eid, src, tgt, days in [
        ("r1", "s1", "f1", 3), ("r2", "s2", "f1", 5), ("r3", "f1", "dc1", 14),
    ]:
        graph.add_edge(EdgeData(id=eid, source=src, target=tgt, transport_mode="ocean", transit_time_days=days))
        twin.add_edge(TwinEdgeState(
            edge_id=eid, source_id=src, target_id=tgt,
            transport_mode="ocean", base_transit_time_days=days, current_transit_time_days=days,
        ))

    return SimulationEngine(twin, graph), twin, graph


class TestSimulationExecution:
    def test_run_scenario(self, engines):
        engine, twin, graph = engines
        scenario = DisruptionScenario(
            disruption_type="earthquake",
            severity=0.7,
            duration_days=30,
            affected_countries=["Taiwan"],
        )
        result = engine.run_scenario(scenario, monte_carlo_runs=50)

        assert result.scenario_id
        assert result.disruption_type == "earthquake"
        assert result.duration_days == 30
        assert result.revenue_at_risk_usd >= 0
        assert len(result.daily_snapshots) > 0

    def test_run_sanctions_scenario(self, engines):
        engine, twin, graph = engines
        scenario = DisruptionScenario(
            disruption_type="sanctions",
            severity=0.6,
            duration_days=90,
            affected_countries=["China"],
        )
        result = engine.run_scenario(scenario, monte_carlo_runs=50)

        assert result.affected_supplier_count >= 0 or result.affected_facility_count >= 0
        assert result.cost_escalation_pct > 0

    def test_recommendations_generated(self, engines):
        engine, twin, graph = engines
        scenario = DisruptionScenario(
            disruption_type="strait_closure",
            severity=0.9,
            duration_days=60,
            affected_countries=["Taiwan"],
        )
        result = engine.run_scenario(scenario, monte_carlo_runs=50)
        assert len(result.recommendations) > 0

    def test_monte_carlo_confidence(self, engines):
        engine, twin, graph = engines
        scenario = DisruptionScenario(
            disruption_type="port_congestion",
            severity=0.5,
            duration_days=14,
            affected_node_ids=["f1"],
        )
        result = engine.run_scenario(scenario, monte_carlo_runs=100)
        assert result.p10_revenue_loss <= result.p50_revenue_loss
        assert result.p50_revenue_loss <= result.p90_revenue_loss


class TestPresetScenarios:
    def test_taiwan_strait(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("taiwan_strait_closure")
        assert result.disruption_type == "strait_closure"
        assert result.duration_days == 90

    def test_suez_canal(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("suez_canal_blockage")
        assert result.disruption_type == "canal_blockage"

    def test_japan_earthquake(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("japan_earthquake")
        assert result.disruption_type == "earthquake"

    def test_demand_surge(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("demand_surge")
        assert result.disruption_type == "demand_surge"

    def test_invalid_preset_raises(self, engines):
        engine, twin, graph = engines
        with pytest.raises(ValueError, match="Unknown preset"):
            engine.run_preset_scenario("nonexistent_scenario")


class TestTwinResetAfterSimulation:
    def test_twin_resets(self, engines):
        engine, twin, graph = engines
        original_throughput = twin.nodes["f1"].current_throughput

        scenario = DisruptionScenario(
            disruption_type="factory_fire",
            severity=1.0,
            duration_days=30,
            affected_node_ids=["f1"],
        )
        engine.run_scenario(scenario, monte_carlo_runs=10)

        # Twin should be reset after simulation
        assert twin.nodes["f1"].current_throughput == original_throughput
