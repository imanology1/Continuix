"""
Seed Data Service

Generates a realistic demo supply chain for an electronics manufacturer.
Creates a multi-tier network spanning semiconductors, displays, batteries,
and final assembly — representative of real OEM supply chains.
"""

from app.services.graph_engine import SupplyChainGraph, NodeData, EdgeData
from app.services.twin_engine import DigitalTwin, TwinNodeState, TwinEdgeState
from app.services.risk_engine import RiskEngine


def build_demo_supply_chain() -> tuple[SupplyChainGraph, DigitalTwin, RiskEngine]:
    """
    Build a demo supply chain for "Continuix Electronics" — a consumer
    electronics OEM sourcing from multiple tiers globally.
    """
    graph = SupplyChainGraph()
    twin = DigitalTwin()
    risk_engine = RiskEngine()

    # =========================================================
    # TIER 3 — Raw Materials & Wafer Fabs
    # =========================================================

    _add_node(graph, twin, NodeData(
        id="t3-silicon-tw", label="Taiwan Semiconductor Wafers",
        node_type="supplier", country="Taiwan", region="East Asia",
        latitude=24.15, longitude=120.67, tier="tier_3",
        risk_score=45, capacity=50000, utilization=0.88, is_critical=True,
    ), revenue_per_unit=12.0, daily_consumption=0, daily_inflow=0,
       operating_cost=150000, inventory=200000, safety_stock=100000)

    _add_node(graph, twin, NodeData(
        id="t3-silicon-kr", label="Korea Semiconductor Materials",
        node_type="supplier", country="South Korea", region="East Asia",
        latitude=37.56, longitude=126.98, tier="tier_3",
        risk_score=30, capacity=35000, utilization=0.75,
    ), revenue_per_unit=11.5, daily_consumption=0, daily_inflow=0,
       operating_cost=120000, inventory=150000, safety_stock=80000)

    _add_node(graph, twin, NodeData(
        id="t3-lithium-au", label="Australia Lithium Mining",
        node_type="supplier", country="Australia", region="Oceania",
        latitude=-31.95, longitude=115.86, tier="tier_3",
        risk_score=18, capacity=40000, utilization=0.65,
    ), revenue_per_unit=8.0, daily_consumption=0, daily_inflow=0,
       operating_cost=100000, inventory=180000, safety_stock=90000)

    _add_node(graph, twin, NodeData(
        id="t3-rare-earth-cn", label="China Rare Earth Processing",
        node_type="supplier", country="China", region="East Asia",
        latitude=23.13, longitude=113.26, tier="tier_3",
        risk_score=55, capacity=60000, utilization=0.82, is_critical=True,
    ), revenue_per_unit=15.0, daily_consumption=0, daily_inflow=0,
       operating_cost=180000, inventory=250000, safety_stock=120000)

    _add_node(graph, twin, NodeData(
        id="t3-glass-jp", label="Japan Display Glass",
        node_type="supplier", country="Japan", region="East Asia",
        latitude=35.68, longitude=139.69, tier="tier_3",
        risk_score=35, capacity=30000, utilization=0.70,
    ), revenue_per_unit=6.0, daily_consumption=0, daily_inflow=0,
       operating_cost=90000, inventory=120000, safety_stock=60000)

    # =========================================================
    # TIER 2 — Component Manufacturers
    # =========================================================

    _add_node(graph, twin, NodeData(
        id="t2-chips-tw", label="Taiwan Chip Fabrication",
        node_type="factory", country="Taiwan", region="East Asia",
        latitude=24.80, longitude=120.97, tier="tier_2",
        risk_score=48, capacity=45000, utilization=0.91, is_critical=True,
    ), revenue_per_unit=85.0, daily_consumption=1200, daily_inflow=1100,
       operating_cost=350000, inventory=90000, safety_stock=45000)

    _add_node(graph, twin, NodeData(
        id="t2-display-kr", label="Korea Display Manufacturing",
        node_type="factory", country="South Korea", region="East Asia",
        latitude=36.35, longitude=127.38, tier="tier_2",
        risk_score=28, capacity=35000, utilization=0.78,
    ), revenue_per_unit=45.0, daily_consumption=800, daily_inflow=750,
       operating_cost=250000, inventory=70000, safety_stock=35000)

    _add_node(graph, twin, NodeData(
        id="t2-battery-cn", label="China Battery Cell Production",
        node_type="factory", country="China", region="East Asia",
        latitude=30.57, longitude=114.27, tier="tier_2",
        risk_score=42, capacity=55000, utilization=0.85,
    ), revenue_per_unit=35.0, daily_consumption=1500, daily_inflow=1400,
       operating_cost=280000, inventory=110000, safety_stock=55000)

    _add_node(graph, twin, NodeData(
        id="t2-pcb-vn", label="Vietnam PCB Assembly",
        node_type="factory", country="Vietnam", region="Southeast Asia",
        latitude=21.03, longitude=105.85, tier="tier_2",
        risk_score=32, capacity=40000, utilization=0.72,
    ), revenue_per_unit=22.0, daily_consumption=900, daily_inflow=850,
       operating_cost=180000, inventory=80000, safety_stock=40000)

    _add_node(graph, twin, NodeData(
        id="t2-sensor-de", label="Germany Sensor Manufacturing",
        node_type="factory", country="Germany", region="Europe",
        latitude=48.14, longitude=11.58, tier="tier_2",
        risk_score=12, capacity=20000, utilization=0.68,
    ), revenue_per_unit=30.0, daily_consumption=500, daily_inflow=480,
       operating_cost=200000, inventory=50000, safety_stock=25000)

    # =========================================================
    # TIER 1 — Module / Sub-Assembly
    # =========================================================

    _add_node(graph, twin, NodeData(
        id="t1-assembly-cn", label="China Module Assembly",
        node_type="factory", country="China", region="East Asia",
        latitude=22.54, longitude=114.06, tier="tier_1",
        risk_score=40, capacity=50000, utilization=0.87, is_critical=True,
    ), revenue_per_unit=250.0, daily_consumption=1400, daily_inflow=1300,
       operating_cost=500000, inventory=60000, safety_stock=30000)

    _add_node(graph, twin, NodeData(
        id="t1-assembly-mx", label="Mexico Assembly Plant",
        node_type="factory", country="Mexico", region="North America",
        latitude=19.43, longitude=-99.13, tier="tier_1",
        risk_score=30, capacity=30000, utilization=0.75,
    ), revenue_per_unit=240.0, daily_consumption=800, daily_inflow=750,
       operating_cost=350000, inventory=45000, safety_stock=22000)

    _add_node(graph, twin, NodeData(
        id="t1-assembly-in", label="India Assembly Hub",
        node_type="factory", country="India", region="South Asia",
        latitude=12.97, longitude=77.59, tier="tier_1",
        risk_score=35, capacity=25000, utilization=0.70,
    ), revenue_per_unit=230.0, daily_consumption=600, daily_inflow=550,
       operating_cost=250000, inventory=40000, safety_stock=20000)

    # =========================================================
    # LOGISTICS NODES — Ports & Distribution
    # =========================================================

    _add_node(graph, twin, NodeData(
        id="port-kaohsiung", label="Port of Kaohsiung",
        node_type="port", country="Taiwan", region="East Asia",
        latitude=22.62, longitude=120.30, risk_score=42, capacity=100000, utilization=0.80,
    ), revenue_per_unit=0, daily_consumption=0, daily_inflow=0,
       operating_cost=50000, inventory=0, safety_stock=0)

    _add_node(graph, twin, NodeData(
        id="port-shenzhen", label="Port of Shenzhen",
        node_type="port", country="China", region="East Asia",
        latitude=22.50, longitude=114.10, risk_score=38, capacity=150000, utilization=0.85,
    ), revenue_per_unit=0, daily_consumption=0, daily_inflow=0,
       operating_cost=60000, inventory=0, safety_stock=0)

    _add_node(graph, twin, NodeData(
        id="port-busan", label="Port of Busan",
        node_type="port", country="South Korea", region="East Asia",
        latitude=35.10, longitude=129.04, risk_score=22, capacity=120000, utilization=0.75,
    ), revenue_per_unit=0, daily_consumption=0, daily_inflow=0,
       operating_cost=45000, inventory=0, safety_stock=0)

    _add_node(graph, twin, NodeData(
        id="port-la", label="Port of Los Angeles",
        node_type="port", country="United States", region="North America",
        latitude=33.74, longitude=-118.27, risk_score=20, capacity=200000, utilization=0.78,
    ), revenue_per_unit=0, daily_consumption=0, daily_inflow=0,
       operating_cost=70000, inventory=0, safety_stock=0)

    _add_node(graph, twin, NodeData(
        id="port-rotterdam", label="Port of Rotterdam",
        node_type="port", country="Netherlands", region="Europe",
        latitude=51.90, longitude=4.50, risk_score=10, capacity=180000, utilization=0.72,
    ), revenue_per_unit=0, daily_consumption=0, daily_inflow=0,
       operating_cost=55000, inventory=0, safety_stock=0)

    # Distribution Centers
    _add_node(graph, twin, NodeData(
        id="dc-us", label="US Distribution Center",
        node_type="distribution_center", country="United States", region="North America",
        latitude=39.10, longitude=-84.51, risk_score=12, capacity=80000, utilization=0.65,
    ), revenue_per_unit=500.0, daily_consumption=2000, daily_inflow=1800,
       operating_cost=200000, inventory=120000, safety_stock=60000)

    _add_node(graph, twin, NodeData(
        id="dc-eu", label="EU Distribution Center",
        node_type="distribution_center", country="Netherlands", region="Europe",
        latitude=52.09, longitude=5.12, risk_score=10, capacity=60000, utilization=0.60,
    ), revenue_per_unit=520.0, daily_consumption=1200, daily_inflow=1100,
       operating_cost=180000, inventory=90000, safety_stock=45000)

    # =========================================================
    # EDGES — Transport Routes
    # =========================================================

    # Tier 3 → Tier 2
    _add_edge(graph, twin, "r-silicon-tw-chips", "t3-silicon-tw", "t2-chips-tw", "road", 1, 50, 2.0)
    _add_edge(graph, twin, "r-silicon-kr-display", "t3-silicon-kr", "t2-display-kr", "road", 2, 200, 1.5)
    _add_edge(graph, twin, "r-lithium-au-battery", "t3-lithium-au", "t2-battery-cn", "ocean", 18, 8000, 4.0, chokepoint=True, chokepoint_name="Strait of Malacca")
    _add_edge(graph, twin, "r-rare-earth-battery", "t3-rare-earth-cn", "t2-battery-cn", "road", 3, 500, 1.0)
    _add_edge(graph, twin, "r-rare-earth-chips", "t3-rare-earth-cn", "t2-chips-tw", "ocean", 4, 800, 2.5, chokepoint=True, chokepoint_name="Taiwan Strait")
    _add_edge(graph, twin, "r-glass-display", "t3-glass-jp", "t2-display-kr", "ocean", 3, 900, 1.8)

    # Tier 2 → Tier 1
    _add_edge(graph, twin, "r-chips-assembly-cn", "t2-chips-tw", "t1-assembly-cn", "ocean", 3, 700, 3.0, chokepoint=True, chokepoint_name="Taiwan Strait")
    _add_edge(graph, twin, "r-display-assembly-cn", "t2-display-kr", "t1-assembly-cn", "ocean", 5, 2000, 2.5)
    _add_edge(graph, twin, "r-battery-assembly-cn", "t2-battery-cn", "t1-assembly-cn", "road", 2, 300, 1.5)
    _add_edge(graph, twin, "r-pcb-assembly-cn", "t2-pcb-vn", "t1-assembly-cn", "ocean", 4, 1500, 2.0)
    _add_edge(graph, twin, "r-sensor-assembly-cn", "t2-sensor-de", "t1-assembly-cn", "air", 3, 9000, 8.0)

    _add_edge(graph, twin, "r-chips-assembly-mx", "t2-chips-tw", "t1-assembly-mx", "ocean", 18, 12000, 5.0, chokepoint=True, chokepoint_name="Panama Canal")
    _add_edge(graph, twin, "r-battery-assembly-mx", "t2-battery-cn", "t1-assembly-mx", "ocean", 22, 15000, 6.0)
    _add_edge(graph, twin, "r-pcb-assembly-in", "t2-pcb-vn", "t1-assembly-in", "ocean", 6, 3000, 2.5)

    # Tier 1 → Ports
    _add_edge(graph, twin, "r-cn-port-shenzhen", "t1-assembly-cn", "port-shenzhen", "road", 1, 50, 0.5)
    _add_edge(graph, twin, "r-mx-port-la", "t1-assembly-mx", "port-la", "road", 3, 2500, 1.5)

    # Ports → Distribution
    _add_edge(graph, twin, "r-shenzhen-la", "port-shenzhen", "port-la", "ocean", 14, 11000, 3.5)
    _add_edge(graph, twin, "r-shenzhen-rotterdam", "port-shenzhen", "port-rotterdam", "ocean", 28, 18000, 4.0, chokepoint=True, chokepoint_name="Suez Canal")
    _add_edge(graph, twin, "r-la-dc-us", "port-la", "dc-us", "rail", 5, 3500, 2.0)
    _add_edge(graph, twin, "r-rotterdam-dc-eu", "port-rotterdam", "dc-eu", "road", 1, 80, 0.5)
    _add_edge(graph, twin, "r-busan-la", "port-busan", "port-la", "ocean", 12, 9500, 3.0)

    return graph, twin, risk_engine


