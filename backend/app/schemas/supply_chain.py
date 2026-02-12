"""Pydantic schemas for API request/response serialization."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Supplier ---

class SupplierBase(BaseModel):
    name: str
    tier: str
    country: str
    region: str
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    annual_capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    lead_time_days: Optional[float] = None
    reliability_score: float = 0.9
    annual_revenue_usd: Optional[float] = None
    credit_rating: Optional[str] = None
    is_critical: bool = False
    tags: list[str] = []


class SupplierCreate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: UUID
    overall_risk_score: float = 0.0
    geopolitical_risk: float = 0.0
    climate_risk: float = 0.0
    financial_risk: float = 0.0
    cyber_risk: float = 0.0
    logistics_risk: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Facility ---

class FacilityBase(BaseModel):
    name: str
    facility_type: str
    country: str
    region: str
    city: Optional[str] = None
    latitude: float
    longitude: float
    supplier_id: Optional[UUID] = None
    max_throughput: Optional[float] = None
    throughput_unit: Optional[str] = None
    current_utilization: float = 0.7
    operating_cost_per_unit: Optional[float] = None


class FacilityCreate(FacilityBase):
    pass


class FacilityResponse(FacilityBase):
    id: UUID
    downtime_risk: float = 0.0
    natural_hazard_exposure: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Transport Route ---

class TransportRouteBase(BaseModel):
    origin_facility_id: UUID
    destination_facility_id: UUID
    transport_mode: str
    transit_time_days: float
    distance_km: Optional[float] = None
    cost_per_unit: Optional[float] = None
    max_capacity: Optional[float] = None
    disruption_probability: float = 0.05
    passes_through_chokepoint: bool = False
    chokepoint_name: Optional[str] = None
    waypoints: list[dict] = []


class TransportRouteCreate(TransportRouteBase):
    pass


class TransportRouteResponse(TransportRouteBase):
    id: UUID
    congestion_risk: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Product ---

class ProductBase(BaseModel):
    name: str
    sku: str
    category: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_revenue: Optional[float] = None
    lead_time_days: Optional[float] = None
    is_critical: bool = False


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Inventory ---

class InventoryBase(BaseModel):
    facility_id: UUID
    product_id: UUID
    quantity_on_hand: float = 0
    safety_stock_level: float = 0
    reorder_point: float = 0
    max_capacity: Optional[float] = None
    daily_consumption_rate: float = 0


class InventoryCreate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: UUID
    last_replenished: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Simulation ---

class SimulationRequest(BaseModel):
    disruption_type: str
    affected_region: Optional[str] = None
    affected_country: Optional[str] = None
    affected_supplier_ids: list[UUID] = []
    affected_facility_ids: list[UUID] = []
    affected_route_ids: list[UUID] = []
    duration_days: int = Field(ge=1, le=365, default=30)
    severity: float = Field(ge=0.0, le=1.0, default=0.5)
    demand_change_pct: float = Field(ge=-1.0, le=5.0, default=0.0)
    monte_carlo_runs: int = Field(ge=1, le=10000, default=500)


class SimulationImpact(BaseModel):
    revenue_at_risk_usd: float
    revenue_at_risk_pct: float
    production_delay_days: float
    affected_supplier_count: int
    affected_facility_count: int
    affected_route_count: int
    inventory_depletion_day: Optional[int] = None
    customer_fulfillment_risk_pct: float
    cost_escalation_pct: float
    recovery_time_days: float


class SimulationTimelinePoint(BaseModel):
    day: int
    inventory_level_pct: float
    production_capacity_pct: float
    revenue_impact_usd: float
    cumulative_loss_usd: float


class SimulationResult(BaseModel):
    id: str
    disruption_type: str
    severity: float
    duration_days: int
    impact: SimulationImpact
    timeline: list[SimulationTimelinePoint]
    affected_suppliers: list[SupplierResponse]
    alternative_suppliers: list[SupplierResponse]
    confidence_interval: float
    recommendations: list[str]
    computed_at: datetime


# --- Risk ---

class RiskScore(BaseModel):
    entity_id: UUID
    entity_type: str  # supplier, facility, route
    entity_name: str
    overall_score: float
    geopolitical: float
    climate: float
    financial: float
    cyber: float
    logistics: float
    trend: str  # increasing, stable, decreasing


class RiskSummary(BaseModel):
    total_suppliers: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
    top_risks: list[RiskScore]
    risk_by_country: dict[str, float]
    risk_by_tier: dict[str, float]


# --- Network Graph ---

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # supplier, facility, warehouse, port
    country: str
    latitude: float
    longitude: float
    risk_score: float
    tier: Optional[str] = None
    is_critical: bool = False


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    transport_mode: str
    transit_time_days: float
    disruption_probability: float
    is_chokepoint: bool = False


class NetworkGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    critical_paths: list[list[str]]
    single_points_of_failure: list[str]


# --- Dashboard ---

class DashboardMetrics(BaseModel):
    total_suppliers: int
    total_facilities: int
    total_routes: int
    total_products: int
    avg_risk_score: float
    revenue_at_risk_usd: float
    suppliers_at_high_risk: int
    inventory_health_pct: float
    avg_lead_time_days: float
    network_resilience_score: float  # 0-100
