import React from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { RiskBar } from "../components/dashboard/RiskBar";
import { riskBadgeClass, riskLabel, tierLabel } from "../utils/format";

export function SuppliersPage() {
  const { data: suppliers, loading } = useApi(() => api.suppliers.list(), []);

  if (loading || !suppliers) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading suppliers...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Supplier Registry</h2>
        <p>Multi-tier supplier network with risk profiles and dependency analysis</p>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Supplier</th>
              <th>Tier</th>
              <th>Country</th>
              <th>Risk Score</th>
              <th>Geopolitical</th>
              <th>Climate</th>
              <th>Financial</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {(suppliers as any[]).map((s) => (
              <tr key={s.id}>
                <td>
                  <span style={{ fontWeight: 500 }}>{s.name}</span>
                  {s.is_critical && (
                    <span
                      className="badge badge-critical"
                      style={{ marginLeft: "0.5rem" }}
                    >
                      Critical
                    </span>
                  )}
                </td>
                <td>{tierLabel(s.tier)}</td>
                <td>{s.country}</td>
                <td style={{ minWidth: 150 }}>
                  <RiskBar score={s.overall_risk_score} />
                </td>
                <td>{s.geopolitical_risk.toFixed(0)}</td>
                <td>{s.climate_risk.toFixed(0)}</td>
                <td>{s.financial_risk.toFixed(0)}</td>
                <td>
                  <span className={`badge ${riskBadgeClass(s.overall_risk_score)}`}>
                    {riskLabel(s.overall_risk_score)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
