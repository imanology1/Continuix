from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Continuix - Resilient Supply Chain Twin"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://continuix:continuix@localhost:5432/continuix"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://continuix:continuix@localhost:5432/continuix"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Simulation
    MAX_SIMULATION_DURATION_DAYS: int = 365
    MONTE_CARLO_ITERATIONS: int = 1000
    SIMULATION_TIMEOUT_SECONDS: int = 60

    # Risk Engine
    RISK_WEIGHT_GEOPOLITICAL: float = 0.25
    RISK_WEIGHT_CLIMATE: float = 0.20
    RISK_WEIGHT_FINANCIAL: float = 0.20
    RISK_WEIGHT_CYBER: float = 0.15
    RISK_WEIGHT_LOGISTICS: float = 0.20

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
