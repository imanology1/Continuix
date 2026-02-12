"""
Continuix — Resilient Supply Chain Twin
Main FastAPI application entry point.
"""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.dependencies import init_platform
from app.api.routes import suppliers, network, simulation, risk, risk_data, dashboard, optimization
from app.services.seed_data import build_demo_supply_chain

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engines and seed demo data on startup."""
    log.info("Initializing Continuix platform...")
    graph, twin, risk_engine = build_demo_supply_chain()
    init_platform(graph, twin, risk_engine)
    log.info(
        "Platform ready",
        nodes=graph.node_count,
        edges=graph.edge_count,
        resilience=graph.calculate_resilience_score(),
    )
    yield
    log.info("Shutting down Continuix platform.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Predictive Supply Chain Risk Intelligence platform. "
        "Digital twin simulation, disruption forecasting, and resilience optimization."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(network.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(risk_data.router, prefix="/api/v1")
app.include_router(optimization.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
