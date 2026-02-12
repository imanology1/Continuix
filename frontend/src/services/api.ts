const API_BASE = "/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  dashboard: {
    getMetrics: () => fetchJson<import("../types/api").DashboardMetrics>("/dashboard/metrics"),
    getCountryExposure: () => fetchJson<import("../types/api").CountryExposure[]>("/dashboard/country-exposure"),
    getInventoryStatus: () => fetchJson<import("../types/api").InventoryItem[]>("/dashboard/inventory-status"),
  },

  network: {
    getGraph: () => fetchJson<import("../types/api").NetworkGraph>("/network/graph"),
    getMetrics: () => fetchJson<Record<string, unknown>>("/network/metrics"),
    getVulnerabilities: () => fetchJson<Record<string, unknown>>("/network/vulnerabilities"),
  },

  suppliers: {
    list: (params?: Record<string, string>) => {
      const query = params ? "?" + new URLSearchParams(params).toString() : "";
      return fetchJson<unknown[]>(`/suppliers${query}`);
    },
    get: (id: string) => fetchJson<Record<string, unknown>>(`/suppliers/${id}`),
    getDependencies: (id: string) => fetchJson<Record<string, unknown>>(`/suppliers/${id}/dependencies`),
  },

  simulation: {
    getPresets: () =>
      fetchJson<{ scenarios: import("../types/api").SimulationPreset[] }>("/simulation/presets"),
    runPreset: (id: string) =>
      fetchJson<import("../types/api").SimulationResult>(`/simulation/presets/${id}`, {
        method: "POST",
      }),
    run: (body: Record<string, unknown>) =>
      fetchJson<import("../types/api").SimulationResult>("/simulation/run", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },

  risk: {
    getSummary: () => fetchJson<import("../types/api").RiskSummary>("/risk/summary"),
    getScores: () => fetchJson<unknown[]>("/risk/scores"),
    getAlerts: () => fetchJson<import("../types/api").RiskAlert[]>("/risk/alerts"),
    getByCountry: () => fetchJson<unknown[]>("/risk/by-country"),
  },

  optimization: {
    analyze: (body: Record<string, unknown>) =>
      fetchJson<Record<string, unknown>>("/optimization/analyze", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    getAlternatives: (nodeId: string) =>
      fetchJson<Record<string, unknown>>(`/optimization/alternatives/${nodeId}`),
  },
};
