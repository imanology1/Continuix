import React from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { SimulationPanel } from "../components/simulation/SimulationPanel";

export function SimulationPage() {
  const { data, loading } = useApi(() => api.simulation.getPresets(), []);

  return (
    <div>
      <div className="page-header">
        <h2>Disruption Simulation</h2>
        <p>
          Model what-if scenarios against your supply chain digital twin.
          Select a preset or configure a custom disruption.
        </p>
      </div>

      {loading || !data ? (
        <div className="loading">
          <div className="spinner" />
          Loading scenarios...
        </div>
      ) : (
        <SimulationPanel presets={data.scenarios} />
      )}
    </div>
  );
}
