export interface DashboardMetrics {
  total_suppliers: number;
  total_facilities: number;
  total_routes: number;
  total_products: number;
  avg_risk_score: number;
  revenue_at_risk_usd: number;
  suppliers_at_high_risk: number;
  inventory_health_pct: number;
  avg_lead_time_days: number;
  network_resilience_score: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  country: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  tier?: string;
  is_critical: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  transport_mode: string;
  transit_time_days: number;
  disruption_probability: number;
  is_chokepoint: boolean;
}

export interface NetworkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  critical_paths: string[][];
  single_points_of_failure: string[];
}

export interface RiskScore {
  entity_id: string;
  entity_type: string;
  entity_name: string;
  overall_score: number;
  geopolitical: number;
  climate: number;
  financial: number;
  cyber: number;
  logistics: number;
  trend: string;
}

export interface RiskSummary {
  total_suppliers: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  average_risk_score: number;
  top_risks: RiskScore[];
  risk_by_country: Record<string, number>;
  risk_by_tier: Record<string, number>;
}

export interface SimulationPreset {
  id: string;
  name: string;
  description: string;
  disruption_type: string;
  severity: number;
  duration_days: number;
  affected_countries: string[];
}

export interface SimulationImpact {
  revenue_at_risk_usd: number;
  revenue_at_risk_pct: number;
  production_delay_days: number;
  affected_supplier_count: number;
  affected_facility_count: number;
  affected_route_count: number;
  inventory_depletion_day: number | null;
  customer_fulfillment_risk_pct: number;
  cost_escalation_pct: number;
  recovery_time_days: number;
}

export interface SimulationTimelinePoint {
  day: number;
  inventory_level_pct: number;
  production_capacity_pct: number;
  revenue_impact_usd: number;
  cumulative_loss_usd: number;
}

export interface SimulationResult {
  id: string;
  disruption_type: string;
  severity: number;
  duration_days: number;
  impact: SimulationImpact;
  timeline: SimulationTimelinePoint[];
  recommendations: string[];
  confidence_interval: number;
  computed_at: string;
}

export interface RiskAlert {
  severity: string;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  country: string;
  risk_score: number;
  message: string;
}

export interface CountryExposure {
  country: string;
  node_count: number;
  pct_of_network: number;
  risk_score: number;
  classification: string;
}

export interface InventoryItem {
  node_id: string;
  name: string;
  country: string;
  inventory_level: number;
  safety_stock: number;
  health_pct: number;
  days_of_supply: number | null;
  daily_consumption: number;
  depletion_day: number | null;
  status: string;
}
