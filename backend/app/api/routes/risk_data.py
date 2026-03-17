"""
Risk data management API routes.

Provides endpoints for:
- Manual risk data entry and calculation
- External data source refresh
- Country risk profile browsing and search
- Data source listing and status
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_platform
from app.services.country_baseline import (
    get_country_risk,
    get_all_countries,
    get_country_profile,
    search_countries,
    COUNTRY_PROFILES,
    REGIONAL_DEFAULTS,
)
from app.services.risk_calculator import RiskCalculator, RiskInput, CalculatedRisk
from app.services.external_data import ExternalDataProvider

router = APIRouter(prefix="/risk-data", tags=["risk-data"])

# Shared instances
_external_provider = ExternalDataProvider()
_calculator = RiskCalculator()


# --- Request/Response schemas ---

class ManualRiskInput(BaseModel):
    """Manual data entry for risk calculation."""
    country_name: str
    country_iso: str

    # Geopolitical
    political_stability: Optional[float] = Field(None, ge=-2.5, le=2.5)
    govt_effectiveness: Optional[float] = Field(None, ge=-2.5, le=2.5)
    conflict_intensity: Optional[float] = Field(None, ge=0, le=10)
    sanctions_active: bool = False
    fragile_state_index: Optional[float] = Field(None, ge=0, le=120)

    # Climate
    climate_vulnerability: Optional[float] = Field(None, ge=0, le=100)
    climate_readiness: Optional[float] = Field(None, ge=0, le=100)
    natural_hazard_frequency: Optional[float] = Field(None, ge=0)
    flood_risk: Optional[float] = Field(None, ge=0, le=10)
    earthquake_risk: Optional[float] = Field(None, ge=0, le=10)
    cyclone_risk: Optional[float] = Field(None, ge=0, le=10)

    # Financial
    inflation_pct: Optional[float] = None
    gdp_growth_pct: Optional[float] = None
    sovereign_credit_rating: Optional[str] = None
    debt_to_gdp_pct: Optional[float] = Field(None, ge=0)
    currency_volatility: Optional[float] = Field(None, ge=0)
    hdi_score: Optional[float] = Field(None, ge=0, le=1)
    unemployment_pct: Optional[float] = Field(None, ge=0, le=100)

    # Cyber
    cybersecurity_index: Optional[float] = Field(None, ge=0, le=100)
    internet_penetration_pct: Optional[float] = Field(None, ge=0, le=100)

    # Logistics
    logistics_performance: Optional[float] = Field(None, ge=1, le=5)
    port_efficiency: Optional[float] = Field(None, ge=0, le=100)
    infrastructure_quality: Optional[float] = Field(None, ge=1, le=7)
    customs_efficiency: Optional[float] = Field(None, ge=1, le=5)

    notes: Optional[str] = None


class CountryOverride(BaseModel):
    """Direct score override for a country risk dimension."""
    country: str
    dimension: str = Field(..., pattern="^(geopolitical|climate|financial|cyber|logistics)$")
    score: float = Field(..., ge=0, le=100)


class CalculatedRiskResponse(BaseModel):
    country_iso: str
    country_name: str
    geopolitical: float
    climate: float
    financial: float
    cyber: float
    logistics: float
    overall: float
    data_completeness: float
    source: str
    calculation_details: dict


class CountryRiskResponse(BaseModel):
    iso3: str
    name: str
    region: str
    sub_region: str
    geopolitical: float
    climate: float
    financial: float
    cyber: float
    logistics: float
    income_group: str


# --- Endpoints ---

@router.get("/countries")
async def list_countries(
    region: Optional[str] = Query(None, description="Filter by region or sub-region"),
    search: Optional[str] = Query(None, description="Search by name or ISO code"),
):
    """
    List all 190+ countries with risk profiles.
    Optionally filter by region or search by name/ISO code.
    """
    if search:
        results = search_countries(search)
        return [
            {
                "iso3": p.iso3, "name": p.name, "region": p.region,
                "sub_region": p.sub_region,
                "geopolitical": p.geopolitical, "climate": p.climate,
                "financial": p.financial, "cyber": p.cyber, "logistics": p.logistics,
                "income_group": p.income_group,
            }
            for p in results
        ]

    countries = get_all_countries()
    if region:
        countries = [c for c in countries if c["region"] == region or c["sub_region"] == region]
    return countries


@router.get("/countries/{country_name}")
async def get_country_detail(country_name: str):
    """Get detailed risk profile for a specific country."""
    profile = get_country_profile(country_name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Country '{country_name}' not found")

    platform = get_platform()
    overrides = platform.risk_engine._manual_overrides.get(country_name, {})

    return {
        "iso3": profile.iso3,
        "name": profile.name,
        "region": profile.region,
        "sub_region": profile.sub_region,
        "risk_scores": {
            "geopolitical": overrides.get("geopolitical", profile.geopolitical),
            "climate": overrides.get("climate", profile.climate),
            "financial": overrides.get("financial", profile.financial),
            "cyber": overrides.get("cyber", profile.cyber),
            "logistics": overrides.get("logistics", profile.logistics),
        },
        "baseline_scores": {
            "geopolitical": profile.geopolitical,
            "climate": profile.climate,
            "financial": profile.financial,
            "cyber": profile.cyber,
            "logistics": profile.logistics,
        },
        "manual_overrides": overrides,
        "income_group": profile.income_group,
        "is_landlocked": profile.is_landlocked,
        "is_small_island": profile.is_small_island,
    }


@router.get("/regions")
async def list_regions():
    """List all regions with their default risk scores."""
    return {
        "regions": [
            {"name": name, **scores}
            for name, scores in REGIONAL_DEFAULTS.items()
        ],
        "total_countries": len(COUNTRY_PROFILES),
    }


@router.post("/calculate", response_model=CalculatedRiskResponse)
async def calculate_risk(inputs: ManualRiskInput):
    """
    Calculate risk scores from manually entered indicator data.
    Returns normalized 0-100 risk scores with full calculation transparency.
    """
    risk_input = RiskInput(
        country_iso=inputs.country_iso,
        country_name=inputs.country_name,
        political_stability=inputs.political_stability,
        govt_effectiveness=inputs.govt_effectiveness,
        conflict_intensity=inputs.conflict_intensity,
        sanctions_active=inputs.sanctions_active,
        fragile_state_index=inputs.fragile_state_index,
        climate_vulnerability=inputs.climate_vulnerability,
        climate_readiness=inputs.climate_readiness,
        natural_hazard_frequency=inputs.natural_hazard_frequency,
        flood_risk=inputs.flood_risk,
        earthquake_risk=inputs.earthquake_risk,
        cyclone_risk=inputs.cyclone_risk,
        inflation_pct=inputs.inflation_pct,
        gdp_growth_pct=inputs.gdp_growth_pct,
        sovereign_credit_rating=inputs.sovereign_credit_rating,
        debt_to_gdp_pct=inputs.debt_to_gdp_pct,
        currency_volatility=inputs.currency_volatility,
        hdi_score=inputs.hdi_score,
        unemployment_pct=inputs.unemployment_pct,
        cybersecurity_index=inputs.cybersecurity_index,
        internet_penetration_pct=inputs.internet_penetration_pct,
        logistics_performance=inputs.logistics_performance,
        port_efficiency=inputs.port_efficiency,
        infrastructure_quality=inputs.infrastructure_quality,
        customs_efficiency=inputs.customs_efficiency,
        data_source="manual",
        notes=inputs.notes,
    )

    # Use country baseline as defaults for missing indicators
    defaults = get_country_risk(inputs.country_name)
    result = _calculator.calculate(risk_input, defaults=defaults)

    return CalculatedRiskResponse(
        country_iso=result.country_iso,
        country_name=result.country_name,
        geopolitical=result.geopolitical,
        climate=result.climate,
        financial=result.financial,
        cyber=result.cyber,
        logistics=result.logistics,
        overall=result.overall,
        data_completeness=result.data_completeness,
        source=result.source,
        calculation_details=result.calculation_details,
    )


@router.post("/override")
async def set_risk_override(override: CountryOverride):
    """
    Set a manual risk score override for a specific country + dimension.
    Override takes precedence over baseline and API data.
    """
    platform = get_platform()
    platform.risk_engine.set_country_override(
        override.country, override.dimension, override.score,
    )
    return {
        "status": "ok",
        "country": override.country,
        "dimension": override.dimension,
        "score": override.score,
    }


@router.delete("/override/{country}")
async def clear_risk_override(
    country: str,
    dimension: Optional[str] = Query(None, description="Specific dimension to clear"),
):
    """Clear manual risk overrides for a country."""
    platform = get_platform()
    platform.risk_engine.clear_country_override(country, dimension)
    return {"status": "ok", "country": country, "cleared": dimension or "all"}


@router.get("/sources")
async def list_data_sources():
    """List all available external data sources with descriptions."""
    return {
        "sources": _external_provider.get_available_sources(),
        "auto_fetch_sources": ["world_bank_wgi", "world_bank_lpi", "imf", "undp_hdi", "eurostat"],
        "manual_upload_sources": ["ndgain", "itu_gci"],
    }


@router.post("/refresh/{country_name}")
async def refresh_country_data(country_name: str):
    """
    Fetch latest data from all external APIs for a specific country.
    Returns raw indicators and normalized risk scores.
    """
    indicators = await _external_provider.fetch_country(country_name)
    if indicators.country_iso == "UNK":
        raise HTTPException(status_code=404, detail=f"No ISO mapping for '{country_name}'")

    normalized = _external_provider.normalize(indicators)

    return {
        "country": country_name,
        "iso": indicators.country_iso,
        "sources_used": indicators.sources_used,
        "raw_indicators": {
            "political_stability": indicators.political_stability,
            "govt_effectiveness": indicators.govt_effectiveness,
            "logistics_performance": indicators.logistics_performance,
            "inflation_pct": indicators.inflation_pct,
            "gdp_growth_pct": indicators.gdp_growth_pct,
            "climate_vulnerability": indicators.climate_vulnerability,
            "climate_readiness": indicators.climate_readiness,
            "cybersecurity_index": indicators.cybersecurity_index,
            "hdi_score": indicators.hdi_score,
            "hdi_rank": indicators.hdi_rank,
            "eu_unemployment_pct": indicators.eu_unemployment_pct,
            "eu_hicp_annual_pct": indicators.eu_hicp_annual_pct,
        },
        "normalized_scores": {
            "geopolitical": normalized.geopolitical,
            "climate": normalized.climate,
            "financial": normalized.financial,
            "cyber": normalized.cyber,
            "logistics": normalized.logistics,
        },
        "data_completeness": normalized.data_completeness,
        "fetched_at": indicators.fetched_at.isoformat(),
    }


@router.post("/refresh-all")
async def refresh_all_data(
    countries: Optional[list[str]] = None,
):
    """
    Bulk refresh external data for multiple countries.
    If no countries specified, refreshes the top 25 manufacturing hubs.
    """
    if not countries:
        countries = [
            "United States", "China", "Taiwan", "Japan", "South Korea",
            "Germany", "India", "Vietnam", "Mexico", "Brazil",
            "Thailand", "Malaysia", "Indonesia", "Turkey", "Singapore",
            "Netherlands", "United Kingdom", "Canada", "Australia", "France",
            "Italy", "Spain", "Poland", "Czech Republic", "South Africa",
        ]

    results = await _external_provider.fetch_many(countries)

    summary = []
    for name, indicators in results.items():
        normalized = _external_provider.normalize(indicators)
        summary.append({
            "country": name,
            "iso": indicators.country_iso,
            "sources_used": indicators.sources_used,
            "data_completeness": normalized.data_completeness,
        })

    return {
        "refreshed": len(results),
        "requested": len(countries),
        "results": summary,
    }


@router.post("/invalidate-cache")
async def invalidate_cache(country_iso: Optional[str] = None):
    """Clear the external data cache (all or specific country)."""
    _external_provider.invalidate_cache(country_iso)
    return {
        "status": "ok",
        "cleared": country_iso or "all",
    }
