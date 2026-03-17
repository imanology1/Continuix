import React, { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import type { SimulationPreset, SimulationResult } from "../../types/api";
import { formatCurrency, formatPct } from "../../utils/format";
import { api } from "../../services/api";

interface SimulationPanelProps {
  presets: SimulationPreset[];
}

export function SimulationPanel({ presets }: SimulationPanelProps) {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  const runScenario = async (presetId: string) => {
    setLoading(true);
    setSelectedPreset(presetId);
    try {
      const data = await api.simulation.runPreset(presetId);
      setResult(data);
    } catch (e) {
      console.error("Simulation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Scenario selection */}
      <div className="scenario-grid" style={{ marginBottom: "2rem" }}>
        {presets.map((preset) => (
          <div
            key={preset.id}
            className="scenario-card"
            style={{
              borderColor: selectedPreset === preset.id ? "var(--accent-cyan)" : undefined,
            }}
            onClick={() => runScenario(preset.id)}
          >
            <h4>{preset.name}</h4>
            <p>{preset.description}</p>
            <div className="scenario-meta">
              <span>Severity: {(preset.severity * 100).toFixed(0)}%</span>
              <span>Duration: {preset.duration_days}d</span>
              {preset.affected_countries.length > 0 && (
                <span>{preset.affected_countries.join(", ")}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="loading">
          <div className="spinner" />
          Running simulation...
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div>
          <h3 style={{ marginBottom: "1rem" }}>Impact Analysis</h3>

          <div className="impact-grid">
            <ImpactCard
              label="Revenue at Risk"
              value={formatCurrency(result.impact.revenue_at_risk_usd)}
              color="var(--accent-red)"
            />
            <ImpactCard
              label="Revenue Impact"
              value={formatPct(result.impact.revenue_at_risk_pct)}
              color="var(--accent-red)"
            />
            <ImpactCard
              label="Recovery Time"
              value={`${result.impact.recovery_time_days.toFixed(0)}d`}
              color="var(--accent-amber)"
            />
            <ImpactCard
              label="Cost Escalation"
              value={formatPct(result.impact.cost_escalation_pct)}
              color="var(--accent-amber)"
            />
            <ImpactCard
              label="Affected Suppliers"
              value={result.impact.affected_supplier_count.toString()}
              color="var(--accent-purple)"
            />
            <ImpactCard
              label="Fulfillment Risk"
              value={formatPct(result.impact.customer_fulfillment_risk_pct)}
              color="var(--accent-red)"
            />
          </div>

          {/* Timeline charts */}
          <div className="content-grid" style={{ marginTop: "1.5rem" }}>
            <div className="card">
              <div className="card-title">Production Capacity Over Time</div>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={result.timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-secondary)",
                      border: "1px solid var(--border)",
                      borderRadius: "0.5rem",
                      fontSize: "0.75rem",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="production_capacity_pct"
                    stroke="var(--accent-blue)"
                    fill="rgba(59,130,246,0.1)"
                    name="Capacity %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <div className="card-title">Cumulative Revenue Loss</div>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={result.timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-secondary)",
                      border: "1px solid var(--border)",
                      borderRadius: "0.5rem",
                      fontSize: "0.75rem",
                    }}
                    formatter={(value: number) => [formatCurrency(value), "Cumulative Loss"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="cumulative_loss_usd"
                    stroke="var(--accent-red)"
                    fill="rgba(239,68,68,0.1)"
                    name="Cumulative Loss"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="card" style={{ marginTop: "1.5rem" }}>
              <div className="card-title">Recommendations</div>
              <ul className="rec-list">
                {result.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ImpactCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="impact-card">
      <div className="label">{label}</div>
      <div className="value" style={{ color }}>
        {value}
      </div>
    </div>
  );
}
