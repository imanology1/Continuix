import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import { DashboardPage } from "./pages/DashboardPage";
import { SimulationPage } from "./pages/SimulationPage";
import { RiskPage } from "./pages/RiskPage";
import { NetworkPage } from "./pages/NetworkPage";
import { SuppliersPage } from "./pages/SuppliersPage";

export default function App() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Continuix</h1>
          <p>Supply Chain Twin</p>
        </div>
        <ul className="sidebar-nav">
          <li>
            <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
                <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
              </svg>
              Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/network" className={({ isActive }) => (isActive ? "active" : "")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="5" r="3" /><circle cx="5" cy="19" r="3" /><circle cx="19" cy="19" r="3" />
                <line x1="12" y1="8" x2="5" y2="16" /><line x1="12" y1="8" x2="19" y2="16" />
              </svg>
              Network
            </NavLink>
          </li>
          <li>
            <NavLink to="/simulation" className={({ isActive }) => (isActive ? "active" : "")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
              Simulation
            </NavLink>
          </li>
          <li>
            <NavLink to="/risk" className={({ isActive }) => (isActive ? "active" : "")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
              Risk Intel
            </NavLink>
          </li>
          <li>
            <NavLink to="/suppliers" className={({ isActive }) => (isActive ? "active" : "")}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                <circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" />
                <path d="M16 3.13a4 4 0 010 7.75" />
              </svg>
              Suppliers
            </NavLink>
          </li>
        </ul>

        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            padding: "1rem 1.5rem",
            borderTop: "1px solid var(--border)",
            fontSize: "0.6875rem",
            color: "var(--text-muted)",
          }}
        >
          <div>v{import.meta.env.VITE_APP_VERSION || "0.1.0"}</div>
          <div style={{ marginTop: "0.25rem" }}>Predictive Risk Intelligence</div>
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/network" element={<NetworkPage />} />
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/suppliers" element={<SuppliersPage />} />
        </Routes>
      </main>
    </div>
  );
}
