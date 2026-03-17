"""
Risk Intelligence Engine

Continuously scores supply chain risk across five dimensions:
- Geopolitical (sanctions, conflict, political instability)
- Climate (natural hazard exposure)
- Financial (credit risk, bankruptcy probability)
- Cyber (threat exposure)
- Logistics (route disruption, congestion)

Uses weighted composite scoring per the requirements:
  Risk = Geo*0.25 + Climate*0.20 + Financial*0.20 + Cyber*0.15 + Logistics*0.20

Now backed by:
- 190+ country baseline profiles (country_baseline.py)
- External API data (World Bank, IMF, UNDP, Eurostat)
- Flexible risk calculator for manual data entry
- Manual override support for any dimension
"""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from app.core.config import settings
from app.services.country_baseline import (
    get_country_risk,
    get_country_risk_by_iso,
    get_all_countries,
    get_country_profile,
    search_countries,
    COUNTRY_PROFILES,
)


# Legacy alias — existing code that imports COUNTRY_RISK_DATA still works.
# Now delegates to the 190+ country baseline.
COUNTRY_RISK_DATA = {name: get_country_risk(name) for name in COUNTRY_PROFILES}

DEFAULT_COUNTRY_RISK = {"geopolitical": 40, "climate": 40, "financial": 40, "cyber": 35, "logistics": 35}


@dataclass
class RiskAssessment:
    entity_id: str
    entity_type: str  # supplier, facility, route
    entity_name: str
    country: str
    geopolitical: float = 0.0
    climate: float = 0.0
    financial: float = 0.0
    cyber: float = 0.0
    logistics: float = 0.0
    overall: float = 0.0
    trend: str = "stable"  # increasing, stable, decreasing
    factors: list[str] = field(default_factory=list)


