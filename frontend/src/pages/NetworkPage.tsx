import React from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import { NetworkMap } from "../components/network/NetworkMap";
import { MetricCard } from "../components/dashboard/MetricCard";
import { riskColor, riskBadgeClass, riskLabel } from "../utils/format";
import { RiskBar } from "../components/dashboard/RiskBar";

export function NetworkPage() {
  const { data: graph, loading } = useApi(() => api.network.getGraph(), []);
  const { data: vulnerabilities } = useApi(() => api.network.getVulnerabilities(), []);
  const { data: metrics } = useApi(() => api.network.getMetrics(), []);

  if (loading || !graph) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading network...
      </div>
    );
  }

  const spofs = (vulnerabilities as any)?.single_points_of_failure ?? [];
  const bridges = (vulnerabilities as any)?.bridge_routes ?? [];
  const concentration = (vulnerabilities as any)?.geographic_concentration ?? {};
  const netMetrics = metrics as any;

  return (
    <div>
      <div className="page-header">
        <h2>Supply Network</h2>
        <p>Multi-tier supplier network graph with dependency and vulnerability analysis</p>
      </div>

      {netMetrics && (
        <div className="metrics-grid">
          <MetricCard
            title="Nodes"
            value={netMetrics.node_count?.toString() ?? "0"}
            subtitle="Suppliers, facilities, ports"
          />
          <MetricCard
            title="Edges"
            value={netMetrics.edge_count?.toString() ?? "0"}
            subtitle="Transport routes"
          />
          <MetricCard
            title="Resilience"
            value={`${(netMetrics.resilience_score ?? 0).toFixed(0)}/100`}
            color={(netMetrics.resilience_score ?? 0) > 50 ? "var(--accent-green)" : "var(--accent-amber)"}
          />
          <MetricCard
            title="SPOFs"
            value={spofs.length.toString()}
            subtitle="Single points of failure"
            color={spofs.length > 3 ? "var(--accent-red)" : "var(--accent-amber)"}
          />
        </div>
      )}

      {/* Network visualization */}
      <div className="card" style={{ marginBottom: "2rem", padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "1rem 1.25rem 0" }}>
          <div className="card-title">
            Interactive Network Map &mdash; {graph.nodes.length} nodes, {graph.edges.length} routes
          </div>
        </div>
        <NetworkMap graph={graph} width={900} height={450} />
      </div>

      <div className="content-grid">
        {/* Single Points of Failure */}
        <div className="card">
          <div className="card-title">Single Points of Failure</div>
          {spofs.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", padding: "1rem 0" }}>
              No single points of failure detected
            </p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Node</th>
                  <th>Country</th>
                  <th>Downstream Impact</th>
                  <th>Criticality</th>
                </tr>
              </thead>
              <tbody>
                {spofs.map((spof: any) => (
                  <tr key={spof.node_id}>
                    <td>{spof.name}</td>
                    <td>{spof.country}</td>
                    <td>{spof.downstream_affected} nodes</td>
                    <td>
                      <RiskBar score={spof.criticality} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Geographic Concentration */}
        <div className="card">
          <div className="card-title">Geographic Concentration Risk</div>
          {Object.keys(concentration).length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", padding: "1rem 0" }}>
              No concentration risks detected
            </p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Country</th>
                  <th>Nodes</th>
                  <th>% of Network</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(concentration).map(([country, count]: [string, any]) => (
                  <tr key={country}>
                    <td>{country}</td>
                    <td>{count}</td>
                    <td>{((count / (netMetrics?.node_count ?? 1)) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Critical paths */}
      {graph.critical_paths.length > 0 && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="card-title">Critical Supply Paths</div>
          {graph.critical_paths.map((path, i) => (
            <div
              key={i}
              style={{
                padding: "0.5rem 0",
                borderBottom: i < graph.critical_paths.length - 1 ? "1px solid var(--border)" : undefined,
                fontSize: "0.8125rem",
              }}
            >
              {path.map((nodeId, j) => {
                const node = graph.nodes.find((n) => n.id === nodeId);
                return (
                  <span key={nodeId}>
                    <span style={{ color: "var(--accent-cyan)" }}>{node?.label ?? nodeId}</span>
                    {j < path.length - 1 && (
                      <span style={{ color: "var(--text-muted)", margin: "0 0.5rem" }}>&rarr;</span>
                    )}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
