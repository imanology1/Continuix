"""Tests for the 190+ Country Baseline Risk Database."""

import pytest
from app.services.country_baseline import (
    COUNTRY_PROFILES,
    get_country_risk,
    get_country_risk_by_iso,
    get_country_profile,
    get_all_countries,
    get_regional_default,
    search_countries,
)


class TestCountryCoverage:
    def test_at_least_190_countries(self):
        assert len(COUNTRY_PROFILES) >= 190

    def test_all_un_regions_covered(self):
        regions = {p.region for p in COUNTRY_PROFILES.values()}
        assert "Europe" in regions
        assert "Asia" in regions
        assert "Africa" in regions
        assert "Americas" in regions
        assert "Oceania" in regions

    def test_major_economies_present(self):
        major = [
            "United States", "China", "Japan", "Germany", "India",
            "United Kingdom", "France", "Brazil", "Canada", "Australia",
        ]
        for country in major:
            assert country in COUNTRY_PROFILES, f"Missing: {country}"

    def test_supply_chain_hubs_present(self):
        hubs = [
            "Taiwan", "South Korea", "Vietnam", "Mexico", "Thailand",
            "Malaysia", "Indonesia", "Singapore", "Turkey", "Poland",
        ]
        for country in hubs:
            assert country in COUNTRY_PROFILES, f"Missing: {country}"


class TestRiskScoreRanges:
    def test_all_scores_in_range(self):
        for name, profile in COUNTRY_PROFILES.items():
            for dim in ["geopolitical", "climate", "financial", "cyber", "logistics"]:
                score = getattr(profile, dim)
                assert 0 <= score <= 100, f"{name}.{dim} = {score} out of range"

    def test_conflict_countries_high_geo_risk(self):
        conflict = ["Syria", "Yemen", "Afghanistan", "Somalia"]
        for country in conflict:
            profile = COUNTRY_PROFILES[country]
            assert profile.geopolitical >= 70, f"{country} geo should be >= 70"

    def test_stable_countries_low_geo_risk(self):
        stable = ["Norway", "Switzerland", "Singapore", "Iceland"]
        for country in stable:
            profile = COUNTRY_PROFILES[country]
            assert profile.geopolitical <= 15, f"{country} geo should be <= 15"

    def test_high_climate_risk_countries(self):
        exposed = ["Bangladesh", "Philippines", "Kiribati"]
        for country in exposed:
            profile = COUNTRY_PROFILES[country]
            assert profile.climate >= 50, f"{country} climate should be >= 50"


class TestLookupFunctions:
    def test_get_by_name(self):
        risk = get_country_risk("Germany")
        assert risk["geopolitical"] == 10
        assert risk["logistics"] == 10

    def test_get_by_iso(self):
        risk = get_country_risk_by_iso("DEU")
        assert risk["geopolitical"] == 10

    def test_unknown_country_returns_default(self):
        risk = get_country_risk("Atlantis")
        assert risk["geopolitical"] == 40  # global default

    def test_unknown_iso_returns_default(self):
        risk = get_country_risk_by_iso("ZZZ")
        assert risk["geopolitical"] == 40

    def test_get_profile(self):
        profile = get_country_profile("Japan")
        assert profile is not None
        assert profile.iso3 == "JPN"
        assert profile.region == "Asia"

    def test_get_all_countries(self):
        all_c = get_all_countries()
        assert len(all_c) >= 190
        assert all("iso3" in c for c in all_c)

    def test_regional_default(self):
        default = get_regional_default("Northern Europe")
        assert default["geopolitical"] == 8

    def test_search_by_name(self):
        results = search_countries("germ")
        assert len(results) >= 1
        assert any(p.name == "Germany" for p in results)

    def test_search_by_iso(self):
        results = search_countries("JPN")
        assert len(results) >= 1
        assert results[0].name == "Japan"

    def test_search_case_insensitive(self):
        results = search_countries("BRAZIL")
        assert len(results) >= 1


class TestCountryAttributes:
    def test_landlocked_countries(self):
        landlocked = [p for p in COUNTRY_PROFILES.values() if p.is_landlocked]
        assert len(landlocked) >= 20
        names = {p.name for p in landlocked}
        assert "Switzerland" in names
        assert "Mongolia" in names

    def test_small_island_states(self):
        islands = [p for p in COUNTRY_PROFILES.values() if p.is_small_island]
        assert len(islands) >= 10
        names = {p.name for p in islands}
        assert "Fiji" in names
        assert "Maldives" in names

    def test_income_groups_assigned(self):
        groups = {p.income_group for p in COUNTRY_PROFILES.values()}
        assert "high" in groups
        assert "upper_middle" in groups
        assert "lower_middle" in groups
        assert "low" in groups