def _add_node(
    graph: SupplyChainGraph,
    twin: DigitalTwin,
    node_data: NodeData,
    revenue_per_unit: float = 0,
    daily_consumption: float = 0,
    daily_inflow: float = 0,
    operating_cost: float = 0,
    inventory: float = 0,
    safety_stock: float = 0,
) -> None:
    """Add a node to both the graph and the twin."""
    graph.add_node(node_data)
    twin.add_node(TwinNodeState(
        node_id=node_data.id,
        node_type=node_data.node_type,
        max_capacity=node_data.capacity,
        current_throughput=node_data.capacity * node_data.utilization,
        utilization=node_data.utilization,
        inventory_level=inventory,
        safety_stock=safety_stock,
        daily_consumption=daily_consumption,
        daily_inflow=daily_inflow,
        operating_cost_per_day=operating_cost,
        revenue_per_unit=revenue_per_unit,
        risk_score=node_data.risk_score,
        country=node_data.country,
        region=node_data.region,
    ))


def _add_edge(
    graph: SupplyChainGraph,
    twin: DigitalTwin,
    edge_id: str,
    source: str,
    target: str,
    mode: str,
    transit_days: float,
    distance_km: float,
    cost_per_unit: float,
    chokepoint: bool = False,
    chokepoint_name: str = "",
) -> None:
    """Add an edge to both the graph and the twin."""
    graph.add_edge(EdgeData(
        id=edge_id, source=source, target=target,
        transport_mode=mode, transit_time_days=transit_days,
        cost_per_unit=cost_per_unit, is_chokepoint=chokepoint,
    ))
    twin.add_edge(TwinEdgeState(
        edge_id=edge_id, source_id=source, target_id=target,
        transport_mode=mode, base_transit_time_days=transit_days,
        current_transit_time_days=transit_days,
        cost_per_unit=cost_per_unit, is_chokepoint=chokepoint,
    ))
