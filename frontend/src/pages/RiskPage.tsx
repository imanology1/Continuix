import React from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { RiskDashboard } from "../components/risk/RiskDashboard";
import { MetricCard } from "../components/dashboard/MetricCard";
import { riskColor, formatPct } from "../utils/format";

export function RiskPage() {
  const { data: summary, loading } = useApi(() => api.risk.getSummary(), []);
  const { data: alerts } = useApi(() => api.risk.getAlerts(), []);

  if (loading || !summary) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading risk data...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h2>Risk Intelligence</h2>
        <p>Continuous risk monitoring across geopolitical, climate, financial, cyber, and logistics dimensions</p>
      </div>

      <div className="metrics-grid">
        <MetricCard
          title="Average Risk Score"
          value={summary.average_risk_score.toFixed(1)}
          subtitle={`of ${summary.total_suppliers} entities`}
          color={riskColor(summary.average_risk_score)}
        />
        <MetricCard
          title="High Risk"
          value={summary.high_risk_count.toString()}
          subtitle="entities above 60"
          color="var(--accent-red)"
        />
        <MetricCard
          title="Medium Risk"
          value={summary.medium_risk_count.toString()}
          subtitle="entities 30-60"
          color="var(--accent-amber)"
        />
        <MetricCard
          title="Low Risk"
          value={summary.low_risk_count.toString()}
          subtitle="entities below 30"
          color="var(--accent-green)"
        />
      </div>

      <RiskDashboard summary={summary} alerts={alerts ?? []} />
    </div>
  );
}