class RiskEngine:
    """
    Scores risk for supply chain entities using a weighted composite model.
    Backed by 190+ country profiles with external API integration.
    """

    def __init__(
        self,
        geo_weight: float = settings.RISK_WEIGHT_GEOPOLITICAL,
        climate_weight: float = settings.RISK_WEIGHT_CLIMATE,
        financial_weight: float = settings.RISK_WEIGHT_FINANCIAL,
        cyber_weight: float = settings.RISK_WEIGHT_CYBER,
        logistics_weight: float = settings.RISK_WEIGHT_LOGISTICS,
    ):
        self.weights = {
            "geopolitical": geo_weight,
            "climate": climate_weight,
            "financial": financial_weight,
            "cyber": cyber_weight,
            "logistics": logistics_weight,
        }
        # Manual overrides storage: country -> {dimension: score}
        self._manual_overrides: dict[str, dict[str, float]] = {}

    def set_country_override(self, country: str, dimension: str, score: float):
        """Set a manual risk score override for a country + dimension."""
        if country not in self._manual_overrides:
            self._manual_overrides[country] = {}
        self._manual_overrides[country][dimension] = max(0, min(100, score))

    def clear_country_override(self, country: str, dimension: Optional[str] = None):
        """Clear manual override for a country (all dimensions or specific one)."""
        if dimension:
            self._manual_overrides.get(country, {}).pop(dimension, None)
        else:
            self._manual_overrides.pop(country, None)

    def get_country_baseline(self, country: str) -> dict[str, float]:
        """Get risk baseline for a country, with manual overrides applied."""
        baseline = get_country_risk(country)
        overrides = self._manual_overrides.get(country, {})
        for dim, val in overrides.items():
            if dim in baseline:
                baseline[dim] = val
        return baseline

    def score_supplier(
        self,
        supplier_id: str,
        name: str,
        country: str,
        tier: str,
        financial_health: Optional[float] = None,
        cyber_exposure: Optional[float] = None,
        logistics_complexity: Optional[float] = None,
        is_sole_source: bool = False,
        reliability_score: float = 0.9,
    ) -> RiskAssessment:
        """
        Score a supplier across all risk dimensions.
        """
        country_baseline = self.get_country_baseline(country)

        # Geopolitical: country baseline + tier modifier
        tier_multiplier = {"tier_1": 1.0, "tier_2": 1.1, "tier_3": 1.2, "tier_4": 1.3}.get(tier, 1.0)
        geo = min(100, country_baseline["geopolitical"] * tier_multiplier)

        # Climate: country baseline
        climate = country_baseline["climate"]

        # Financial: country baseline + specific health data if available
        fin = country_baseline["financial"]
        if financial_health is not None:
            fin = (fin * 0.4) + (financial_health * 0.6)

        # Cyber: country baseline + exposure data
        cyber = country_baseline["cyber"]
        if cyber_exposure is not None:
            cyber = (cyber * 0.4) + (cyber_exposure * 0.6)

        # Logistics: country baseline + complexity
        logistics = country_baseline["logistics"]
        if logistics_complexity is not None:
            logistics = (logistics * 0.4) + (logistics_complexity * 0.6)

        # Sole source penalty: +20% across all categories
        if is_sole_source:
            geo = min(100, geo * 1.2)
            fin = min(100, fin * 1.2)
            logistics = min(100, logistics * 1.2)

        # Low reliability penalty
        if reliability_score < 0.8:
            penalty = (0.8 - reliability_score) * 50
            logistics = min(100, logistics + penalty)

        # Weighted composite
        overall = (
            geo * self.weights["geopolitical"]
            + climate * self.weights["climate"]
            + fin * self.weights["financial"]
            + cyber * self.weights["cyber"]
            + logistics * self.weights["logistics"]
        )

        # Risk factors
        factors = []
        if geo > 50:
            factors.append(f"High geopolitical risk in {country}")
        if climate > 50:
            factors.append(f"Elevated climate/natural hazard exposure in {country}")
        if fin > 50:
            factors.append("Financial instability indicators present")
        if cyber > 40:
            factors.append("Above-average cyber threat exposure")
        if logistics > 40:
            factors.append("Logistics complexity and disruption risk")
        if is_sole_source:
            factors.append("Single-source supplier — no backup")
        if reliability_score < 0.8:
            factors.append(f"Below-target reliability: {reliability_score:.0%}")

        return RiskAssessment(
            entity_id=supplier_id,
            entity_type="supplier",
            entity_name=name,
            country=country,
            geopolitical=round(geo, 1),
            climate=round(climate, 1),
            financial=round(fin, 1),
            cyber=round(cyber, 1),
            logistics=round(logistics, 1),
            overall=round(overall, 1),
            factors=factors,
        )

    def score_facility(
        self,
        facility_id: str,
        name: str,
        country: str,
        facility_type: str,
        natural_hazard_exposure: float = 0.0,
        utilization: float = 0.7,
    ) -> RiskAssessment:
        """Score risk for a facility."""
        country_baseline = self.get_country_baseline(country)

        geo = country_baseline["geopolitical"]
        climate = max(country_baseline["climate"], natural_hazard_exposure)
        fin = country_baseline["financial"]
        cyber = country_baseline["cyber"]
        logistics = country_baseline["logistics"]

        # High utilization = less buffer capacity = higher risk
        if utilization > 0.85:
            overhead = (utilization - 0.85) * 200  # up to +30 at 100%
            logistics = min(100, logistics + overhead)

        # Port facilities have higher logistics risk
        if facility_type == "port":
            logistics = min(100, logistics * 1.3)

        overall = (
            geo * self.weights["geopolitical"]
            + climate * self.weights["climate"]
            + fin * self.weights["financial"]
            + cyber * self.weights["cyber"]
            + logistics * self.weights["logistics"]
        )

        factors = []
        if utilization > 0.85:
            factors.append(f"High utilization ({utilization:.0%}) — limited surge capacity")
        if climate > 50:
            factors.append(f"High natural hazard exposure in {country}")
        if geo > 50:
            factors.append(f"Geopolitical risk in {country}")

        return RiskAssessment(
            entity_id=facility_id,
            entity_type="facility",
            entity_name=name,
            country=country,
            geopolitical=round(geo, 1),
            climate=round(climate, 1),
            financial=round(fin, 1),
            cyber=round(cyber, 1),
            logistics=round(logistics, 1),
            overall=round(overall, 1),
            factors=factors,
        )

    def score_route(
        self,
        route_id: str,
        origin_country: str,
        destination_country: str,
        transport_mode: str,
        passes_through_chokepoint: bool = False,
        chokepoint_name: Optional[str] = None,
        transit_time_days: float = 5.0,
    ) -> RiskAssessment:
        """Score risk for a transport route."""
        origin_risk = self.get_country_baseline(origin_country)
        dest_risk = self.get_country_baseline(destination_country)

        # Average of origin and destination
        geo = (origin_risk["geopolitical"] + dest_risk["geopolitical"]) / 2
        climate = max(origin_risk["climate"], dest_risk["climate"])
        logistics = (origin_risk["logistics"] + dest_risk["logistics"]) / 2

        # Chokepoint penalty
        if passes_through_chokepoint:
            geo = min(100, geo + 20)
            logistics = min(100, logistics + 25)

        # Transport mode risk
        mode_risk = {"ocean": 1.2, "air": 0.8, "rail": 1.0, "road": 1.1, "multimodal": 1.15}
        mode_mult = mode_risk.get(transport_mode, 1.0)
        logistics *= mode_mult

        # Long transit = more exposure
        if transit_time_days > 20:
            logistics = min(100, logistics + (transit_time_days - 20) * 1.5)

        overall = (
            geo * self.weights["geopolitical"]
            + climate * self.weights["climate"]
            + 0.0  # routes don't have financial risk
            + 0.0  # routes don't have cyber risk
            + logistics * (self.weights["logistics"] + self.weights["financial"] + self.weights["cyber"])
        )

        factors = []
        if passes_through_chokepoint:
            factors.append(f"Passes through chokepoint: {chokepoint_name or 'unknown'}")
        if transit_time_days > 20:
            factors.append(f"Extended transit time: {transit_time_days:.0f} days")
        if geo > 40:
            factors.append("Elevated geopolitical risk on route")

        return RiskAssessment(
            entity_id=route_id,
            entity_type="route",
            entity_name=f"{origin_country} → {destination_country}",
            country=f"{origin_country}/{destination_country}",
            geopolitical=round(geo, 1),
            climate=round(climate, 1),
            financial=0.0,
            cyber=0.0,
            logistics=round(min(100, logistics), 1),
            overall=round(overall, 1),
            factors=factors,
        )

    def classify_risk(self, score: float) -> str:
        """Classify a risk score into high/medium/low."""
        if score >= 60:
            return "high"
        elif score >= 30:
            return "medium"
        return "low"

    def compute_network_risk_summary(
        self, assessments: list[RiskAssessment]
    ) -> dict:
        """Aggregate risk scores across the entire network."""
        if not assessments:
            return {
                "total_entities": 0,
                "high_risk": 0, "medium_risk": 0, "low_risk": 0,
                "avg_score": 0, "max_score": 0,
                "by_country": {}, "by_type": {},
            }

        scores = [a.overall for a in assessments]
        classifications = [self.classify_risk(a.overall) for a in assessments]

        by_country: dict[str, list[float]] = {}
        by_type: dict[str, list[float]] = {}
        for a in assessments:
            by_country.setdefault(a.country, []).append(a.overall)
            by_type.setdefault(a.entity_type, []).append(a.overall)

        return {
            "total_entities": len(assessments),
            "high_risk": classifications.count("high"),
            "medium_risk": classifications.count("medium"),
            "low_risk": classifications.count("low"),
            "avg_score": round(float(np.mean(scores)), 1),
            "max_score": round(float(np.max(scores)), 1),
            "by_country": {k: round(float(np.mean(v)), 1) for k, v in by_country.items()},
            "by_type": {k: round(float(np.mean(v)), 1) for k, v in by_type.items()},
        }

    def get_country_count(self) -> int:
        """Return total number of countries with risk profiles."""
        return len(COUNTRY_PROFILES)

    def list_countries(self, region: Optional[str] = None) -> list[dict]:
        """List all available countries, optionally filtered by region."""
        countries = get_all_countries()
        if region:
            countries = [c for c in countries if c["region"] == region or c["sub_region"] == region]
        return countries

    def search_country(self, query: str) -> list[dict]:
        """Search countries by name or ISO code."""
        results = search_countries(query)
        return [
            {
                "iso3": p.iso3,
                "name": p.name,
                "region": p.region,
                "sub_region": p.sub_region,
                "geopolitical": p.geopolitical,
                "climate": p.climate,
                "financial": p.financial,
                "cyber": p.cyber,
                "logistics": p.logistics,
            }
            for p in results
        ]
