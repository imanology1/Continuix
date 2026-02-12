import React from "react";
import { riskColor } from "../../utils/format";

interface RiskBarProps {
  score: number;
  label?: string;
}

export function RiskBar({ score, label }: RiskBarProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
      {label && (
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", minWidth: "80px" }}>
          {label}
        </span>
      )}
      <div className="risk-bar" style={{ flex: 1 }}>
        <div
          className="risk-bar-fill"
          style={{
            width: `${Math.min(score, 100)}%`,
            background: riskColor(score),
          }}
        />
      </div>
      <span style={{ fontSize: "0.75rem", fontWeight: 600, color: riskColor(score), minWidth: "30px" }}>
        {score.toFixed(0)}
      </span>
    </div>
  );
}
