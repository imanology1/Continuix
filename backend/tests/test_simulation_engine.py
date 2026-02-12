"""Tests for the Disruption Simulation Engine."""

import pytest
from app.services.graph_engine import SupplyChainGraph, NodeData, EdgeData
from app.services.twin_engine import DigitalTwin, TwinNodeState, TwinEdgeState
from app.services.simulation_engine import SimulationEngine, DisruptionScenario


@pytest.fixture
def engines():
    graph = SupplyChainGraph()
    twin = DigitalTwin()

    # Build a multi-country network matching the seed data structure
    for nid, label, ntype, country, tier, cap, util, rev, cons, inflow, inv, ss in [
        # Tier 3 raw materials
        ("t3-silicon-tw", "Taiwan Wafers", "supplier", "Taiwan", "tier_3", 5000, 0.88, 12, 0, 0, 20000, 10000),
        ("t3-lithium-au", "Australia Lithium", "supplier", "Australia", "tier_3", 4000, 0.65, 8, 0, 0, 18000, 9000),
        ("t3-rare-earth-cn", "China Rare Earth", "supplier", "China", "tier_3", 6000, 0.82, 15, 0, 0, 25000, 12000),
        ("t3-glass-jp", "Japan Glass", "supplier", "Japan", "tier_3", 3000, 0.70, 6, 0, 0, 12000, 6000),
        # Tier 2 components
        ("t2-chips-tw", "Taiwan Chips", "factory", "Taiwan", "tier_2", 4500, 0.91, 85, 1200, 1100, 9000, 4500),
        ("t2-display-kr", "Korea Display", "factory", "South Korea", "tier_2", 3500, 0.78, 45, 800, 750, 7000, 3500),
        ("t2-battery-cn", "China Battery", "factory", "China", "tier_2", 5500, 0.85, 35, 1500, 1400, 11000, 5500),
        ("t2-pcb-vn", "Vietnam PCB", "factory", "Vietnam", "tier_2", 4000, 0.72, 22, 900, 850, 8000, 4000),
        ("t2-sensor-de", "Germany Sensor", "factory", "Germany", "tier_2", 2000, 0.68, 30, 500, 480, 5000, 2500),
        # Tier 1 assembly
        ("t1-assembly-cn", "China Assembly", "factory", "China", "tier_1", 5000, 0.87, 250, 1400, 1300, 6000, 3000),
        ("t1-assembly-mx", "Mexico Assembly", "factory", "Mexico", "tier_1", 3000, 0.75, 240, 800, 750, 4500, 2200),
        ("t1-assembly-in", "India Assembly", "factory", "India", "tier_1", 2500, 0.70, 230, 600, 550, 4000, 2000),
        # Ports
        ("port-kaohsiung", "Port Kaohsiung", "port", "Taiwan", None, 10000, 0.80, 0, 0, 0, 0, 0),
        ("port-shenzhen", "Port Shenzhen", "port", "China", None, 15000, 0.85, 0, 0, 0, 0, 0),
        # Distribution
        ("dc-us", "US DC", "distribution_center", "United States", None, 8000, 0.65, 500, 2000, 1800, 12000, 6000),
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
        ("r-silicon-tw-chips", "t3-silicon-tw", "t2-chips-tw", 1),
        ("r-lithium-au-battery", "t3-lithium-au", "t2-battery-cn", 18),
        ("r-rare-earth-battery", "t3-rare-earth-cn", "t2-battery-cn", 3),
        ("r-glass-display", "t3-glass-jp", "t2-display-kr", 3),
        ("r-chips-assembly-cn", "t2-chips-tw", "t1-assembly-cn", 3),
        ("r-display-assembly-cn", "t2-display-kr", "t1-assembly-cn", 5),
        ("r-battery-assembly-cn", "t2-battery-cn", "t1-assembly-cn", 2),
        ("r-pcb-assembly-cn", "t2-pcb-vn", "t1-assembly-cn", 4),
        ("r-sensor-assembly-cn", "t2-sensor-de", "t1-assembly-cn", 3),
        ("r-chips-assembly-mx", "t2-chips-tw", "t1-assembly-mx", 18),
        ("r-cn-port-shenzhen", "t1-assembly-cn", "port-shenzhen", 1),
        ("r-shenzhen-la", "port-shenzhen", "dc-us", 14),
        ("r-shenzhen-rotterdam", "port-shenzhen", "dc-us", 28),
        ("r-busan-la", "t2-display-kr", "dc-us", 12),
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
            affected_node_ids=["t1-assembly-cn"],
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


class TestNewPresetScenarios:
    """Tests for the 15 new disruption scenarios."""

    def test_korea_fab_fire(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("korea_fab_fire")
        assert result.disruption_type == "factory_fire"
        assert result.duration_days == 45
        assert result.severity == 0.85

    def test_global_pandemic(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("global_pandemic")
        assert result.disruption_type == "pandemic"
        assert result.duration_days == 120
        assert result.revenue_at_risk_usd >= 0

    def test_china_rare_earth_ban(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("china_rare_earth_ban")
        assert result.disruption_type == "export_controls"
        assert result.duration_days == 365

    def test_logistics_ransomware(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("logistics_ransomware")
        assert result.disruption_type == "ransomware"
        assert result.duration_days == 21

    def test_vietnam_flooding(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("vietnam_flooding")
        assert result.disruption_type == "flooding"
        assert result.duration_days == 30

    def test_malacca_strait_closure(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("malacca_strait_closure")
        assert result.disruption_type == "strait_closure"
        assert result.duration_days == 60

    def test_european_energy_crisis(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("european_energy_crisis")
        assert result.disruption_type == "energy_crisis"
        assert result.duration_days == 150

    def test_mexico_labor_strike(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("mexico_labor_strike")
        assert result.disruption_type == "labor_strike"
        assert result.duration_days == 28

    def test_taiwan_supplier_bankruptcy(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("taiwan_supplier_bankruptcy")
        assert result.disruption_type == "bankruptcy"
        assert result.severity == 1.0
        assert result.duration_days == 180

    def test_india_grid_failure(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("india_grid_failure")
        assert result.disruption_type == "power_grid_failure"
        assert result.duration_days == 14

    def test_panama_canal_drought(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("panama_canal_drought")
        assert result.disruption_type == "drought"
        assert result.duration_days == 90

    def test_us_china_trade_embargo(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("us_china_trade_embargo")
        assert result.disruption_type == "trade_embargo"
        assert result.duration_days == 365

    def test_australia_wildfire(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("australia_wildfire")
        assert result.disruption_type == "wildfire"
        assert result.duration_days == 45

    def test_global_recession(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("global_recession")
        assert result.disruption_type == "demand_collapse"
        assert result.duration_days == 180

    def test_port_cyberattack(self, engines):
        engine, twin, graph = engines
        result = engine.run_preset_scenario("port_cyberattack")
        assert result.disruption_type == "cyberattack"
        assert result.duration_days == 10


class TestTwinResetAfterSimulation:
    def test_twin_resets(self, engines):
        engine, twin, graph = engines
        original_throughput = twin.nodes["t1-assembly-cn"].current_throughput

        scenario = DisruptionScenario(
            disruption_type="factory_fire",
            severity=1.0,
            duration_days=30,
            affected_node_ids=["t1-assembly-cn"],
        )
        engine.run_scenario(scenario, monte_carlo_runs=10)

        # Twin should be reset after simulation
        assert twin.nodes["t1-assembly-cn"].current_throughput == original_throughput
