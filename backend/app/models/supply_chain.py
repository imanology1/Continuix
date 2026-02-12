"""
Core supply chain domain models.

These represent the nodes and edges of the supply chain graph:
- Suppliers, Facilities, Warehouses, Ports (nodes)
- Transport Routes (edges)
- Products, BOM, Inventory (attributes)
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey,
    Enum, Text, JSON, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- Enums ---

class SupplierTier(str, enum.Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    TIER_4 = "tier_4"


class FacilityType(str, enum.Enum):
    FACTORY = "factory"
    WAREHOUSE = "warehouse"
    PORT = "port"
    DISTRIBUTION_CENTER = "distribution_center"
    RAW_MATERIAL_SOURCE = "raw_material_source"


class TransportMode(str, enum.Enum):
    OCEAN = "ocean"
    AIR = "air"
    RAIL = "rail"
    ROAD = "road"
    MULTIMODAL = "multimodal"


class RiskCategory(str, enum.Enum):
    GEOPOLITICAL = "geopolitical"
    CLIMATE = "climate"
    FINANCIAL = "financial"
    CYBER = "cyber"
    LOGISTICS = "logistics"
    OPERATIONAL = "operational"


class DisruptionType(str, enum.Enum):
    # Geopolitical
    SANCTIONS = "sanctions"
    TRADE_EMBARGO = "trade_embargo"
    STRAIT_CLOSURE = "strait_closure"
    TARIFF = "tariff"
    EXPORT_CONTROLS = "export_controls"
    REGIME_CHANGE = "regime_change"
    # Natural disaster
    EARTHQUAKE = "earthquake"
    HURRICANE = "hurricane"
    FLOODING = "flooding"
    WILDFIRE = "wildfire"
    DROUGHT = "drought"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    # Operational
    FACTORY_FIRE = "factory_fire"
    LABOR_STRIKE = "labor_strike"
    BANKRUPTCY = "bankruptcy"
    MASS_RESIGNATION = "mass_resignation"
    # Cyber
    CYBERATTACK = "cyberattack"
    RANSOMWARE = "ransomware"
    # Logistics
    PORT_CONGESTION = "port_congestion"
    CANAL_BLOCKAGE = "canal_blockage"
    SHIPPING_SHORTAGE = "shipping_shortage"
    # Demand
    DEMAND_SURGE = "demand_surge"
    DEMAND_COLLAPSE = "demand_collapse"
    # Pandemic / Health
    PANDEMIC = "pandemic"
    # Infrastructure / Energy
    POWER_GRID_FAILURE = "power_grid_failure"
    ENERGY_CRISIS = "energy_crisis"
    # Regulatory
    REGULATORY_BAN = "regulatory_ban"
    # Financial
    CURRENCY_CRISIS = "currency_crisis"


# --- Models ---

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    tier = Column(Enum(SupplierTier), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False)
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)

    # Capacity and performance
    annual_capacity = Column(Float)
    capacity_unit = Column(String(50))
    lead_time_days = Column(Float)
    reliability_score = Column(Float, default=0.9)  # 0-1

    # Financial
    annual_revenue_usd = Column(Float)
    credit_rating = Column(String(10))

    # Risk
    overall_risk_score = Column(Float, default=0.0)  # 0-100
    geopolitical_risk = Column(Float, default=0.0)
    climate_risk = Column(Float, default=0.0)
    financial_risk = Column(Float, default=0.0)
    cyber_risk = Column(Float, default=0.0)
    logistics_risk = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)
    criticality_reason = Column(Text)

    # Metadata
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    facilities = relationship("Facility", back_populates="supplier", cascade="all, delete-orphan")
    products_supplied = relationship("SupplierProduct", back_populates="supplier")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    name = Column(String(255), nullable=False)
    facility_type = Column(Enum(FacilityType), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False)
    city = Column(String(100))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Capacity
    max_throughput = Column(Float)
    throughput_unit = Column(String(50))
    current_utilization = Column(Float, default=0.7)  # 0-1

    # Cost
    operating_cost_per_unit = Column(Float)
    currency = Column(String(3), default="USD")

    # Risk
    downtime_risk = Column(Float, default=0.0)  # 0-1
    natural_hazard_exposure = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="facilities")
    inventory = relationship("Inventory", back_populates="facility", cascade="all, delete-orphan")


class TransportRoute(Base):
    __tablename__ = "transport_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)
    destination_facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)
    transport_mode = Column(Enum(TransportMode), nullable=False)

    # Performance
    transit_time_days = Column(Float, nullable=False)
    distance_km = Column(Float)
    cost_per_unit = Column(Float)
    currency = Column(String(3), default="USD")
    max_capacity = Column(Float)
    capacity_unit = Column(String(50))

    # Risk
    disruption_probability = Column(Float, default=0.05)  # 0-1
    congestion_risk = Column(Float, default=0.0)

    # Route details
    waypoints = Column(JSON, default=list)  # [{lat, lng, name}]
    passes_through_chokepoint = Column(Boolean, default=False)
    chokepoint_name = Column(String(100))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    origin = relationship("Facility", foreign_keys=[origin_facility_id])
    destination = relationship("Facility", foreign_keys=[destination_facility_id])


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False)
    category = Column(String(100))
    unit_cost = Column(Float)
    unit_revenue = Column(Float)
    currency = Column(String(3), default="USD")
    lead_time_days = Column(Float)
    is_critical = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    suppliers = relationship("SupplierProduct", back_populates="product")
    bom_entries = relationship("BillOfMaterials", back_populates="product",
                               foreign_keys="BillOfMaterials.product_id")


class SupplierProduct(Base):
    """Junction: which suppliers provide which products."""
    __tablename__ = "supplier_products"
    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    unit_cost = Column(Float)
    lead_time_days = Column(Float)
    min_order_quantity = Column(Integer)
    max_capacity = Column(Float)
    is_primary = Column(Boolean, default=False)

    supplier = relationship("Supplier", back_populates="products_supplied")
    product = relationship("Product", back_populates="suppliers")


class BillOfMaterials(Base):
    """BOM: what components make up a product."""
    __tablename__ = "bill_of_materials"
    __table_args__ = (
        UniqueConstraint("product_id", "component_id", name="uq_bom_entry"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity_required = Column(Float, nullable=False)

    product = relationship("Product", foreign_keys=[product_id], back_populates="bom_entries")
    component = relationship("Product", foreign_keys=[component_id])


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("facility_id", "product_id", name="uq_facility_product_inv"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    quantity_on_hand = Column(Float, default=0)
    safety_stock_level = Column(Float, default=0)
    reorder_point = Column(Float, default=0)
    max_capacity = Column(Float)
    daily_consumption_rate = Column(Float, default=0)
    unit = Column(String(50), default="units")

    last_replenished = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    facility = relationship("Facility", back_populates="inventory")
    product = relationship("Product")
