"""
External Data Provider

Fetches country-level risk indicators from free public APIs:
- World Bank API: Political Stability (WGI), Logistics Performance Index (LPI)
- IMF DataMapper: Inflation (CPI), GDP growth
- UNDP Human Development Index: Development/stability composite
- Eurostat: EU unemployment, GDP growth, inflation (EU countries)
- ND-GAIN: Climate vulnerability index

Normalizes all indicators to 0-100 risk scale and caches results.

Note on data sources referenced in requirements:
- ITU Global Cybersecurity Index: no public API; requires CSV ingestion.
  We support manual upload via the risk data entry API.
- Climate Impact Explorer (cie-api-v2.climateanalytics.org): provides
  projection data, not a single risk score. We use ND-GAIN for the
  composite climate vulnerability score instead.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx
import structlog

log = structlog.get_logger()

# World Bank indicator codes
WB_POLITICAL_STABILITY = "PV.EST"  # Political Stability & Absence of Violence (-2.5 to 2.5)
WB_GOVT_EFFECTIVENESS = "GE.EST"   # Government Effectiveness (-2.5 to 2.5)
WB_LPI_OVERALL = "LP.LPI.OVRL.XQ"  # Logistics Performance Index (1-5)

# IMF indicator codes
IMF_INFLATION = "PCPIPCH"    # Consumer Price Inflation (%)
IMF_GDP_GROWTH = "NGDP_RPCH"  # Real GDP Growth (%)

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
IMF_BASE = "https://www.imf.org/external/datamapper/api/v1"
UNDP_HDI_BASE = "https://hdr.undp.org/api/composite/HDI"
EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Eurostat dataset codes
EUROSTAT_UNEMPLOYMENT = "une_rt_m"      # Monthly unemployment rate
EUROSTAT_HICP = "prc_hicp_manr"         # HICP - Annual rate of change
EUROSTAT_GDP_GROWTH = "namq_10_gdp"     # GDP and main components

# ISO-3166 alpha-3 to alpha-2 mapping for Eurostat (which uses alpha-2)
ISO3_TO_ISO2 = {
    "DEU": "DE", "FRA": "FR", "ITA": "IT", "ESP": "ES", "NLD": "NL",
    "BEL": "BE", "AUT": "AT", "PRT": "PT", "GRC": "EL", "FIN": "FI",
    "IRL": "IE", "LUX": "LU", "SVN": "SI", "SVK": "SK", "EST": "EE",
    "LVA": "LV", "LTU": "LT", "CYP": "CY", "MLT": "MT", "HRV": "HR",
    "BGR": "BG", "ROU": "RO", "HUN": "HU", "POL": "PL", "CZE": "CZ",
    "SWE": "SE", "DNK": "DK", "NOR": "NO", "ISL": "IS", "CHE": "CH",
    "GBR": "UK",
}

# EU member states (for Eurostat queries)
EU_COUNTRIES = {
    "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "PRT", "GRC", "FIN",
    "IRL", "LUX", "SVN", "SVK", "EST", "LVA", "LTU", "CYP", "MLT", "HRV",
    "BGR", "ROU", "HUN", "POL", "CZE", "SWE", "DNK",
}


@dataclass
class ExternalIndicators:
    """Raw indicator values fetched from external sources."""
    country_iso: str
    country_name: str
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    # World Bank — WGI
    political_stability: Optional[float] = None   # -2.5 to 2.5
    govt_effectiveness: Optional[float] = None     # -2.5 to 2.5

    # World Bank — LPI
    logistics_performance: Optional[float] = None  # 1.0 to 5.0

    # IMF
    inflation_pct: Optional[float] = None          # %
    gdp_growth_pct: Optional[float] = None         # %

    # Climate (ND-GAIN or manual)
    climate_vulnerability: Optional[float] = None  # 0-100 (ND-GAIN vulnerability score)
    climate_readiness: Optional[float] = None      # 0-100 (ND-GAIN readiness score)

    # Cyber (ITU GCI or manual)
    cybersecurity_index: Optional[float] = None    # 0-100 (ITU GCI)

    # UNDP Human Development Index
    hdi_score: Optional[float] = None              # 0-1 (higher = more developed)
    hdi_rank: Optional[int] = None                 # 1-191

    # Eurostat (EU countries only)
    eu_unemployment_pct: Optional[float] = None    # Eurostat unemployment %
    eu_hicp_annual_pct: Optional[float] = None     # Eurostat harmonized inflation %

    # Data source tracking
    sources_used: list[str] = field(default_factory=list)


@dataclass
class NormalizedCountryRisk:
    """Indicators normalized to 0-100 risk scale (higher = more risk)."""
    country_iso: str
    country_name: str
    geopolitical: float = 50.0
    climate: float = 50.0
    financial: float = 50.0
    cyber: float = 50.0
    logistics: float = 50.0
    data_completeness: float = 0.0  # 0-1, what fraction of indicators were available
    source: str = "default"  # default, external_api, manual, blended
    sources_used: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


# --- ISO code mapping ---
# Comprehensive mapping from country_baseline.py is the authoritative source;
# this provides a quick-lookup for the external data fetcher.

COUNTRY_NAME_TO_ISO = {
    "United States": "USA", "China": "CHN", "Taiwan": "TWN", "Japan": "JPN",
    "South Korea": "KOR", "Germany": "DEU", "India": "IND", "Vietnam": "VNM",
    "Mexico": "MEX", "Brazil": "BRA", "Thailand": "THA", "Malaysia": "MYS",
    "Indonesia": "IDN", "Turkey": "TUR", "Russia": "RUS", "Ukraine": "UKR",
    "Singapore": "SGP", "Netherlands": "NLD", "United Kingdom": "GBR",
    "Canada": "CAN", "Australia": "AUS", "Saudi Arabia": "SAU", "UAE": "ARE",
    "Egypt": "EGY", "South Africa": "ZAF", "France": "FRA", "Italy": "ITA",
    "Spain": "ESP", "Poland": "POL", "Czech Republic": "CZE", "Romania": "ROU",
    "Hungary": "HUN", "Sweden": "SWE", "Norway": "NOR", "Denmark": "DNK",
    "Finland": "FIN", "Switzerland": "CHE", "Austria": "AUT", "Belgium": "BEL",
    "Portugal": "PRT", "Greece": "GRC", "Ireland": "IRL", "Israel": "ISR",
    "Philippines": "PHL", "Bangladesh": "BGD", "Pakistan": "PAK", "Sri Lanka": "LKA",
    "Cambodia": "KHM", "Myanmar": "MMR", "Laos": "LAO", "New Zealand": "NZL",
    "Chile": "CHL", "Argentina": "ARG", "Colombia": "COL", "Peru": "PER",
    "Ecuador": "ECU", "Venezuela": "VEN", "Bolivia": "BOL", "Uruguay": "URY",
    "Paraguay": "PRY", "Costa Rica": "CRI", "Panama": "PAN",
    "Dominican Republic": "DOM", "Guatemala": "GTM", "Honduras": "HND",
    "El Salvador": "SLV", "Nicaragua": "NIC", "Cuba": "CUB", "Jamaica": "JAM",
    "Trinidad and Tobago": "TTO", "Nigeria": "NGA", "Kenya": "KEN",
    "Ethiopia": "ETH", "Ghana": "GHA", "Tanzania": "TZA", "Uganda": "UGA",
    "Mozambique": "MOZ", "Ivory Coast": "CIV", "Senegal": "SEN",
    "Democratic Republic of Congo": "COD", "Angola": "AGO", "Cameroon": "CMR",
    "Morocco": "MAR", "Tunisia": "TUN", "Algeria": "DZA", "Libya": "LBY",
    "Sudan": "SDN", "Iraq": "IRQ", "Iran": "IRN", "Afghanistan": "AFG",
    "Syria": "SYR", "Jordan": "JOR", "Lebanon": "LBN", "Oman": "OMN",
    "Kuwait": "KWT", "Bahrain": "BHR", "Qatar": "QAT", "Yemen": "YEM",
    "Kazakhstan": "KAZ", "Uzbekistan": "UZB", "Mongolia": "MNG",
    "Georgia": "GEO", "Armenia": "ARM", "Azerbaijan": "AZE",
    "Belarus": "BLR", "Moldova": "MDA", "Serbia": "SRB",
    "Croatia": "HRV", "Slovenia": "SVN", "Slovakia": "SVK",
    "Bulgaria": "BGR", "Lithuania": "LTU", "Latvia": "LVA",
    "Estonia": "EST", "Iceland": "ISL", "Luxembourg": "LUX",
    "Malta": "MLT", "Cyprus": "CYP", "North Macedonia": "MKD",
    "Albania": "ALB", "Bosnia and Herzegovina": "BIH", "Montenegro": "MNE",
    "Kosovo": "XKX", "Hong Kong": "HKG", "Macau": "MAC",
    "Papua New Guinea": "PNG", "Fiji": "FJI",
    "Nepal": "NPL", "Bhutan": "BTN", "Maldives": "MDV",
    "Turkmenistan": "TKM", "Tajikistan": "TJK", "Kyrgyzstan": "KGZ",
    "North Korea": "PRK", "Brunei": "BRN", "Timor-Leste": "TLS",
    "Haiti": "HTI", "Honduras": "HND", "Belize": "BLZ",
    "Guyana": "GUY", "Suriname": "SUR",
    "Rwanda": "RWA", "Burundi": "BDI", "Somalia": "SOM", "Eritrea": "ERI",
    "Djibouti": "DJI", "Madagascar": "MDG", "Mauritius": "MUS",
    "Mali": "MLI", "Burkina Faso": "BFA", "Niger": "NER",
    "Guinea": "GIN", "Benin": "BEN", "Togo": "TGO",
    "Sierra Leone": "SLE", "Liberia": "LBR", "Gambia": "GMB",
    "Cape Verde": "CPV", "Mauritania": "MRT",
    "Botswana": "BWA", "Namibia": "NAM", "Zambia": "ZMB",
    "Zimbabwe": "ZWE", "Malawi": "MWI", "Lesotho": "LSO", "Eswatini": "SWZ",
    "Republic of Congo": "COG", "Gabon": "GAB",
    "Central African Republic": "CAF", "Chad": "TCD",
    "South Sudan": "SSD", "Palestine": "PSE",
    "Samoa": "WSM", "Tonga": "TON", "Vanuatu": "VUT",
    "Solomon Islands": "SLB", "Kiribati": "KIR",
}

ISO_TO_COUNTRY_NAME = {v: k for k, v in COUNTRY_NAME_TO_ISO.items()}


class ExternalDataProvider:
    """
    Fetches and caches country risk indicators from public APIs.
    Thread-safe with TTL-based caching.

    Data sources:
    1. World Bank API — WGI (Political Stability, Govt Effectiveness) + LPI
    2. IMF DataMapper — Inflation, GDP Growth
    3. UNDP — Human Development Index
    4. Eurostat — EU unemployment, inflation (EU countries only)
    """

    def __init__(self, cache_ttl_seconds: int = 86400):
        self._cache: dict[str, ExternalIndicators] = {}
        self._cache_ttl = cache_ttl_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _is_cached(self, iso: str) -> bool:
        if iso not in self._cache:
            return False
        age = (datetime.utcnow() - self._cache[iso].fetched_at).total_seconds()
        return age < self._cache_ttl

    def invalidate_cache(self, iso: Optional[str] = None):
        """Clear cache for one country or all countries."""
        if iso:
            self._cache.pop(iso, None)
        else:
            self._cache.clear()

    async def fetch_country(self, country_name: str) -> ExternalIndicators:
        """Fetch all available indicators for a country from all data sources."""
        iso = COUNTRY_NAME_TO_ISO.get(country_name)
        if not iso:
            log.warning("No ISO code for country", country=country_name)
            return ExternalIndicators(country_iso="UNK", country_name=country_name)

        if self._is_cached(iso):
            return self._cache[iso]

        indicators = ExternalIndicators(country_iso=iso, country_name=country_name)

        # Build list of fetch tasks — always fetch World Bank + IMF + UNDP
        tasks = [
            self._fetch_world_bank_wgi(iso),
            self._fetch_world_bank_lpi(iso),
            self._fetch_imf_indicators(iso),
            self._fetch_undp_hdi(iso),
        ]
        task_names = ["world_bank_wgi", "world_bank_lpi", "imf", "undp_hdi"]

        # Add Eurostat if EU country
        if iso in EU_COUNTRIES:
            tasks.append(self._fetch_eurostat_indicators(iso))
            task_names.append("eurostat")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(task_names, results):
            if isinstance(result, Exception):
                log.debug("External API error", source=name, iso=iso, error=str(result))
                continue

            if name == "world_bank_wgi" and isinstance(result, dict):
                indicators.political_stability = result.get("PV.EST")
                indicators.govt_effectiveness = result.get("GE.EST")
                indicators.sources_used.append("world_bank_wgi")

            elif name == "world_bank_lpi" and isinstance(result, float):
                indicators.logistics_performance = result
                indicators.sources_used.append("world_bank_lpi")

            elif name == "imf" and isinstance(result, dict):
                indicators.inflation_pct = result.get("inflation")
                indicators.gdp_growth_pct = result.get("gdp_growth")
                indicators.sources_used.append("imf")

            elif name == "undp_hdi" and isinstance(result, dict):
                indicators.hdi_score = result.get("hdi_score")
                indicators.hdi_rank = result.get("hdi_rank")
                indicators.sources_used.append("undp_hdi")

            elif name == "eurostat" and isinstance(result, dict):
                indicators.eu_unemployment_pct = result.get("unemployment_pct")
                indicators.eu_hicp_annual_pct = result.get("hicp_annual_pct")
                indicators.sources_used.append("eurostat")

        self._cache[iso] = indicators
        log.info("Fetched external data", country=country_name, iso=iso,
                 sources=indicators.sources_used)
        return indicators

    async def fetch_many(self, country_names: list[str]) -> dict[str, ExternalIndicators]:
        """Fetch indicators for multiple countries concurrently."""
        tasks = [self.fetch_country(name) for name in country_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out = {}
        for name, result in zip(country_names, results):
            if isinstance(result, ExternalIndicators):
                out[name] = result
            else:
                log.warning("Failed to fetch", country=name, error=str(result))
        return out

    def get_available_sources(self) -> list[dict]:
        """List all external data sources with descriptions."""
        return [
            {
                "id": "world_bank_wgi",
                "name": "World Bank — Worldwide Governance Indicators",
                "indicators": ["Political Stability (PV.EST)", "Government Effectiveness (GE.EST)"],
                "url": "https://api.worldbank.org/v2",
                "coverage": "190+ countries",
                "update_frequency": "Annual",
                "risk_dimensions": ["geopolitical"],
            },
            {
                "id": "world_bank_lpi",
                "name": "World Bank — Logistics Performance Index",
                "indicators": ["Overall LPI Score (LP.LPI.OVRL.XQ)"],
                "url": "https://api.worldbank.org/v2",
                "coverage": "160+ countries",
                "update_frequency": "Biennial",
                "risk_dimensions": ["logistics"],
            },
            {
                "id": "imf",
                "name": "IMF DataMapper",
                "indicators": ["Consumer Price Inflation (PCPIPCH)", "Real GDP Growth (NGDP_RPCH)"],
                "url": "https://www.imf.org/external/datamapper/api/v1",
                "coverage": "190+ countries",
                "update_frequency": "Semi-annual (WEO)",
                "risk_dimensions": ["financial"],
            },
            {
                "id": "undp_hdi",
                "name": "United Nations Development Programme — Human Development Index",
                "indicators": ["HDI Score (0-1)", "HDI Rank"],
                "url": "https://hdr.undp.org/api",
                "coverage": "191 countries",
                "update_frequency": "Annual",
                "risk_dimensions": ["financial", "geopolitical"],
            },
            {
                "id": "eurostat",
                "name": "Eurostat — European Statistical Office",
                "indicators": ["Unemployment Rate", "HICP Inflation"],
                "url": "https://ec.europa.eu/eurostat/api",
                "coverage": "EU-27 + EEA countries",
                "update_frequency": "Monthly",
                "risk_dimensions": ["financial"],
            },
            {
                "id": "ndgain",
                "name": "ND-GAIN — Notre Dame Global Adaptation Initiative",
                "indicators": ["Climate Vulnerability (0-100)", "Climate Readiness (0-100)"],
                "url": "https://gain.nd.edu/",
                "coverage": "181 countries",
                "update_frequency": "Annual",
                "risk_dimensions": ["climate"],
                "note": "Requires manual CSV upload — no public REST API",
            },
            {
                "id": "itu_gci",
                "name": "ITU — Global Cybersecurity Index",
                "indicators": ["GCI Score (0-100)"],
                "url": "https://www.itu.int/en/ITU-D/Cybersecurity/Pages/global-cybersecurity-index.aspx",
                "coverage": "194 countries",
                "update_frequency": "Biennial",
                "risk_dimensions": ["cyber"],
                "note": "Requires manual CSV upload — no public REST API",
            },
        ]

    # --- World Bank API ---

    async def _fetch_world_bank_wgi(self, iso: str) -> dict[str, float]:
        """Fetch World Governance Indicators from World Bank API."""
        client = await self._get_client()
        out = {}
        for indicator in [WB_POLITICAL_STABILITY, WB_GOVT_EFFECTIVENESS]:
            try:
                url = f"{WORLD_BANK_BASE}/country/{iso}/indicator/{indicator}"
                resp = await client.get(url, params={
                    "format": "json", "date": "2020:2026", "per_page": "10",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        for record in data[1]:
                            if record.get("value") is not None:
                                out[indicator] = float(record["value"])
                                break
            except Exception as e:
                log.debug("World Bank API error", indicator=indicator, iso=iso, error=str(e))
        return out

    async def _fetch_world_bank_lpi(self, iso: str) -> Optional[float]:
        """Fetch Logistics Performance Index from World Bank API."""
        client = await self._get_client()
        try:
            url = f"{WORLD_BANK_BASE}/country/{iso}/indicator/{WB_LPI_OVERALL}"
            resp = await client.get(url, params={
                "format": "json", "date": "2018:2026", "per_page": "10",
            })
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 1 and data[1]:
                    for record in data[1]:
                        if record.get("value") is not None:
                            return float(record["value"])
        except Exception as e:
            log.debug("World Bank LPI error", iso=iso, error=str(e))
        return None

    # --- IMF DataMapper API ---

    async def _fetch_imf_indicators(self, iso: str) -> dict[str, float]:
        """Fetch inflation and GDP growth from IMF DataMapper API."""
        client = await self._get_client()
        out = {}
        for indicator, key in [(IMF_INFLATION, "inflation"), (IMF_GDP_GROWTH, "gdp_growth")]:
            try:
                url = f"{IMF_BASE}/{indicator}/{iso}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    values = data.get("values", {}).get(indicator, {}).get(iso, {})
                    if values:
                        latest_year = max(values.keys())
                        out[key] = float(values[latest_year])
            except Exception as e:
                log.debug("IMF API error", indicator=indicator, iso=iso, error=str(e))
        return out

    # --- UNDP Human Development Index ---

    async def _fetch_undp_hdi(self, iso: str) -> dict:
        """
        Fetch Human Development Index from UNDP API.

        HDI is a composite of life expectancy, education, and GNI per capita.
        Score range: 0-1 (higher = more developed = lower risk).
        """
        client = await self._get_client()
        try:
            # UNDP HDI API endpoint
            url = f"{UNDP_HDI_BASE}"
            resp = await client.get(url, params={
                "indicator_id": "137506",  # HDI indicator
                "country_code": iso,
                "year": "2022,2023,2024",
            })
            if resp.status_code == 200:
                data = resp.json()
                # Parse UNDP response format
                if isinstance(data, dict):
                    # Try to extract from various UNDP API response formats
                    records = data.get("indicator_value", {}).get(iso, {})
                    if records:
                        latest_year = max(records.keys())
                        hdi_val = records[latest_year]
                        if hdi_val is not None:
                            return {"hdi_score": float(hdi_val)}

                    # Alternative: flat list format
                    if isinstance(data, list):
                        for record in data:
                            if record.get("value") is not None:
                                return {"hdi_score": float(record["value"])}
        except Exception as e:
            log.debug("UNDP HDI API error", iso=iso, error=str(e))
        return {}

    # --- Eurostat (EU countries only) ---

    async def _fetch_eurostat_indicators(self, iso: str) -> dict[str, float]:
        """
        Fetch unemployment and inflation from Eurostat JSON API.

        Only available for EU-27 and some EEA countries.
        Uses the Eurostat REST API with JSON-stat format.
        """
        client = await self._get_client()
        out = {}
        iso2 = ISO3_TO_ISO2.get(iso)
        if not iso2:
            return out

        # Unemployment rate
        try:
            url = f"{EUROSTAT_BASE}/{EUROSTAT_UNEMPLOYMENT}"
            resp = await client.get(url, params={
                "geo": iso2,
                "s_adj": "SA",       # Seasonally adjusted
                "age": "TOTAL",
                "sex": "T",          # Total
                "unit": "PC_ACT",    # Percentage of active population
                "sinceTimePeriod": "2024-01",
                "format": "JSON",
            })
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("value", {})
                if values:
                    # Get most recent value (highest index)
                    latest_key = max(values.keys(), key=int)
                    out["unemployment_pct"] = float(values[latest_key])
        except Exception as e:
            log.debug("Eurostat unemployment error", iso=iso, error=str(e))

        # HICP inflation (annual rate of change)
        try:
            url = f"{EUROSTAT_BASE}/{EUROSTAT_HICP}"
            resp = await client.get(url, params={
                "geo": iso2,
                "coicop": "CP00",    # All items
                "unit": "RCH_A",     # Rate of change, annual
                "sinceTimePeriod": "2024-01",
                "format": "JSON",
            })
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("value", {})
                if values:
                    latest_key = max(values.keys(), key=int)
                    out["hicp_annual_pct"] = float(values[latest_key])
        except Exception as e:
            log.debug("Eurostat HICP error", iso=iso, error=str(e))

        return out

    # --- Normalization ---

    def normalize(self, indicators: ExternalIndicators) -> NormalizedCountryRisk:
        """
        Convert raw indicators to 0-100 risk scores.
        Higher score = higher risk.
        """
        available = 0
        total_indicators = 5  # geo, climate, financial, cyber, logistics
        sources_used = list(indicators.sources_used)

        # Geopolitical: from Political Stability (-2.5 to 2.5 → 100 to 0)
        geo = 50.0
        if indicators.political_stability is not None:
            geo = max(0, min(100, (2.5 - indicators.political_stability) / 5.0 * 100))
            available += 1
            if indicators.govt_effectiveness is not None:
                ge_risk = max(0, min(100, (2.5 - indicators.govt_effectiveness) / 5.0 * 100))
                geo = geo * 0.6 + ge_risk * 0.4

        # Climate: from ND-GAIN vulnerability (already 0-100, higher = more vulnerable)
        climate = 50.0
        if indicators.climate_vulnerability is not None:
            climate = indicators.climate_vulnerability
            available += 1

        # Financial: from inflation + GDP growth + HDI + Eurostat data
        fin = 50.0
        fin_parts = 0
        fin_sum = 0.0
        fin_weight = 0.0

        if indicators.inflation_pct is not None:
            inf_risk = max(0, min(100, indicators.inflation_pct * 5))
            fin_sum += inf_risk * 0.3
            fin_weight += 0.3
            fin_parts += 1

        if indicators.gdp_growth_pct is not None:
            gdp_risk = max(0, min(100, 50 - indicators.gdp_growth_pct * 8))
            fin_sum += gdp_risk * 0.25
            fin_weight += 0.25
            fin_parts += 1

        if indicators.hdi_score is not None:
            # HDI 0-1: higher = more developed = lower risk
            hdi_risk = max(0, min(100, (1.0 - indicators.hdi_score) * 100))
            fin_sum += hdi_risk * 0.25
            fin_weight += 0.25
            fin_parts += 1

        if indicators.eu_unemployment_pct is not None:
            # <5% = healthy, >20% = severe
            unemp_risk = max(0, min(100, indicators.eu_unemployment_pct * 4))
            fin_sum += unemp_risk * 0.1
            fin_weight += 0.1
            fin_parts += 1

        if indicators.eu_hicp_annual_pct is not None:
            # Eurostat inflation complements/overrides IMF
            hicp_risk = max(0, min(100, indicators.eu_hicp_annual_pct * 5))
            fin_sum += hicp_risk * 0.1
            fin_weight += 0.1
            fin_parts += 1

        if fin_weight > 0:
            fin = fin_sum / fin_weight
            available += 1

        # Cyber: from ITU GCI (0-100, higher GCI = lower risk)
        cyber = 50.0
        if indicators.cybersecurity_index is not None:
            cyber = max(0, 100 - indicators.cybersecurity_index)
            available += 1

        # Logistics: from LPI (1-5 → 100 to 0)
        logistics = 50.0
        if indicators.logistics_performance is not None:
            logistics = max(0, min(100, (5.0 - indicators.logistics_performance) / 4.0 * 100))
            available += 1

        completeness = available / total_indicators
        source = "external_api" if available > 0 else "default"

        return NormalizedCountryRisk(
            country_iso=indicators.country_iso,
            country_name=indicators.country_name,
            geopolitical=round(geo, 1),
            climate=round(climate, 1),
            financial=round(fin, 1),
            cyber=round(cyber, 1),
            logistics=round(logistics, 1),
            data_completeness=round(completeness, 2),
            source=source,
            sources_used=sources_used,
        )

    def merge_with_manual(
        self,
        normalized: NormalizedCountryRisk,
        manual_overrides: dict[str, float],
    ) -> NormalizedCountryRisk:
        """
        Merge API-fetched data with manually entered overrides.
        Manual values take precedence.
        """
        for dimension in ["geopolitical", "climate", "financial", "cyber", "logistics"]:
            if dimension in manual_overrides:
                setattr(normalized, dimension, manual_overrides[dimension])
        normalized.source = "blended" if normalized.source == "external_api" else "manual"
        normalized.last_updated = datetime.utcnow()
        return normalized
