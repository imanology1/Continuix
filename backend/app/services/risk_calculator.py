"""
Flexible Risk Calculator

Computes risk scores from arbitrary user-provided inputs.
Users can enter raw indicator values (political stability, inflation, LPI, etc.)
and the calculator normalizes them to the 0-100 risk scale.

This enables:
- Manual data entry for countries without API coverage
- Custom overrides for specific indicators
- CSV/bulk import workflows
- What-if analysis with hypothetical values
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RiskInput:
    """Raw input data for risk calculation. All fields optional — the calculator
    uses whatever is provided and fills gaps with regional/global defaults."""

    country_iso: str
    country_name: str

    # Geopolitical inputs
    political_stability: Optional[float] = None    # World Bank WGI: -2.5 to 2.5
    govt_effectiveness: Optional[float] = None      # World Bank WGI: -2.5 to 2.5
    conflict_intensity: Optional[float] = None      # 0 (none) to 10 (war)
    sanctions_active: bool = False                   # Binary: under active sanctions?
    fragile_state_index: Optional[float] = None      # Fund for Peace FSI: 0-120

    # Climate inputs
    climate_vulnerability: Optional[float] = None    # ND-GAIN: 0-100 (higher = more vulnerable)
    climate_readiness: Optional[float] = None        # ND-GAIN: 0-100 (higher = more ready)
    natural_hazard_frequency: Optional[float] = None # Average annual events per 1M sq km
    flood_risk: Optional[float] = None               # 0-10
    earthquake_risk: Optional[float] = None          # 0-10
    cyclone_risk: Optional[float] = None             # 0-10

    # Financial inputs
    inflation_pct: Optional[float] = None            # Annual CPI %
    gdp_growth_pct: Optional[float] = None           # Annual real GDP growth %
    sovereign_credit_rating: Optional[str] = None    # S&P style: AAA to D
    debt_to_gdp_pct: Optional[float] = None          # %
    currency_volatility: Optional[float] = None      # Annualized vol %
    hdi_score: Optional[float] = None                # UNDP HDI: 0-1
    gdp_per_capita_ppp: Optional[float] = None       # USD PPP
    unemployment_pct: Optional[float] = None         # Eurostat / ILO unemployment %

    # Cyber inputs
    cybersecurity_index: Optional[float] = None      # ITU GCI: 0-100
    internet_penetration_pct: Optional[float] = None # % of population
    data_breach_frequency: Optional[float] = None    # Incidents per year per 1M pop

    # Logistics inputs
    logistics_performance: Optional[float] = None    # World Bank LPI: 1-5
    port_efficiency: Optional[float] = None          # 0-100 (Container Port Performance Index)
    infrastructure_quality: Optional[float] = None   # WEF: 1-7
    trade_openness: Optional[float] = None           # (Exports+Imports)/GDP ratio
    customs_efficiency: Optional[float] = None       # LPI customs sub-index: 1-5

    # Metadata
    data_source: str = "manual"
    entered_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


@dataclass
class CalculatedRisk:
    """Output of risk calculation with full transparency on how scores were derived."""
    country_iso: str
    country_name: str
    geopolitical: float = 50.0
    climate: float = 50.0
    financial: float = 50.0
    cyber: float = 50.0
    logistics: float = 50.0
    overall: float = 50.0
    data_completeness: float = 0.0  # 0-1
    source: str = "manual"
    calculation_details: dict = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.utcnow)


# Credit rating → risk score mapping
CREDIT_RATING_RISK = {
    "AAA": 5, "AA+": 8, "AA": 10, "AA-": 13,
    "A+": 16, "A": 20, "A-": 25,
    "BBB+": 30, "BBB": 35, "BBB-": 40,
    "BB+": 48, "BB": 55, "BB-": 60,
    "B+": 65, "B": 70, "B-": 75,
    "CCC+": 80, "CCC": 85, "CCC-": 88,
    "CC": 92, "C": 95, "D": 100,
}


class RiskCalculator:
    """
    Computes normalized 0-100 risk scores from raw indicator inputs.
    Transparently shows which inputs contributed to each dimension.

    All dimensions follow: higher score = higher risk.
    """

    def __init__(self, weights: Optional[dict[str, float]] = None):
        self.weights = weights or {
            "geopolitical": 0.25,
            "climate": 0.20,
            "financial": 0.20,
            "cyber": 0.15,
            "logistics": 0.20,
        }

    def calculate(self, inputs: RiskInput, defaults: Optional[dict[str, float]] = None) -> CalculatedRisk:
        """
        Calculate risk scores from raw inputs.

        Args:
            inputs: Raw indicator values
            defaults: Optional fallback scores {dimension: score} for missing data
        """
        defaults = defaults or {}
        details: dict[str, list[dict]] = {
            "geopolitical": [], "climate": [], "financial": [],
            "cyber": [], "logistics": [],
        }

        # --- Geopolitical ---
        geo_scores = []

        if inputs.political_stability is not None:
            # WGI: -2.5 (worst) to 2.5 (best) → 100 to 0
            score = _clamp((2.5 - inputs.political_stability) / 5.0 * 100)
            geo_scores.append(("political_stability", score, 0.4))
            details["geopolitical"].append({
                "indicator": "political_stability",
                "raw_value": inputs.political_stability,
                "normalized": round(score, 1),
                "weight": 0.4,
            })

        if inputs.govt_effectiveness is not None:
            score = _clamp((2.5 - inputs.govt_effectiveness) / 5.0 * 100)
            geo_scores.append(("govt_effectiveness", score, 0.3))
            details["geopolitical"].append({
                "indicator": "govt_effectiveness",
                "raw_value": inputs.govt_effectiveness,
                "normalized": round(score, 1),
                "weight": 0.3,
            })

        if inputs.conflict_intensity is not None:
            score = _clamp(inputs.conflict_intensity * 10)
            geo_scores.append(("conflict_intensity", score, 0.2))
            details["geopolitical"].append({
                "indicator": "conflict_intensity",
                "raw_value": inputs.conflict_intensity,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        if inputs.fragile_state_index is not None:
            # FSI: 0 (stable) to 120 (fragile) → 0 to 100
            score = _clamp(inputs.fragile_state_index / 120 * 100)
            geo_scores.append(("fragile_state_index", score, 0.1))
            details["geopolitical"].append({
                "indicator": "fragile_state_index",
                "raw_value": inputs.fragile_state_index,
                "normalized": round(score, 1),
                "weight": 0.1,
            })

        if inputs.sanctions_active:
            geo_scores.append(("sanctions_active", 90.0, 0.3))
            details["geopolitical"].append({
                "indicator": "sanctions_active",
                "raw_value": True,
                "normalized": 90.0,
                "weight": 0.3,
            })

        geo = _weighted_avg(geo_scores, defaults.get("geopolitical", 50.0))

        # --- Climate ---
        climate_scores = []

        if inputs.climate_vulnerability is not None:
            # ND-GAIN vulnerability: 0-100, higher = more vulnerable
            climate_scores.append(("climate_vulnerability", inputs.climate_vulnerability, 0.4))
            details["climate"].append({
                "indicator": "climate_vulnerability",
                "raw_value": inputs.climate_vulnerability,
                "normalized": round(inputs.climate_vulnerability, 1),
                "weight": 0.4,
            })

        if inputs.climate_readiness is not None:
            # ND-GAIN readiness: 0-100, higher = more ready = lower risk
            score = _clamp(100 - inputs.climate_readiness)
            climate_scores.append(("climate_readiness", score, 0.3))
            details["climate"].append({
                "indicator": "climate_readiness",
                "raw_value": inputs.climate_readiness,
                "normalized": round(score, 1),
                "weight": 0.3,
            })

        if inputs.natural_hazard_frequency is not None:
            score = _clamp(min(100, inputs.natural_hazard_frequency * 5))
            climate_scores.append(("natural_hazard_frequency", score, 0.15))
            details["climate"].append({
                "indicator": "natural_hazard_frequency",
                "raw_value": inputs.natural_hazard_frequency,
                "normalized": round(score, 1),
                "weight": 0.15,
            })

        # Individual hazard types
        for hazard, attr in [("flood_risk", inputs.flood_risk),
                             ("earthquake_risk", inputs.earthquake_risk),
                             ("cyclone_risk", inputs.cyclone_risk)]:
            if attr is not None:
                score = _clamp(attr * 10)
                climate_scores.append((hazard, score, 0.05))
                details["climate"].append({
                    "indicator": hazard,
                    "raw_value": attr,
                    "normalized": round(score, 1),
                    "weight": 0.05,
                })

        climate = _weighted_avg(climate_scores, defaults.get("climate", 50.0))

        # --- Financial ---
        fin_scores = []

        if inputs.inflation_pct is not None:
            # Low inflation (<3%) → low risk, high (>15%) → high risk
            score = _clamp(inputs.inflation_pct * 5)
            fin_scores.append(("inflation_pct", score, 0.25))
            details["financial"].append({
                "indicator": "inflation_pct",
                "raw_value": inputs.inflation_pct,
                "normalized": round(score, 1),
                "weight": 0.25,
            })

        if inputs.gdp_growth_pct is not None:
            # Negative growth = high risk, >5% = low risk
            score = _clamp(50 - inputs.gdp_growth_pct * 8)
            fin_scores.append(("gdp_growth_pct", score, 0.2))
            details["financial"].append({
                "indicator": "gdp_growth_pct",
                "raw_value": inputs.gdp_growth_pct,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        if inputs.sovereign_credit_rating is not None:
            score = CREDIT_RATING_RISK.get(inputs.sovereign_credit_rating, 50)
            fin_scores.append(("sovereign_credit_rating", float(score), 0.2))
            details["financial"].append({
                "indicator": "sovereign_credit_rating",
                "raw_value": inputs.sovereign_credit_rating,
                "normalized": float(score),
                "weight": 0.2,
            })

        if inputs.debt_to_gdp_pct is not None:
            # <60% safe, >120% risky
            score = _clamp((inputs.debt_to_gdp_pct - 30) / 120 * 100)
            fin_scores.append(("debt_to_gdp_pct", score, 0.1))
            details["financial"].append({
                "indicator": "debt_to_gdp_pct",
                "raw_value": inputs.debt_to_gdp_pct,
                "normalized": round(score, 1),
                "weight": 0.1,
            })

        if inputs.currency_volatility is not None:
            # <5% = stable, >20% = risky
            score = _clamp(inputs.currency_volatility * 4)
            fin_scores.append(("currency_volatility", score, 0.1))
            details["financial"].append({
                "indicator": "currency_volatility",
                "raw_value": inputs.currency_volatility,
                "normalized": round(score, 1),
                "weight": 0.1,
            })

        if inputs.hdi_score is not None:
            # HDI 0-1: higher = better development = lower risk
            score = _clamp((1.0 - inputs.hdi_score) * 100)
            fin_scores.append(("hdi_score", score, 0.1))
            details["financial"].append({
                "indicator": "hdi_score",
                "raw_value": inputs.hdi_score,
                "normalized": round(score, 1),
                "weight": 0.1,
            })

        if inputs.unemployment_pct is not None:
            # <5% = healthy, >20% = severe
            score = _clamp(inputs.unemployment_pct * 4)
            fin_scores.append(("unemployment_pct", score, 0.05))
            details["financial"].append({
                "indicator": "unemployment_pct",
                "raw_value": inputs.unemployment_pct,
                "normalized": round(score, 1),
                "weight": 0.05,
            })

        fin = _weighted_avg(fin_scores, defaults.get("financial", 50.0))

        # --- Cyber ---
        cyber_scores = []

        if inputs.cybersecurity_index is not None:
            # ITU GCI: 0-100, higher = more secure = lower risk
            score = _clamp(100 - inputs.cybersecurity_index)
            cyber_scores.append(("cybersecurity_index", score, 0.6))
            details["cyber"].append({
                "indicator": "cybersecurity_index",
                "raw_value": inputs.cybersecurity_index,
                "normalized": round(score, 1),
                "weight": 0.6,
            })

        if inputs.internet_penetration_pct is not None:
            # Higher penetration = larger attack surface but also better infrastructure
            # U-shaped: low penetration (poor infra) and very high (large surface) both risky
            if inputs.internet_penetration_pct < 50:
                score = _clamp((50 - inputs.internet_penetration_pct) * 1.5)
            else:
                score = _clamp(20 + (inputs.internet_penetration_pct - 50) * 0.3)
            cyber_scores.append(("internet_penetration_pct", score, 0.2))
            details["cyber"].append({
                "indicator": "internet_penetration_pct",
                "raw_value": inputs.internet_penetration_pct,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        if inputs.data_breach_frequency is not None:
            score = _clamp(inputs.data_breach_frequency * 5)
            cyber_scores.append(("data_breach_frequency", score, 0.2))
            details["cyber"].append({
                "indicator": "data_breach_frequency",
                "raw_value": inputs.data_breach_frequency,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        cyber = _weighted_avg(cyber_scores, defaults.get("cyber", 50.0))

        # --- Logistics ---
        log_scores = []

        if inputs.logistics_performance is not None:
            # LPI: 1 (worst) to 5 (best) → 100 to 0
            score = _clamp((5.0 - inputs.logistics_performance) / 4.0 * 100)
            log_scores.append(("logistics_performance", score, 0.35))
            details["logistics"].append({
                "indicator": "logistics_performance",
                "raw_value": inputs.logistics_performance,
                "normalized": round(score, 1),
                "weight": 0.35,
            })

        if inputs.port_efficiency is not None:
            # 0-100, higher = better → invert
            score = _clamp(100 - inputs.port_efficiency)
            log_scores.append(("port_efficiency", score, 0.2))
            details["logistics"].append({
                "indicator": "port_efficiency",
                "raw_value": inputs.port_efficiency,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        if inputs.infrastructure_quality is not None:
            # WEF: 1 (worst) to 7 (best) → 100 to 0
            score = _clamp((7.0 - inputs.infrastructure_quality) / 6.0 * 100)
            log_scores.append(("infrastructure_quality", score, 0.25))
            details["logistics"].append({
                "indicator": "infrastructure_quality",
                "raw_value": inputs.infrastructure_quality,
                "normalized": round(score, 1),
                "weight": 0.25,
            })

        if inputs.customs_efficiency is not None:
            # LPI customs: 1 (worst) to 5 (best) → 100 to 0
            score = _clamp((5.0 - inputs.customs_efficiency) / 4.0 * 100)
            log_scores.append(("customs_efficiency", score, 0.2))
            details["logistics"].append({
                "indicator": "customs_efficiency",
                "raw_value": inputs.customs_efficiency,
                "normalized": round(score, 1),
                "weight": 0.2,
            })

        logistics = _weighted_avg(log_scores, defaults.get("logistics", 50.0))

        # Count data completeness
        total_possible = 20  # total input fields
        filled = sum(1 for v in [
            inputs.political_stability, inputs.govt_effectiveness, inputs.conflict_intensity,
            inputs.fragile_state_index, inputs.climate_vulnerability, inputs.climate_readiness,
            inputs.natural_hazard_frequency, inputs.flood_risk, inputs.earthquake_risk,
            inputs.cyclone_risk, inputs.inflation_pct, inputs.gdp_growth_pct,
            inputs.sovereign_credit_rating, inputs.debt_to_gdp_pct, inputs.currency_volatility,
            inputs.hdi_score, inputs.cybersecurity_index, inputs.internet_penetration_pct,
            inputs.logistics_performance, inputs.infrastructure_quality,
        ] if v is not None)
        if inputs.sanctions_active:
            filled += 1

        completeness = filled / total_possible

        # Overall weighted score
        overall = (
            geo * self.weights["geopolitical"]
            + climate * self.weights["climate"]
            + fin * self.weights["financial"]
            + cyber * self.weights["cyber"]
            + logistics * self.weights["logistics"]
        )

        return CalculatedRisk(
            country_iso=inputs.country_iso,
            country_name=inputs.country_name,
            geopolitical=round(geo, 1),
            climate=round(climate, 1),
            financial=round(fin, 1),
            cyber=round(cyber, 1),
            logistics=round(logistics, 1),
            overall=round(overall, 1),
            data_completeness=round(completeness, 2),
            source=inputs.data_source,
            calculation_details=details,
        )

    def recalculate_overall(self, scores: dict[str, float]) -> float:
        """Recalculate overall score from dimension scores with current weights."""
        return round(sum(
            scores.get(dim, 50.0) * w
            for dim, w in self.weights.items()
        ), 1)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _weighted_avg(
    components: list[tuple[str, float, float]],
    default: float,
) -> float:
    """Weighted average of (name, score, weight) tuples. Falls back to default if empty."""
    if not components:
        return default
    total_weight = sum(w for _, _, w in components)
    if total_weight == 0:
        return default
    return sum(s * w for _, s, w in components) / total_weight
