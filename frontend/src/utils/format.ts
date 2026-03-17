export function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 1 });
}

export function formatPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function riskColor(score: number): string {
  if (score >= 60) return "var(--accent-red)";
  if (score >= 30) return "var(--accent-amber)";
  return "var(--accent-green)";
}

export function riskLabel(score: number): string {
  if (score >= 60) return "High";
  if (score >= 30) return "Medium";
  return "Low";
}

export function riskBadgeClass(score: number): string {
  if (score >= 60) return "badge-critical";
  if (score >= 30) return "badge-warning";
  return "badge-healthy";
}

export function tierLabel(tier: string | undefined): string {
  if (!tier) return "N/A";
  return tier.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function nodeTypeColor(type: string): string {
  switch (type) {
    case "supplier": return "var(--accent-purple)";
    case "factory": return "var(--accent-blue)";
    case "warehouse": return "var(--accent-green)";
    case "port": return "var(--accent-cyan)";
    case "distribution_center": return "var(--accent-amber)";
    default: return "var(--text-muted)";
  }
}
