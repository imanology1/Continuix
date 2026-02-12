# Continuix — Resilient Supply Chain Twin

Predictive supply chain risk intelligence platform. Digital twin simulation, disruption forecasting, and resilience optimization.

## Architecture

```
backend/          Python/FastAPI backend
  app/
    api/routes/   REST API endpoints
    core/         Configuration, database
    models/       SQLAlchemy domain models
    schemas/      Pydantic request/response schemas
    services/     Core engines
      graph_engine.py         Supply chain graph (NetworkX)
      twin_engine.py          Digital twin state modeling
      simulation_engine.py    Disruption simulation + Monte Carlo
      risk_engine.py          Multi-dimensional risk scoring
      optimization_engine.py  Alternative sourcing optimizer
      seed_data.py            Demo supply chain data
  tests/          Pytest test suite

frontend/         React/TypeScript dashboard
  src/
    components/   Reusable UI components
    pages/        Route pages (Dashboard, Network, Simulation, Risk, Suppliers)
    services/     API client
    types/        TypeScript type definitions
```

## Core Engines

### Supply Chain Graph Engine
Directed graph (NetworkX) modeling multi-tier supplier networks. Provides dependency tracing, critical path identification, single-point-of-failure detection, and failure propagation analysis.

### Digital Twin Engine
Living computational replica of the supply chain. Each node carries dynamic state (capacity, inventory, throughput) that evolves daily. Supports disruption application with gradual recovery modeling.

### Disruption Simulation Engine
Runs what-if scenarios against the digital twin with Monte Carlo confidence intervals. Five preset scenarios:
- Taiwan Strait closure (90 days)
- Suez Canal blockage (14 days)
- Japan earthquake (60 days)
- China trade sanctions (180 days)
- Demand surge (+50%, 45 days)

Supports 15 disruption types across geopolitical, natural disaster, operational, and logistics categories.

### Risk Intelligence Engine
Weighted composite scoring across five dimensions:
- Geopolitical (0.25) — sanctions, conflict, instability
- Climate (0.20) — natural hazard exposure
- Financial (0.20) — credit risk, bankruptcy
- Cyber (0.15) — threat exposure
- Logistics (0.20) — route disruption, congestion

Includes baseline risk data for 25+ countries.

### Optimization Engine
Multi-objective alternative sourcing with cost/lead-time/capacity/risk tradeoffs. Recommends replacement suppliers, safety stock adjustments, and strategic sourcing shifts.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up
```

### Tests
```bash
cd backend
pytest tests/ -v
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/v1/dashboard/metrics` | Executive dashboard metrics |
| `GET /api/v1/network/graph` | Full supply chain graph |
| `GET /api/v1/network/vulnerabilities` | SPOFs, bridges, concentrations |
| `GET /api/v1/suppliers` | Supplier registry with risk scores |
| `GET /api/v1/risk/summary` | Aggregated risk intelligence |
| `GET /api/v1/risk/alerts` | Active risk alerts |
| `POST /api/v1/simulation/run` | Run custom disruption scenario |
| `POST /api/v1/simulation/presets/{id}` | Run preset scenario |
| `POST /api/v1/optimization/analyze` | Run optimization analysis |

## Demo Data

The platform ships with a realistic electronics OEM supply chain:
- 20+ nodes across 10 countries (Taiwan, China, South Korea, Japan, Vietnam, Germany, Mexico, India, US, Netherlands, Australia)
- 20+ transport routes including maritime chokepoints (Taiwan Strait, Suez Canal, Strait of Malacca, Panama Canal)
- Multi-tier network: Tier 3 (raw materials) → Tier 2 (components) → Tier 1 (assembly) → Distribution

## Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, NetworkX, NumPy/SciPy
- **Frontend**: React 19, TypeScript, Recharts, Vite
- **Database**: PostgreSQL 16 (production), in-memory graph (demo)
- **Infrastructure**: Docker, Nginx
