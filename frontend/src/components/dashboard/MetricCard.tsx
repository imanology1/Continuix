import React from "react";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
}

export function MetricCard({ title, value, subtitle, color }: MetricCardProps) {
  return (
    <div className="card">
      <div className="card-title">{title}</div>
      <div className="card-value" style={color ? { color } : undefined}>
        {value}
      </div>
      {subtitle && <div className="card-subtitle">{subtitle}</div>}
    </div>
  );
}
