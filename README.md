# Continuix — Resilient Supply Chain Twin

Predictive supply chain risk intelligence platform that creates a real-time digital twin of multi-tier supplier networks. Simulates disruptions, forecasts impact with Monte Carlo confidence intervals, and optimizes resilience through alternative sourcing strategies.

Built for manufacturing, automotive, pharma, aerospace, and energy companies managing complex global supply chains.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Core Engines](#core-engines)
- [Risk Intelligence System](#risk-intelligence-system)
- [External Data Sources](#external-data-sources)
- [API Reference](#api-reference)
- [Frontend Dashboard](#frontend-dashboard)
- [Demo Data](#demo-data)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Testing](#testing)
- [Technology Stack](#technology-stack)

---

## Overview

Continuix models your entire supply chain as a directed graph, wraps it in a computational digital twin that evolves daily, and lets you run what-if disruption scenarios before they happen. The platform scores risk across five dimensions using data from the World Bank, IMF, UNDP, and Eurostat, covering 199 countries.

**What it does:**

- Maps multi-tier supplier networks with dependency tracing and chokepoint detection
- Runs disruption simulations (20 preset scenarios, 28 disruption types) with P10/P50/P90 confidence intervals
- Scores risk across geopolitical, climate, financial, cyber, and logistics dimensions for 199 countries
- Pulls live data from 5 external APIs (World Bank, IMF, UNDP HDI, Eurostat) with manual override support
- Recommends alternative suppliers, safety stock adjustments, and sourcing strategy shifts

---

## Key Features

| Feature | Detail |
|---------|--------|
| Multi-tier graph modeling | Directed graph via NetworkX — trace dependencies from raw materials through distribution |
| Digital twin simulation | Living replica with daily state evolution, capacity/inventory/throughput modeling |
| Monte Carlo forecasting | 1,000-iteration confidence intervals for revenue impact, production delays, recovery time |
| 20 preset scenarios | Taiwan Strait closure, Suez blockage, global pandemic, ransomware attacks, and more |
| 28 disruption types | Geopolitical, natural disaster, operational, cyber, logistics, and demand categories |
| 199-country risk database | Calibrated baseline scores with regional defaults and income-group classification |
| 5 live API integrations | World Bank WGI/LPI, IMF DataMapper, UNDP HDI, Eurostat |
| Flexible risk calculator | Manual data entry with 20+ indicators, weighted normalization, full calculation transparency |
| Alternative sourcing optimizer | Multi-objective scoring across cost, lead time, capacity, and risk |
| Interactive dashboard | React/TypeScript frontend with geographic network visualization, charts, and alerts |

---

## Architecture

```
continuix/
├── backend/                    Python/FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── dashboard.py        Executive metrics & inventory status
│   │   │   │   ├── network.py          Graph visualization & vulnerability analysis
│   │   │   │   ├── suppliers.py        Supplier CRUD & dependency tracing
│   │   │   │   ├── simulation.py       Disruption simulation & presets
│   │   │   │   ├── risk.py             Risk scoring & alerts
│   │   │   │   ├── risk_data.py        Country data, manual entry, external refresh
│   │   │   │   └── optimization.py     Alternative sourcing analysis
│   │   │   └── dependencies.py         Platform singleton (graph + twin + risk engine)
│   │   ├── core/
│   │   │   ├── config.py               Settings (risk weights, simulation params)
│   │   │   └── database.py             SQLAlchemy async engine
│   │   ├── models/
│   │   │   └── supply_chain.py         Domain models & enums (28 disruption types)
│   │   ├── schemas/
│   │   │   └── supply_chain.py         Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── graph_engine.py         Supply chain graph (NetworkX directed graph)
│   │   │   ├── twin_engine.py          Digital twin state modeling & daily evolution
│   │   │   ├── simulation_engine.py    Monte Carlo disruption simulation (20 presets)
│   │   │   ├── risk_engine.py          Weighted composite risk scoring
│   │   │   ├── risk_calculator.py      Flexible calculator from raw indicators
│   │   │   ├── country_baseline.py     199-country risk database
│   │   │   ├── external_data.py        World Bank, IMF, UNDP, Eurostat API client
│   │   │   ├── optimization_engine.py  Multi-objective alternative sourcing
│   │   │   └── seed_data.py            Demo electronics OEM supply chain
│   │   └── main.py                     FastAPI app with lifespan & CORS
│   ├── tests/                          135 tests across 7 test files
│   ├── requirements.txt
│   ├── pytest.ini
│   └── Dockerfile
│
├── frontend/                   React 19 / TypeScript dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx       Executive command center
│   │   │   ├── NetworkPage.tsx         Supply network graph & vulnerabilities
│   │   │   ├── SimulationPage.tsx      What-if scenario runner
│   │   │   ├── RiskPage.tsx            Risk intelligence dashboard
│   │   │   └── SuppliersPage.tsx       Supplier registry & profiles
│   │   ├── components/
│   │   │   ├── dashboard/              MetricCard, RiskBar
│   │   │   ├── network/               NetworkMap (SVG Mercator projection)
│   │   │   ├── simulation/            SimulationPanel (Recharts timeline)
│   │   │   └── risk/                  RiskDashboard (pie, bar, alerts)
│   │   ├── services/api.ts            API client for all endpoints
│   │   ├── hooks/useApi.ts            Generic data-fetching hook
│   │   ├── types/api.ts               TypeScript interfaces
│   │   ├── utils/format.ts            Formatting utilities
│   │   ├── App.tsx                    Router & sidebar navigation
│   │   └── index.css                  Dark theme design system
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf                     Production reverse proxy
│   └── Dockerfile                     Multi-stage build + nginx
│
├── docker-compose.yml          Backend + Frontend + PostgreSQL
└── .gitignore
```

---

## Core Engines

### Supply Chain Graph Engine

`graph_engine.py` — Directed graph (NetworkX) modeling multi-tier supplier networks.

| Capability | Method |
|-----------|--------|
| Dependency tracing | `get_upstream_suppliers()`, `get_downstream_dependents()` |
| Critical path identification | `find_critical_paths()` |
| Single-point-of-failure detection | `find_single_points_of_failure()` |
| Bridge route detection | `find_bridge_routes()` |
| Node criticality scoring | `calculate_node_criticality()` |
| Failure propagation | `simulate_node_failure()`, `simulate_region_disruption()` |
| Resilience scoring | `calculate_resilience_score()` |
| Network topology metrics | `get_network_metrics()` |

### Digital Twin Engine

`twin_engine.py` — Living computational replica of the supply chain.

Each node carries dynamic state: capacity utilization, inventory level, throughput rate, and cost multiplier. The twin evolves daily through the `step()` method, modeling:

- **Disruption application**: Capacity reduction, delay injection, cost escalation
- **Recovery modeling**: Gradual capacity restoration at configurable recovery rates
- **Inventory depletion**: Daily consumption against finite stock
- **Cascading effects**: Upstream disruptions propagate downstream through the graph

Key analytics: `get_inventory_depletion_day()`, `get_production_loss()`, `get_revenue_impact()`

### Disruption Simulation Engine

`simulation_engine.py` — Runs what-if scenarios with Monte Carlo confidence intervals.

**28 Disruption Types** organized across 6 categories:

| Category | Types |
|----------|-------|
| Geopolitical | Sanctions, trade embargo, strait closure, tariff, export controls, regime change |
| Natural Disaster | Earthquake, hurricane, flooding, wildfire, drought, volcanic eruption |
| Operational | Factory fire, labor strike, bankruptcy, mass resignation |
| Cyber | Cyberattack, ransomware |
| Logistics | Port congestion, canal blockage, shipping shortage |
| Economic | Demand surge, demand collapse, pandemic, power grid failure, energy crisis, regulatory ban, currency crisis |

Each type has a calibrated disruption profile with `capacity_reduction_range`, `delay_factor_range`, `recovery_rate`, and `cost_escalation`.

**20 Preset Scenarios:**

| # | Scenario | Duration | Severity |
|---|----------|----------|----------|
| 1 | Taiwan Strait Closure | 90 days | Critical |
| 2 | Suez Canal Blockage | 14 days | Major |
| 3 | Japan Earthquake | 60 days | Major |
| 4 | China Trade Sanctions | 180 days | Critical |
| 5 | Demand Surge (+50%) | 45 days | Moderate |
| 6 | Korea Fab Fire | 120 days | Major |
| 7 | Global Pandemic | 180 days | Critical |
| 8 | China Rare Earth Ban | 365 days | Critical |
| 9 | Logistics Ransomware | 14 days | Major |
| 10 | Vietnam Flooding | 30 days | Moderate |
| 11 | Malacca Strait Closure | 60 days | Major |
| 12 | European Energy Crisis | 180 days | Major |
| 13 | Mexico Labor Strike | 30 days | Moderate |
| 14 | Taiwan Supplier Bankruptcy | 90 days | Major |
| 15 | India Grid Failure | 14 days | Moderate |
| 16 | Panama Canal Drought | 90 days | Major |
| 17 | US-China Trade Embargo | 365 days | Critical |
| 18 | Australia Wildfire | 45 days | Moderate |
| 19 | Global Recession | 365 days | Major |
| 20 | Port Cyberattack | 21 days | Major |

### Optimization Engine

`optimization_engine.py` — Multi-objective alternative sourcing.

Scores replacement suppliers across four dimensions:
- **Cost** (0.25 weight) — Unit cost competitiveness
- **Lead time** (0.25 weight) — Days to delivery
- **Capacity** (0.25 weight) — Available throughput headroom
- **Risk** (0.25 weight) — Country + supplier risk composite

Also provides inventory adjustment recommendations (safety stock, reorder points) and strategic sourcing shifts (dual-source, nearshore, regional diversification).

---

## Risk Intelligence System

### Weighted Composite Scoring

Risk is computed as a weighted average across five dimensions:

```
Overall Risk = Geopolitical × 0.25
             + Climate      × 0.20
             + Financial    × 0.20
             + Cyber        × 0.15
             + Logistics    × 0.20
```

All scores are on a 0-100 scale (higher = more risk). Classification thresholds: Low (0-29), Medium (30-59), High (60-100).

### 199-Country Baseline Database

`country_baseline.py` provides calibrated risk scores for 199 countries across all UN regions:

| Region | Countries | Sub-regions |
|--------|-----------|-------------|
| Europe | 47 | Northern, Western, Southern, Eastern |
| Asia | 49 | East, Southeast, South, Central, West Asia |
| Africa | 54 | North, West, East, Central, Southern |
| Americas | 35 | North, Central, Caribbean, South America |
| Oceania | 14 | Oceania, Pacific Islands |

Each country profile includes: ISO-3 code, region/sub-region, income group (high/upper-middle/lower-middle/low), landlocked flag, small-island flag, and all five risk dimension scores.

20 regional defaults fill gaps for any country not individually profiled.

### Flexible Risk Calculator

`risk_calculator.py` accepts 20+ raw indicator inputs and computes normalized risk scores with full transparency:

| Dimension | Input Indicators |
|-----------|-----------------|
| Geopolitical | Political stability (-2.5 to 2.5), govt effectiveness, conflict intensity (0-10), sanctions flag, fragile state index (0-120) |
| Climate | Vulnerability (0-100), readiness (0-100), hazard frequency, flood/earthquake/cyclone risk (0-10) |
| Financial | Inflation %, GDP growth %, sovereign credit rating (AAA-D), debt-to-GDP %, currency volatility, HDI (0-1), unemployment % |
| Cyber | Cybersecurity index (0-100), internet penetration %, breach frequency |
| Logistics | LPI (1-5), port efficiency (0-100), infrastructure quality (1-7), customs efficiency (1-5) |

The calculator shows exactly which inputs contributed to each score, reports data completeness (0-100%), and falls back to country baseline defaults for missing values.

---

## External Data Sources

`external_data.py` fetches live data from 5 public APIs:

| Source | Indicators | Coverage | Frequency | Risk Dimension |
|--------|-----------|----------|-----------|----------------|
| **World Bank WGI** | Political Stability (PV.EST), Govt Effectiveness (GE.EST) | 190+ countries | Annual | Geopolitical |
| **World Bank LPI** | Logistics Performance Index (LP.LPI.OVRL.XQ) | 160+ countries | Biennial | Logistics |
| **IMF DataMapper** | Consumer Price Inflation (PCPIPCH), Real GDP Growth (NGDP_RPCH) | 190+ countries | Semi-annual | Financial |
| **UNDP HDI** | Human Development Index (0-1) | 191 countries | Annual | Financial, Geopolitical |
| **Eurostat** | Unemployment Rate, HICP Inflation | EU-27 + EEA | Monthly | Financial |

**Manual upload supported** (no public REST API):
- **ND-GAIN** — Climate vulnerability and readiness scores (181 countries)
- **ITU GCI** — Global Cybersecurity Index (194 countries)

Features:
- TTL-based caching (default 24h) with per-country invalidation
- Parallel async fetching (all sources queried concurrently per country)
- Manual override support — set any dimension score directly
- Blended scoring — API data merged with manual overrides

---

## API Reference

26 REST endpoints across 7 route groups. All endpoints are prefixed with `/api/v1`.

### Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | Executive dashboard — suppliers, facilities, risk scores, resilience score, inventory health |
| GET | `/country-exposure` | Supply chain exposure by country with entity count and risk classification |
| GET | `/inventory-status` | Inventory health across all facilities with depletion day predictions |

### Network (`/api/v1/network`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph` | Full supply chain graph (nodes + edges) for visualization |
| GET | `/metrics` | Network topology metrics — node/edge count, resilience score, diameter |
| GET | `/vulnerabilities` | SPOFs, bridge routes, geographic concentration risk |

### Suppliers (`/api/v1/suppliers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all suppliers (filter by tier, country, criticality) |
| GET | `/{supplier_id}` | Detailed supplier profile with risk factors |
| GET | `/{supplier_id}/dependencies` | Upstream and downstream dependency tree |

### Simulation (`/api/v1/simulation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/run` | Run a custom disruption scenario with Monte Carlo simulation |
| GET | `/presets` | List all 20 preset disruption scenarios |
| POST | `/presets/{scenario_id}` | Run a preset scenario against the digital twin |

### Risk Intelligence (`/api/v1/risk`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/summary` | Aggregated risk summary — high/medium/low counts, by country, by tier |
| GET | `/scores` | Risk scores for every entity with classification and factors |
| GET | `/by-country` | Country-level risk aggregation with max/avg scores |
| GET | `/alerts` | Active risk alerts for entities scoring >= 40 |

### Risk Data Management (`/api/v1/risk-data`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/countries` | Browse 199 countries (filter by region, search by name/ISO) |
| GET | `/countries/{name}` | Country detail — baseline scores, overrides, metadata |
| GET | `/regions` | List all 20 regions with default risk scores |
| POST | `/calculate` | Calculate risk from manual indicator inputs with full transparency |
| POST | `/override` | Set a manual risk score override for a country + dimension |
| DELETE | `/override/{country}` | Clear overrides (all dimensions or specific one) |
| GET | `/sources` | List all 7 external data sources with coverage details |
| POST | `/refresh/{country}` | Fetch latest data from all APIs for a country |
| POST | `/refresh-all` | Bulk refresh (default: top 25 manufacturing hubs) |
| POST | `/invalidate-cache` | Clear external data cache |

### System (`/api/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — status, app name, version |

Interactive API documentation available at `http://localhost:8000/docs` (Swagger UI) when the backend is running.

---

## Frontend Dashboard

5-page React/TypeScript SPA with dark theme and interactive visualizations.

### Pages

**Command Center** (`/`) — Executive overview with 6 KPI cards (resilience score, revenue at risk, avg risk, inventory health, supplier count, route count), geographic network map, risk-by-country chart, active alerts, and inventory burn-down status.

**Supply Network** (`/network`) — Interactive graph visualization with Mercator projection showing nodes by type (supplier, factory, port, distribution center) and edges by transport mode. Displays SPOFs, geographic concentration risk, and critical supply paths.

**Disruption Simulation** (`/simulation`) — Preset scenario selection cards with severity/duration badges. Impact analysis panel showing revenue at risk, recovery time, cost escalation, and fulfillment risk. Timeline charts for production capacity and cumulative revenue loss. AI-generated recommendations.

**Risk Intelligence** (`/risk`) — Risk distribution pie chart, country risk bar chart, top-risk entities table, and active alert feed. Summary metrics for high/medium/low entity counts.

**Supplier Registry** (`/suppliers`) — Sortable table with tier badges, country, risk score bars, dimension breakdowns (geopolitical, climate, financial), and critical-supplier indicators.

### Visualization Stack

- **Recharts** — Area charts (simulation timeline), bar charts (country risk), pie charts (risk distribution)
- **Custom SVG** — Mercator projection network map with node type coloring, chokepoint highlighting, and hover tooltips
- **Design system** — CSS custom properties with dark theme, consistent risk color coding (green/amber/red)

---

## Demo Data

The platform ships with a realistic electronics OEM supply chain built by `seed_data.py`:

**20 nodes** across 10 countries:
- **Tier 3** (raw materials): Silicon wafer plant (Taiwan), rare earth mine (China), chemical supplier (Japan)
- **Tier 2** (components): Semiconductor fab (Taiwan), display panel factory (South Korea), PCB manufacturer (China), battery cell plant (China)
- **Tier 1** (assembly): Electronics assembly (Vietnam, Mexico, India)
- **Infrastructure**: Ports (Netherlands, China, US), distribution centers (US, Germany, Australia)

**21 transport routes** with 4 maritime chokepoints:
- Taiwan Strait — semiconductor and silicon supply
- Suez Canal — Europe-bound shipments
- Strait of Malacca — Southeast Asia logistics
- Panama Canal — East Asia to US East Coast

---

## Quick Start

### Option 1: Backend Only (no database required)

The backend runs fully in-memory with demo seed data — no PostgreSQL needed.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000/api/v1/health
- Swagger docs: http://localhost:8000/docs

### Option 2: Backend + Frontend

Terminal 1 — backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:
```bash
cd frontend
npm install
npm run dev
```

- Dashboard: http://localhost:3000
- Vite proxies `/api` requests to the backend automatically

### Option 3: Docker Compose (full stack)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

---

## Configuration

Environment variables (or `.env` file in `backend/`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://continuix:continuix@localhost:5432/continuix` | Async database URL |
| `DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173"]` | Allowed CORS origins |
| `MONTE_CARLO_ITERATIONS` | `1000` | Default Monte Carlo runs per simulation |
| `MAX_SIMULATION_DURATION_DAYS` | `365` | Maximum scenario duration |
| `RISK_WEIGHT_GEOPOLITICAL` | `0.25` | Geopolitical dimension weight |
| `RISK_WEIGHT_CLIMATE` | `0.20` | Climate dimension weight |
| `RISK_WEIGHT_FINANCIAL` | `0.20` | Financial dimension weight |
| `RISK_WEIGHT_CYBER` | `0.15` | Cyber dimension weight |
| `RISK_WEIGHT_LOGISTICS` | `0.20` | Logistics dimension weight |

---

## Testing

```bash
cd backend
pytest tests/ -v
```

**135 tests** across 7 test files:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_graph_engine.py` | 17 | Graph construction, dependency tracing, SPOF detection, path analysis |
| `test_twin_engine.py` | 15 | Twin state, disruptions, daily simulation, recovery, analytics |
| `test_simulation_engine.py` | 27 | Scenario execution, all 20 presets, Monte Carlo confidence, twin reset |
| `test_risk_engine.py` | 14 | Supplier/facility/route scoring, classification, network summary |
| `test_country_baseline.py` | 21 | 199-country coverage, score ranges, lookups, search, attributes |
| `test_risk_calculator.py` | 20 | All 5 dimensions, sanctions, credit ratings, HDI, defaults, details |
| `test_external_data.py` | 21 | ISO mapping, normalization, HDI/Eurostat integration, caching, sources |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Python 3.12, FastAPI, Uvicorn |
| Graph modeling | NetworkX |
| Numerical computation | NumPy, SciPy |
| HTTP client (external APIs) | httpx (async) |
| Data validation | Pydantic v2, Pydantic Settings |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 (production), in-memory graph (demo) |
| Logging | structlog |
| Frontend framework | React 19, TypeScript 5.7 |
| Build tooling | Vite 6 |
| Charts | Recharts |
| Icons | Lucide React |
| Routing | React Router v7 |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Containerization | Docker, Docker Compose |
| Reverse proxy | Nginx |
