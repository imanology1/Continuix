import React, { useState, useMemo } from "react";
import type { NetworkGraph, GraphNode } from "../../types/api";
import { nodeTypeColor, riskColor } from "../../utils/format";

interface NetworkMapProps {
  graph: NetworkGraph;
  width?: number;
  height?: number;
}

// Simple Mercator-like projection for positioning nodes on a rectangular map
function project(lat: number, lng: number, width: number, height: number) {
  const x = ((lng + 180) / 360) * width;
  const latRad = (lat * Math.PI) / 180;
  const mercN = Math.log(Math.tan(Math.PI / 4 + latRad / 2));
  const y = height / 2 - (mercN / Math.PI) * (height / 2) * 0.8;
  return { x, y };
}

export function NetworkMap({ graph, width = 900, height = 450 }: NetworkMapProps) {
  const [hovered, setHovered] = useState<GraphNode | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    for (const node of graph.nodes) {
      positions[node.id] = project(node.latitude, node.longitude, width, height);
    }
    return positions;
  }, [graph.nodes, width, height]);

  const spofSet = useMemo(() => new Set(graph.single_points_of_failure), [graph]);

  return (
    <div className="network-container" style={{ width, height, position: "relative" }}>
      {/* Edges as SVG lines */}
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", top: 0, left: 0, zIndex: 1 }}
      >
        {graph.edges.map((edge) => {
          const src = nodePositions[edge.source];
          const tgt = nodePositions[edge.target];
          if (!src || !tgt) return null;
          return (
            <line
              key={edge.id}
              x1={src.x}
              y1={src.y}
              x2={tgt.x}
              y2={tgt.y}
              stroke={edge.is_chokepoint ? "rgba(239,68,68,0.4)" : "rgba(100,116,139,0.25)"}
              strokeWidth={edge.is_chokepoint ? 2 : 1}
              strokeDasharray={edge.is_chokepoint ? "4,4" : undefined}
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {graph.nodes.map((node) => {
        const pos = nodePositions[node.id];
        if (!pos) return null;
        const isCritical = node.is_critical || spofSet.has(node.id);
        const size = isCritical ? 14 : 10;
        return (
          <div
            key={node.id}
            className={`network-node${isCritical ? " critical" : ""}`}
            style={{
              left: pos.x,
              top: pos.y,
              width: size,
              height: size,
              background: nodeTypeColor(node.type),
              border: `2px solid ${isCritical ? riskColor(node.risk_score) : "transparent"}`,
            }}
            onMouseEnter={(e) => {
              setHovered(node);
              setMousePos({ x: e.clientX, y: e.clientY });
            }}
            onMouseLeave={() => setHovered(null)}
          />
        );
      })}

      {/* Tooltip */}
      {hovered && (
        <div
          className="network-tooltip"
          style={{
            left: Math.min(
              (nodePositions[hovered.id]?.x ?? 0) + 16,
              width - 200
            ),
            top: Math.max((nodePositions[hovered.id]?.y ?? 0) - 30, 10),
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{hovered.label}</div>
          <div>Country: {hovered.country}</div>
          <div>Type: {hovered.type.replace("_", " ")}</div>
          {hovered.tier && <div>Tier: {hovered.tier.replace("_", " ")}</div>}
          <div style={{ color: riskColor(hovered.risk_score) }}>
            Risk: {hovered.risk_score.toFixed(0)}
          </div>
          {hovered.is_critical && (
            <div style={{ color: "var(--accent-red)", marginTop: "0.25rem" }}>
              CRITICAL NODE
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          bottom: 8,
          left: 8,
          display: "flex",
          gap: "0.75rem",
          fontSize: "0.625rem",
          color: "var(--text-muted)",
          background: "rgba(15,23,42,0.9)",
          padding: "0.375rem 0.625rem",
          borderRadius: "0.375rem",
        }}
      >
        {[
          { label: "Supplier", color: "var(--accent-purple)" },
          { label: "Factory", color: "var(--accent-blue)" },
          { label: "Port", color: "var(--accent-cyan)" },
          { label: "DC", color: "var(--accent-amber)" },
        ].map((item) => (
          <span key={item.label} style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: item.color,
                display: "inline-block",
              }}
            />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}
