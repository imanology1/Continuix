import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { MetricCard } from "../components/dashboard/MetricCard";
import { RiskBar } from "../components/dashboard/RiskBar";
import { NetworkMap } from "../components/network/NetworkMap";
import {
  formatCurrency,
  formatPct,
  formatNumber,
  riskColor,
  riskBadgeClass,
  riskLabel,
} from "../utils/format";

export function DashboardPage() {
  const { data: metrics, loading: metricsLoading } = useApi(() => api.dashboard.getMetrics(), []);
  const { data: graph, loading: graphLoading } = useApi(() => api.network.getGraph(), []);
  const { data: riskSummary } = useApi(() => api.risk.getSummary(), []);
  const { data: alerts } = useApi(() => api.risk.getAlerts(), []);
  const { data: inventory } = useApi(() => api.dashboard.getInventoryStatus(), []);

  if (metricsLoading || !metrics) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading dashboard...
      </div>
    );
  }

  const countryData = riskSummary
    ? Object.entries(riskSummary.risk_by_country)
        .map(([country, score]) => ({ country, score }))
        .sort((a, b) => b.score - a.score)
        .slice(0, 8)
    : [];

  return (
    <div>
      <div className="page-header">
        <h2>Command Center</h2>
        <p>Real-time supply chain intelligence and risk overview</p>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <MetricCard
          title="Network Resilience"
          value={`${metrics.network_resilience_score.toFixed(0)}/100`}
          subtitle="Composite score"
          color={metrics.network_resilience_score > 50 ? "var(--accent-green)" : "var(--accent-amber)"}
        />
        <MetricCard
          title="Revenue at Risk"
          value={formatCurrency(metrics.revenue_at_risk_usd)}
          subtitle="30-day exposure"
          color="var(--accent-red)"
        />
        <MetricCard
          title="Avg Risk Score"
          value={metrics.avg_risk_score.toFixed(1)}
          subtitle={`${metrics.suppliers_at_high_risk} high-risk suppliers`}
          color={riskColor(metrics.avg_risk_score)}
        />
        <MetricCard
          title="Inventory Health"
          value={formatPct(metrics.inventory_health_pct)}
          subtitle="vs safety stock"
          color={metrics.inventory_health_pct > 80 ? "var(--accent-green)" : "var(--accent-amber)"}
        />
        <MetricCard
          title="Total Suppliers"
          value={formatNumber(metrics.total_suppliers)}
          subtitle={`${metrics.total_facilities} facilities`}
        />
        <MetricCard
          title="Transport Routes"
          value={formatNumber(metrics.total_routes)}
          subtitle={`Avg ${metrics.avg_lead_time_days.toFixed(0)}d lead time`}
        />
      </div>

      {/* Network Map */}
      {graph && !graphLoading && (
        <div className="card content-full" style={{ marginBottom: "2rem", padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "1rem 1.25rem 0" }}>
            <div className="card-title">Global Supply Network</div>
          </div>
          <NetworkMap graph={graph} width={900} height={400} />
        </div>
      )}

      {/* Risk + Alerts */}
      <div className="content-grid">
        <div className="card">
          <div className="card-title">Risk by Country</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={countryData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis type="number" domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} />
              <YAxis type="category" dataKey="country" width={100} stroke="var(--text-muted)" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "0.5rem",
                  fontSize: "0.75rem",
                }}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {countryData.map((entry, i) => (
                  <Cell key={i} fill={riskColor(entry.score)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Active Alerts</div>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            {alerts && alerts.slice(0, 10).map((alert, i) => (
              <div key={i} className="alert-item">
                <div className={`alert-dot ${alert.severity}`} />
                <div>
                  <div style={{ fontWeight: 500, fontSize: "0.8125rem" }}>
                    {alert.entity_name}
                    <span
                      style={{
                        color: "var(--text-muted)",
                        marginLeft: "0.5rem",
                        fontSize: "0.75rem",
                        fontWeight: 400,
                      }}
                    >
                      {alert.country}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    {alert.message}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Inventory Status */}
      {inventory && inventory.length > 0 && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-title">Inventory Burn-Down Status</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Facility</th>
                <th>Country</th>
                <th>Health</th>
                <th>Days of Supply</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {inventory.slice(0, 10).map((item) => (
                <tr key={item.node_id}>
                  <td>{item.name}</td>
                  <td>{item.country}</td>
                  <td>
                    <RiskBar score={100 - item.health_pct} label={formatPct(item.health_pct)} />
                  </td>
                  <td>{item.days_of_supply ? `${item.days_of_supply.toFixed(0)} days` : "N/A"}</td>
                  <td>
                    <span className={`badge badge-${item.status === "healthy" ? "healthy" : item.status === "warning" ? "warning" : "critical"}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
