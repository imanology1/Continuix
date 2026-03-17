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
  PieChart,
  Pie,
} from "recharts";
import type { RiskSummary, RiskAlert } from "../../types/api";
import { RiskBar } from "../dashboard/RiskBar";
import { riskColor, riskBadgeClass, riskLabel } from "../../utils/format";

interface RiskDashboardProps {
  summary: RiskSummary;
  alerts: RiskAlert[];
}

export function RiskDashboard({ summary, alerts }: RiskDashboardProps) {
  const pieData = [
    { name: "High", value: summary.high_risk_count, fill: "var(--accent-red)" },
    { name: "Medium", value: summary.medium_risk_count, fill: "var(--accent-amber)" },
    { name: "Low", value: summary.low_risk_count, fill: "var(--accent-green)" },
  ];

  const countryData = Object.entries(summary.risk_by_country)
    .map(([country, score]) => ({ country, score }))
    .sort((a, b) => b.score - a.score);

  return (
    <div>
      {/* Distribution */}
      <div className="content-grid" style={{ marginBottom: "2rem" }}>
        <div className="card">
          <div className="card-title">Risk Distribution</div>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
              >
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: "0.5rem",
                  fontSize: "0.75rem",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", justifyContent: "center", gap: "1.5rem", marginTop: "0.5rem" }}>
            {pieData.map((d) => (
              <span
                key={d.name}
                style={{ display: "flex", alignItems: "center", gap: "0.375rem", fontSize: "0.8125rem" }}
              >
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: d.fill }} />
                {d.name}: {d.value}
              </span>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Risk by Country</div>
          <ResponsiveContainer width="100%" height={300}>
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
      </div>

      {/* Top risks table */}
      <div className="content-grid">
        <div className="card">
          <div className="card-title">Top Risk Entities</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Type</th>
                <th>Overall</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {summary.top_risks.slice(0, 8).map((risk) => (
                <tr key={risk.entity_id}>
                  <td>{risk.entity_name}</td>
                  <td style={{ textTransform: "capitalize" }}>{risk.entity_type}</td>
                  <td>
                    <RiskBar score={risk.overall_score} />
                  </td>
                  <td>
                    <span className={`badge ${riskBadgeClass(risk.overall_score)}`}>
                      {riskLabel(risk.overall_score)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-title">Active Risk Alerts</div>
          {alerts.length === 0 ? (
            <p style={{ color: "var(--text-muted)", padding: "1rem", fontSize: "0.8125rem" }}>
              No active alerts
            </p>
          ) : (
            <div style={{ maxHeight: 400, overflowY: "auto" }}>
              {alerts.slice(0, 15).map((alert, i) => (
                <div key={i} className="alert-item">
                  <div className={`alert-dot ${alert.severity}`} />
                  <div>
                    <div style={{ fontWeight: 500, fontSize: "0.8125rem" }}>
                      {alert.entity_name}
                      <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem", fontWeight: 400, fontSize: "0.75rem" }}>
                        {alert.country}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.125rem" }}>
                      {alert.message}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
