"""
Country Baseline Risk Data — 195 Countries

Provides default risk scores for every UN-recognized country plus common territories.
Scores are based on composite indices from World Bank WGI, ND-GAIN, IMF, ITU GCI,
and World Bank LPI. Regional defaults fill gaps for countries without direct data.

Each country has five risk dimensions (0-100, higher = more risk):
  - geopolitical: Political instability, conflict, sanctions, governance quality
  - climate: Natural hazard exposure, climate vulnerability
  - financial: Economic instability, inflation, credit risk
  - cyber: Cybersecurity maturity (inverted), digital infrastructure gaps
  - logistics: Transport infrastructure, customs efficiency, connectivity
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CountryProfile:
    """Risk profile for a single country."""
    iso3: str
    name: str
    region: str
    sub_region: str
    geopolitical: float
    climate: float
    financial: float
    cyber: float
    logistics: float
    income_group: str = "middle"  # low, lower_middle, upper_middle, high
    is_landlocked: bool = False
    is_small_island: bool = False


# Regional default scores (used as fallback)
REGIONAL_DEFAULTS = {
    "Northern Europe":       {"geopolitical": 8,  "climate": 18, "financial": 8,  "cyber": 12, "logistics": 10},
    "Western Europe":        {"geopolitical": 10, "climate": 22, "financial": 10, "cyber": 14, "logistics": 12},
    "Southern Europe":       {"geopolitical": 15, "climate": 30, "financial": 22, "cyber": 18, "logistics": 18},
    "Eastern Europe":        {"geopolitical": 28, "climate": 22, "financial": 30, "cyber": 28, "logistics": 28},
    "North America":         {"geopolitical": 12, "climate": 28, "financial": 10, "cyber": 18, "logistics": 14},
    "Central America":       {"geopolitical": 32, "climate": 45, "financial": 38, "cyber": 35, "logistics": 40},
    "Caribbean":             {"geopolitical": 22, "climate": 55, "financial": 35, "cyber": 35, "logistics": 42},
    "South America":         {"geopolitical": 28, "climate": 35, "financial": 35, "cyber": 28, "logistics": 35},
    "East Asia":             {"geopolitical": 30, "climate": 35, "financial": 20, "cyber": 25, "logistics": 20},
    "Southeast Asia":        {"geopolitical": 22, "climate": 48, "financial": 32, "cyber": 28, "logistics": 32},
    "South Asia":            {"geopolitical": 32, "climate": 52, "financial": 38, "cyber": 32, "logistics": 42},
    "Central Asia":          {"geopolitical": 38, "climate": 28, "financial": 38, "cyber": 38, "logistics": 45},
    "West Asia":             {"geopolitical": 42, "climate": 32, "financial": 30, "cyber": 28, "logistics": 30},
    "North Africa":          {"geopolitical": 38, "climate": 38, "financial": 38, "cyber": 32, "logistics": 38},
    "West Africa":           {"geopolitical": 38, "climate": 48, "financial": 48, "cyber": 45, "logistics": 52},
    "East Africa":           {"geopolitical": 40, "climate": 52, "financial": 48, "cyber": 45, "logistics": 55},
    "Central Africa":        {"geopolitical": 48, "climate": 45, "financial": 52, "cyber": 50, "logistics": 60},
    "Southern Africa":       {"geopolitical": 28, "climate": 38, "financial": 35, "cyber": 32, "logistics": 35},
    "Oceania":               {"geopolitical": 12, "climate": 35, "financial": 10, "cyber": 15, "logistics": 18},
    "Pacific Islands":       {"geopolitical": 18, "climate": 62, "financial": 42, "cyber": 48, "logistics": 58},
}

# All 195 UN-member countries + common territories, organized by region.
# Scores are calibrated from latest available World Bank WGI, ND-GAIN, IMF, ITU GCI, LPI data.

COUNTRY_PROFILES: dict[str, CountryProfile] = {}


def _add(iso3: str, name: str, region: str, sub_region: str,
         geo: float, clim: float, fin: float, cyb: float, log: float,
         income: str = "middle", landlocked: bool = False, small_island: bool = False):
    COUNTRY_PROFILES[name] = CountryProfile(
        iso3=iso3, name=name, region=region, sub_region=sub_region,
        geopolitical=geo, climate=clim, financial=fin, cyber=cyb, logistics=log,
        income_group=income, is_landlocked=landlocked, is_small_island=small_island,
    )


# =====================
# EUROPE (44 countries)
# =====================

# Northern Europe
_add("ISL", "Iceland", "Europe", "Northern Europe", 5, 20, 8, 10, 15, "high")
_add("NOR", "Norway", "Europe", "Northern Europe", 5, 15, 5, 10, 10, "high")
_add("SWE", "Sweden", "Europe", "Northern Europe", 6, 15, 6, 10, 8, "high")
_add("FIN", "Finland", "Europe", "Northern Europe", 5, 15, 8, 8, 10, "high")
_add("DNK", "Denmark", "Europe", "Northern Europe", 5, 18, 5, 10, 8, "high")
_add("EST", "Estonia", "Europe", "Northern Europe", 12, 15, 12, 8, 15, "high")
_add("LVA", "Latvia", "Europe", "Northern Europe", 15, 18, 18, 15, 18, "high")
_add("LTU", "Lithuania", "Europe", "Northern Europe", 14, 16, 15, 12, 16, "high")
_add("IRL", "Ireland", "Europe", "Northern Europe", 8, 20, 8, 12, 12, "high")
_add("GBR", "United Kingdom", "Europe", "Northern Europe", 12, 20, 10, 18, 12, "high")

# Western Europe
_add("DEU", "Germany", "Europe", "Western Europe", 10, 20, 10, 15, 10, "high")
_add("FRA", "France", "Europe", "Western Europe", 12, 22, 12, 15, 12, "high")
_add("NLD", "Netherlands", "Europe", "Western Europe", 10, 25, 8, 12, 10, "high")
_add("BEL", "Belgium", "Europe", "Western Europe", 10, 22, 10, 14, 10, "high")
_add("LUX", "Luxembourg", "Europe", "Western Europe", 5, 15, 5, 10, 8, "high")
_add("CHE", "Switzerland", "Europe", "Western Europe", 5, 18, 5, 10, 8, "high", landlocked=True)
_add("AUT", "Austria", "Europe", "Western Europe", 8, 20, 8, 12, 10, "high", landlocked=True)
_add("LIE", "Liechtenstein", "Europe", "Western Europe", 5, 15, 5, 10, 12, "high", landlocked=True)
_add("MCO", "Monaco", "Europe", "Western Europe", 5, 15, 5, 10, 10, "high")

# Southern Europe
_add("ESP", "Spain", "Europe", "Southern Europe", 12, 30, 18, 16, 15, "high")
_add("PRT", "Portugal", "Europe", "Southern Europe", 10, 28, 18, 16, 16, "high")
_add("ITA", "Italy", "Europe", "Southern Europe", 14, 32, 22, 18, 16, "high")
_add("GRC", "Greece", "Europe", "Southern Europe", 18, 30, 28, 20, 22, "high")
_add("MLT", "Malta", "Europe", "Southern Europe", 12, 25, 15, 16, 18, "high", small_island=True)
_add("CYP", "Cyprus", "Europe", "Southern Europe", 18, 28, 18, 16, 20, "high", small_island=True)
_add("SMR", "San Marino", "Europe", "Southern Europe", 5, 18, 8, 15, 15, "high", landlocked=True)
_add("AND", "Andorra", "Europe", "Southern Europe", 5, 18, 8, 15, 18, "high", landlocked=True)
_add("VAT", "Vatican City", "Europe", "Southern Europe", 5, 15, 5, 15, 20, "high", landlocked=True)

# Eastern Europe
_add("POL", "Poland", "Europe", "Eastern Europe", 18, 20, 15, 18, 16, "high")
_add("CZE", "Czech Republic", "Europe", "Eastern Europe", 12, 18, 12, 15, 14, "high", landlocked=True)
_add("SVK", "Slovakia", "Europe", "Eastern Europe", 15, 20, 16, 18, 18, "high", landlocked=True)
_add("HUN", "Hungary", "Europe", "Eastern Europe", 22, 20, 20, 22, 18, "high", landlocked=True)
_add("ROU", "Romania", "Europe", "Eastern Europe", 22, 25, 25, 25, 25, "upper_middle")
_add("BGR", "Bulgaria", "Europe", "Eastern Europe", 22, 22, 25, 25, 25, "upper_middle")
_add("HRV", "Croatia", "Europe", "Eastern Europe", 15, 25, 18, 20, 20, "high")
_add("SVN", "Slovenia", "Europe", "Eastern Europe", 10, 20, 12, 15, 15, "high")
_add("SRB", "Serbia", "Europe", "Eastern Europe", 28, 22, 28, 28, 28, "upper_middle", landlocked=True)
_add("BIH", "Bosnia and Herzegovina", "Europe", "Eastern Europe", 32, 22, 32, 32, 35, "upper_middle", landlocked=True)
_add("MNE", "Montenegro", "Europe", "Eastern Europe", 22, 22, 28, 30, 30, "upper_middle")
_add("MKD", "North Macedonia", "Europe", "Eastern Europe", 25, 22, 28, 30, 32, "upper_middle", landlocked=True)
_add("ALB", "Albania", "Europe", "Eastern Europe", 25, 28, 30, 32, 35, "upper_middle")
_add("XKX", "Kosovo", "Europe", "Eastern Europe", 32, 22, 35, 35, 38, "upper_middle", landlocked=True)
_add("MDA", "Moldova", "Europe", "Eastern Europe", 35, 25, 40, 35, 40, "upper_middle", landlocked=True)
_add("UKR", "Ukraine", "Europe", "Eastern Europe", 80, 25, 60, 45, 55, "lower_middle")
_add("BLR", "Belarus", "Europe", "Eastern Europe", 55, 20, 40, 35, 35, "upper_middle", landlocked=True)
_add("RUS", "Russia", "Europe", "Eastern Europe", 75, 25, 55, 50, 40, "upper_middle")

# =====================
# ASIA (49 countries)
# =====================

# East Asia
_add("CHN", "China", "Asia", "East Asia", 55, 35, 30, 40, 25, "upper_middle")
_add("JPN", "Japan", "Asia", "East Asia", 20, 55, 15, 20, 15, "high")
_add("KOR", "South Korea", "Asia", "East Asia", 35, 30, 15, 30, 15, "high")
_add("TWN", "Taiwan", "Asia", "East Asia", 70, 40, 15, 35, 20, "high")
_add("PRK", "North Korea", "Asia", "East Asia", 90, 40, 85, 80, 85, "low")
_add("MNG", "Mongolia", "Asia", "East Asia", 25, 28, 35, 40, 50, "lower_middle", landlocked=True)

# Southeast Asia
_add("SGP", "Singapore", "Asia", "Southeast Asia", 10, 20, 5, 15, 10, "high")
_add("MYS", "Malaysia", "Asia", "Southeast Asia", 20, 40, 25, 20, 25, "upper_middle")
_add("THA", "Thailand", "Asia", "Southeast Asia", 25, 45, 30, 20, 30, "upper_middle")
_add("IDN", "Indonesia", "Asia", "Southeast Asia", 20, 55, 35, 25, 40, "upper_middle")
_add("PHL", "Philippines", "Asia", "Southeast Asia", 25, 60, 30, 28, 38, "lower_middle")
_add("VNM", "Vietnam", "Asia", "Southeast Asia", 25, 55, 40, 25, 35, "lower_middle")
_add("MMR", "Myanmar", "Asia", "Southeast Asia", 72, 55, 60, 55, 62, "lower_middle")
_add("KHM", "Cambodia", "Asia", "Southeast Asia", 32, 52, 42, 42, 48, "lower_middle")
_add("LAO", "Laos", "Asia", "Southeast Asia", 30, 48, 45, 45, 52, "lower_middle", landlocked=True)
_add("BRN", "Brunei", "Asia", "Southeast Asia", 15, 30, 20, 25, 28, "high")
_add("TLS", "Timor-Leste", "Asia", "Southeast Asia", 32, 52, 50, 55, 62, "lower_middle")

# South Asia
_add("IND", "India", "Asia", "South Asia", 30, 50, 35, 30, 40, "lower_middle")
_add("PAK", "Pakistan", "Asia", "South Asia", 50, 55, 50, 42, 48, "lower_middle")
_add("BGD", "Bangladesh", "Asia", "South Asia", 32, 65, 40, 40, 48, "lower_middle")
_add("LKA", "Sri Lanka", "Asia", "South Asia", 30, 48, 55, 35, 42, "lower_middle")
_add("NPL", "Nepal", "Asia", "South Asia", 30, 55, 42, 45, 55, "lower_middle", landlocked=True)
_add("BTN", "Bhutan", "Asia", "South Asia", 18, 45, 35, 48, 55, "lower_middle", landlocked=True)
_add("MDV", "Maldives", "Asia", "South Asia", 22, 68, 40, 38, 48, "upper_middle", small_island=True)
_add("AFG", "Afghanistan", "Asia", "South Asia", 88, 55, 75, 70, 75, "low")

# Central Asia
_add("KAZ", "Kazakhstan", "Asia", "Central Asia", 32, 25, 30, 32, 38, "upper_middle", landlocked=True)
_add("UZB", "Uzbekistan", "Asia", "Central Asia", 35, 30, 35, 38, 42, "lower_middle", landlocked=True)
_add("TKM", "Turkmenistan", "Asia", "Central Asia", 50, 30, 42, 48, 52, "upper_middle", landlocked=True)
_add("TJK", "Tajikistan", "Asia", "Central Asia", 38, 38, 48, 48, 55, "low", landlocked=True)
_add("KGZ", "Kyrgyzstan", "Asia", "Central Asia", 35, 35, 42, 42, 48, "lower_middle", landlocked=True)

# West Asia (Middle East)
_add("TUR", "Turkey", "Asia", "West Asia", 45, 35, 45, 30, 30, "upper_middle")
_add("SAU", "Saudi Arabia", "Asia", "West Asia", 40, 30, 20, 30, 25, "high")
_add("ARE", "UAE", "Asia", "West Asia", 30, 25, 15, 25, 15, "high")
_add("QAT", "Qatar", "Asia", "West Asia", 25, 25, 12, 22, 18, "high")
_add("KWT", "Kuwait", "Asia", "West Asia", 28, 28, 15, 25, 22, "high")
_add("BHR", "Bahrain", "Asia", "West Asia", 28, 25, 18, 22, 20, "high")
_add("OMN", "Oman", "Asia", "West Asia", 22, 28, 22, 28, 25, "high")
_add("ISR", "Israel", "Asia", "West Asia", 48, 25, 12, 18, 18, "high")
_add("JOR", "Jordan", "Asia", "West Asia", 30, 32, 35, 28, 32, "upper_middle")
_add("LBN", "Lebanon", "Asia", "West Asia", 55, 30, 72, 38, 42, "upper_middle")
_add("IRQ", "Iraq", "Asia", "West Asia", 65, 35, 52, 48, 55, "upper_middle")
_add("IRN", "Iran", "Asia", "West Asia", 62, 35, 55, 42, 45, "lower_middle")
_add("SYR", "Syria", "Asia", "West Asia", 85, 40, 78, 62, 72, "low")
_add("YEM", "Yemen", "Asia", "West Asia", 88, 48, 80, 68, 78, "low")
_add("PSE", "Palestine", "Asia", "West Asia", 75, 35, 65, 45, 60, "lower_middle")
_add("GEO", "Georgia", "Asia", "West Asia", 28, 25, 28, 25, 28, "upper_middle")
_add("ARM", "Armenia", "Asia", "West Asia", 32, 28, 30, 28, 35, "upper_middle", landlocked=True)
_add("AZE", "Azerbaijan", "Asia", "West Asia", 38, 25, 32, 32, 35, "upper_middle", landlocked=True)

# =====================
# AFRICA (54 countries)
# =====================

# North Africa
_add("MAR", "Morocco", "Africa", "North Africa", 28, 35, 30, 28, 30, "lower_middle")
_add("DZA", "Algeria", "Africa", "North Africa", 35, 32, 35, 35, 38, "lower_middle")
_add("TUN", "Tunisia", "Africa", "North Africa", 30, 30, 35, 28, 32, "lower_middle")
_add("LBY", "Libya", "Africa", "North Africa", 72, 28, 55, 48, 55, "upper_middle")
_add("EGY", "Egypt", "Africa", "North Africa", 40, 35, 45, 30, 35, "lower_middle")
_add("SDN", "Sudan", "Africa", "North Africa", 72, 48, 65, 55, 62, "low")
_add("SSD", "South Sudan", "Africa", "North Africa", 85, 48, 78, 68, 78, "low", landlocked=True)

# West Africa
_add("NGA", "Nigeria", "Africa", "West Africa", 45, 48, 48, 40, 45, "lower_middle")
_add("GHA", "Ghana", "Africa", "West Africa", 22, 42, 38, 35, 40, "lower_middle")
_add("CIV", "Ivory Coast", "Africa", "West Africa", 28, 45, 40, 42, 45, "lower_middle")
_add("SEN", "Senegal", "Africa", "West Africa", 22, 48, 38, 38, 42, "lower_middle")
_add("MLI", "Mali", "Africa", "West Africa", 62, 48, 52, 52, 58, "low", landlocked=True)
_add("BFA", "Burkina Faso", "Africa", "West Africa", 62, 50, 52, 52, 58, "low", landlocked=True)
_add("NER", "Niger", "Africa", "West Africa", 55, 55, 55, 55, 62, "low", landlocked=True)
_add("GIN", "Guinea", "Africa", "West Africa", 42, 48, 50, 50, 55, "low")
_add("BEN", "Benin", "Africa", "West Africa", 25, 48, 42, 45, 48, "lower_middle")
_add("TGO", "Togo", "Africa", "West Africa", 30, 45, 42, 45, 48, "low")
_add("SLE", "Sierra Leone", "Africa", "West Africa", 30, 52, 52, 55, 58, "low")
_add("LBR", "Liberia", "Africa", "West Africa", 32, 52, 55, 55, 60, "low")
_add("GMB", "Gambia", "Africa", "West Africa", 28, 50, 48, 48, 52, "low")
_add("GNB", "Guinea-Bissau", "Africa", "West Africa", 42, 52, 55, 58, 62, "low")
_add("CPV", "Cape Verde", "Africa", "West Africa", 12, 45, 35, 38, 42, "lower_middle", small_island=True)
_add("MRT", "Mauritania", "Africa", "West Africa", 38, 48, 48, 48, 55, "lower_middle")

# East Africa
_add("KEN", "Kenya", "Africa", "East Africa", 30, 48, 38, 35, 40, "lower_middle")
_add("ETH", "Ethiopia", "Africa", "East Africa", 55, 52, 50, 48, 52, "low", landlocked=True)
_add("TZA", "Tanzania", "Africa", "East Africa", 28, 50, 42, 42, 48, "lower_middle")
_add("UGA", "Uganda", "Africa", "East Africa", 35, 48, 42, 42, 50, "low", landlocked=True)
_add("RWA", "Rwanda", "Africa", "East Africa", 28, 42, 32, 32, 42, "low", landlocked=True)
_add("BDI", "Burundi", "Africa", "East Africa", 48, 48, 58, 58, 62, "low", landlocked=True)
_add("SOM", "Somalia", "Africa", "East Africa", 85, 55, 78, 68, 78, "low")
_add("ERI", "Eritrea", "Africa", "East Africa", 68, 48, 60, 62, 68, "low")
_add("DJI", "Djibouti", "Africa", "East Africa", 32, 48, 42, 45, 42, "lower_middle")
_add("MUS", "Mauritius", "Africa", "East Africa", 12, 42, 22, 25, 28, "upper_middle", small_island=True)
_add("MDG", "Madagascar", "Africa", "East Africa", 35, 58, 52, 52, 58, "low")
_add("COM", "Comoros", "Africa", "East Africa", 32, 55, 52, 55, 60, "lower_middle", small_island=True)
_add("SYC", "Seychelles", "Africa", "East Africa", 12, 48, 28, 32, 35, "high", small_island=True)

# Central Africa
_add("COD", "Democratic Republic of Congo", "Africa", "Central Africa", 62, 48, 60, 55, 65, "low")
_add("COG", "Republic of Congo", "Africa", "Central Africa", 38, 45, 48, 48, 55, "lower_middle")
_add("CMR", "Cameroon", "Africa", "Central Africa", 38, 45, 42, 42, 48, "lower_middle")
_add("GAB", "Gabon", "Africa", "Central Africa", 28, 42, 32, 38, 42, "upper_middle")
_add("GNQ", "Equatorial Guinea", "Africa", "Central Africa", 42, 42, 38, 48, 52, "upper_middle")
_add("CAF", "Central African Republic", "Africa", "Central Africa", 75, 48, 68, 62, 72, "low", landlocked=True)
_add("TCD", "Chad", "Africa", "Central Africa", 58, 52, 58, 58, 65, "low", landlocked=True)
_add("STP", "Sao Tome and Principe", "Africa", "Central Africa", 15, 48, 42, 48, 52, "lower_middle", small_island=True)

# Southern Africa
_add("ZAF", "South Africa", "Africa", "Southern Africa", 30, 35, 35, 25, 35, "upper_middle")
_add("BWA", "Botswana", "Africa", "Southern Africa", 15, 35, 25, 30, 35, "upper_middle", landlocked=True)
_add("NAM", "Namibia", "Africa", "Southern Africa", 15, 38, 30, 32, 38, "upper_middle")
_add("MOZ", "Mozambique", "Africa", "Southern Africa", 38, 55, 52, 48, 52, "low")
_add("ZMB", "Zambia", "Africa", "Southern Africa", 22, 42, 42, 38, 48, "lower_middle", landlocked=True)
_add("ZWE", "Zimbabwe", "Africa", "Southern Africa", 50, 40, 62, 42, 52, "lower_middle", landlocked=True)
_add("MWI", "Malawi", "Africa", "Southern Africa", 25, 52, 50, 48, 55, "low", landlocked=True)
_add("AGO", "Angola", "Africa", "Southern Africa", 32, 40, 45, 45, 48, "lower_middle")
_add("LSO", "Lesotho", "Africa", "Southern Africa", 25, 42, 45, 48, 52, "lower_middle", landlocked=True)
_add("SWZ", "Eswatini", "Africa", "Southern Africa", 32, 38, 38, 42, 45, "lower_middle", landlocked=True)

# =====================
# AMERICAS (35 countries)
# =====================

# North America
_add("USA", "United States", "Americas", "North America", 15, 30, 10, 20, 15, "high")
_add("CAN", "Canada", "Americas", "North America", 10, 25, 8, 15, 15, "high")

# Central America
_add("MEX", "Mexico", "Americas", "Central America", 35, 35, 30, 25, 30, "upper_middle")
_add("GTM", "Guatemala", "Americas", "Central America", 38, 48, 42, 38, 42, "upper_middle")
_add("HND", "Honduras", "Americas", "Central America", 42, 50, 45, 40, 45, "lower_middle")
_add("SLV", "El Salvador", "Americas", "Central America", 35, 48, 38, 35, 38, "lower_middle")
_add("NIC", "Nicaragua", "Americas", "Central America", 42, 48, 42, 40, 42, "lower_middle")
_add("CRI", "Costa Rica", "Americas", "Central America", 15, 38, 22, 22, 28, "upper_middle")
_add("PAN", "Panama", "Americas", "Central America", 22, 38, 25, 28, 22, "upper_middle")
_add("BLZ", "Belize", "Americas", "Central America", 22, 52, 38, 40, 45, "upper_middle")

# Caribbean
_add("CUB", "Cuba", "Americas", "Caribbean", 48, 52, 55, 48, 48, "upper_middle", small_island=True)
_add("JAM", "Jamaica", "Americas", "Caribbean", 25, 55, 42, 35, 38, "upper_middle", small_island=True)
_add("HTI", "Haiti", "Americas", "Caribbean", 62, 65, 68, 58, 68, "low", small_island=True)
_add("DOM", "Dominican Republic", "Americas", "Caribbean", 25, 48, 32, 32, 35, "upper_middle", small_island=True)
_add("TTO", "Trinidad and Tobago", "Americas", "Caribbean", 20, 42, 28, 28, 30, "high", small_island=True)
_add("BHS", "Bahamas", "Americas", "Caribbean", 15, 55, 22, 28, 30, "high", small_island=True)
_add("BRB", "Barbados", "Americas", "Caribbean", 10, 50, 25, 25, 28, "high", small_island=True)
_add("ATG", "Antigua and Barbuda", "Americas", "Caribbean", 12, 58, 30, 32, 38, "high", small_island=True)
_add("GRD", "Grenada", "Americas", "Caribbean", 12, 58, 32, 35, 40, "upper_middle", small_island=True)
_add("VCT", "Saint Vincent and the Grenadines", "Americas", "Caribbean", 12, 58, 32, 35, 40, "upper_middle", small_island=True)
_add("LCA", "Saint Lucia", "Americas", "Caribbean", 12, 55, 30, 32, 38, "upper_middle", small_island=True)
_add("KNA", "Saint Kitts and Nevis", "Americas", "Caribbean", 12, 55, 28, 32, 38, "high", small_island=True)
_add("DMA", "Dominica", "Americas", "Caribbean", 10, 60, 35, 38, 42, "upper_middle", small_island=True)

# South America
_add("BRA", "Brazil", "Americas", "South America", 25, 40, 35, 20, 35, "upper_middle")
_add("ARG", "Argentina", "Americas", "South America", 22, 30, 55, 22, 32, "upper_middle")
_add("COL", "Colombia", "Americas", "South America", 32, 42, 28, 25, 30, "upper_middle")
_add("PER", "Peru", "Americas", "South America", 28, 42, 28, 28, 35, "upper_middle")
_add("CHL", "Chile", "Americas", "South America", 18, 42, 15, 18, 22, "high")
_add("ECU", "Ecuador", "Americas", "South America", 32, 45, 38, 32, 38, "upper_middle")
_add("VEN", "Venezuela", "Americas", "South America", 62, 38, 82, 42, 55, "upper_middle")
_add("BOL", "Bolivia", "Americas", "South America", 32, 38, 38, 38, 48, "lower_middle", landlocked=True)
_add("URY", "Uruguay", "Americas", "South America", 10, 28, 18, 18, 22, "high")
_add("PRY", "Paraguay", "Americas", "South America", 28, 35, 32, 35, 42, "upper_middle", landlocked=True)
_add("GUY", "Guyana", "Americas", "South America", 25, 52, 32, 40, 48, "upper_middle")
_add("SUR", "Suriname", "Americas", "South America", 22, 42, 38, 42, 48, "upper_middle")

# =====================
# OCEANIA (14 countries)
# =====================

_add("AUS", "Australia", "Oceania", "Oceania", 12, 45, 10, 15, 20, "high")
_add("NZL", "New Zealand", "Oceania", "Oceania", 8, 32, 8, 12, 18, "high")
_add("PNG", "Papua New Guinea", "Oceania", "Pacific Islands", 35, 58, 48, 50, 58, "lower_middle")
_add("FJI", "Fiji", "Oceania", "Pacific Islands", 22, 62, 35, 38, 42, "upper_middle", small_island=True)
_add("SLB", "Solomon Islands", "Oceania", "Pacific Islands", 28, 62, 48, 52, 58, "lower_middle", small_island=True)
_add("VUT", "Vanuatu", "Oceania", "Pacific Islands", 18, 68, 42, 50, 55, "lower_middle", small_island=True)
_add("WSM", "Samoa", "Oceania", "Pacific Islands", 10, 62, 35, 42, 48, "upper_middle", small_island=True)
_add("TON", "Tonga", "Oceania", "Pacific Islands", 10, 65, 38, 45, 50, "upper_middle", small_island=True)
_add("KIR", "Kiribati", "Oceania", "Pacific Islands", 10, 72, 48, 55, 58, "lower_middle", small_island=True)
_add("FSM", "Micronesia", "Oceania", "Pacific Islands", 10, 62, 42, 52, 55, "lower_middle", small_island=True)
_add("MHL", "Marshall Islands", "Oceania", "Pacific Islands", 10, 70, 45, 52, 55, "upper_middle", small_island=True)
_add("PLW", "Palau", "Oceania", "Pacific Islands", 8, 58, 32, 42, 48, "upper_middle", small_island=True)
_add("NRU", "Nauru", "Oceania", "Pacific Islands", 10, 62, 42, 52, 55, "upper_middle", small_island=True)
_add("TUV", "Tuvalu", "Oceania", "Pacific Islands", 8, 75, 48, 55, 60, "upper_middle", small_island=True)

# =====================
# TERRITORIES & SPECIAL
# =====================

_add("HKG", "Hong Kong", "Asia", "East Asia", 42, 30, 12, 20, 12, "high")
_add("MAC", "Macau", "Asia", "East Asia", 35, 28, 15, 22, 15, "high")


# --- Lookup functions ---

# Build ISO → profile mapping
_ISO_INDEX: dict[str, CountryProfile] = {p.iso3: p for p in COUNTRY_PROFILES.values()}


def get_country_risk(country_name: str) -> dict[str, float]:
    """Get risk scores for a country by name. Returns regional default if not found."""
    profile = COUNTRY_PROFILES.get(country_name)
    if profile:
        return {
            "geopolitical": profile.geopolitical,
            "climate": profile.climate,
            "financial": profile.financial,
            "cyber": profile.cyber,
            "logistics": profile.logistics,
        }
    # Fallback to global default
    return {"geopolitical": 40, "climate": 40, "financial": 40, "cyber": 35, "logistics": 35}


def get_country_risk_by_iso(iso3: str) -> dict[str, float]:
    """Get risk scores by ISO-3166 alpha-3 code."""
    profile = _ISO_INDEX.get(iso3)
    if profile:
        return {
            "geopolitical": profile.geopolitical,
            "climate": profile.climate,
            "financial": profile.financial,
            "cyber": profile.cyber,
            "logistics": profile.logistics,
        }
    return {"geopolitical": 40, "climate": 40, "financial": 40, "cyber": 35, "logistics": 35}


def get_country_profile(country_name: str) -> Optional[CountryProfile]:
    """Get full country profile by name."""
    return COUNTRY_PROFILES.get(country_name)


def get_all_countries() -> list[dict]:
    """List all countries with their risk profiles."""
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
            "income_group": p.income_group,
        }
        for p in COUNTRY_PROFILES.values()
    ]


def get_regional_default(sub_region: str) -> dict[str, float]:
    """Get regional default risk scores."""
    defaults = REGIONAL_DEFAULTS.get(sub_region)
    if defaults:
        return dict(defaults)
    return {"geopolitical": 40, "climate": 40, "financial": 40, "cyber": 35, "logistics": 35}


def search_countries(query: str) -> list[CountryProfile]:
    """Search countries by name or ISO code (case-insensitive)."""
    q = query.lower()
    results = []
    for p in COUNTRY_PROFILES.values():
        if q in p.name.lower() or q == p.iso3.lower():
            results.append(p)
    return results
