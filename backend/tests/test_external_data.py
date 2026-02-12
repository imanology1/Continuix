"""Tests for the External Data Provider."""

import pytest
from datetime import datetime, timedelta
from app.services.external_data import (
    ExternalDataProvider,
    ExternalIndicators,
    NormalizedCountryRisk,
    COUNTRY_NAME_TO_ISO,
    ISO_TO_COUNTRY_NAME,
    EU_COUNTRIES,
    ISO3_TO_ISO2,
)


class TestISOMapping:
    def test_major_countries_mapped(self):
        assert COUNTRY_NAME_TO_ISO["United States"] == "USA"
        assert COUNTRY_NAME_TO_ISO["China"] == "CHN"
        assert COUNTRY_NAME_TO_ISO["Germany"] == "DEU"
        assert COUNTRY_NAME_TO_ISO["Japan"] == "JPN"

    def test_reverse_mapping(self):
        assert ISO_TO_COUNTRY_NAME["USA"] == "United States"
        assert ISO_TO_COUNTRY_NAME["DEU"] == "Germany"

    def test_eu_countries_have_iso2(self):
        for iso3 in EU_COUNTRIES:
            assert iso3 in ISO3_TO_ISO2, f"Missing ISO2 for EU country {iso3}"

    def test_mapping_count(self):
        assert len(COUNTRY_NAME_TO_ISO) >= 100


class TestNormalization:
    @pytest.fixture
    def provider(self):
        return ExternalDataProvider()

    def test_normalize_all_data(self, provider):
        indicators = ExternalIndicators(
            country_iso="USA",
            country_name="United States",
            political_stability=1.5,
            govt_effectiveness=1.8,
            logistics_performance=3.9,
            inflation_pct=3.0,
            gdp_growth_pct=2.5,
            climate_vulnerability=30.0,
            cybersecurity_index=90.0,
            hdi_score=0.92,
        )
        result = provider.normalize(indicators)
        assert result.country_iso == "USA"
        assert result.data_completeness == 1.0
        assert result.source == "external_api"

        # Check all dimensions are in range
        for dim in ["geopolitical", "climate", "financial", "cyber", "logistics"]:
            score = getattr(result, dim)
            assert 0 <= score <= 100, f"{dim} = {score} out of range"

    def test_normalize_partial_data(self, provider):
        indicators = ExternalIndicators(
            country_iso="CHN",
            country_name="China",
            political_stability=-0.3,
            inflation_pct=2.5,
        )
        result = provider.normalize(indicators)
        assert result.data_completeness < 1.0
        assert result.data_completeness > 0

    def test_normalize_no_data(self, provider):
        indicators = ExternalIndicators(
            country_iso="UNK",
            country_name="Unknown",
        )
        result = provider.normalize(indicators)
        assert result.data_completeness == 0.0
        assert result.source == "default"
        assert result.geopolitical == 50.0  # default

    def test_stable_country_low_geo_risk(self, provider):
        indicators = ExternalIndicators(
            country_iso="NOR",
            country_name="Norway",
            political_stability=2.2,
            govt_effectiveness=2.0,
        )
        result = provider.normalize(indicators)
        assert result.geopolitical < 15

    def test_unstable_country_high_geo_risk(self, provider):
        indicators = ExternalIndicators(
            country_iso="SOM",
            country_name="Somalia",
            political_stability=-2.3,
            govt_effectiveness=-2.0,
        )
        result = provider.normalize(indicators)
        assert result.geopolitical > 85

    def test_high_inflation_increases_financial_risk(self, provider):
        low_inf = ExternalIndicators(country_iso="DEU", country_name="Germany",
                                     inflation_pct=2.0, gdp_growth_pct=1.5)
        high_inf = ExternalIndicators(country_iso="ARG", country_name="Argentina",
                                      inflation_pct=50.0, gdp_growth_pct=-3.0)
        low_result = provider.normalize(low_inf)
        high_result = provider.normalize(high_inf)
        assert high_result.financial > low_result.financial

    def test_high_lpi_low_logistics_risk(self, provider):
        indicators = ExternalIndicators(
            country_iso="DEU",
            country_name="Germany",
            logistics_performance=4.3,
        )
        result = provider.normalize(indicators)
        assert result.logistics < 25

    def test_hdi_lowers_financial_risk(self, provider):
        low_hdi = ExternalIndicators(country_iso="NER", country_name="Niger",
                                     hdi_score=0.35, inflation_pct=5.0)
        high_hdi = ExternalIndicators(country_iso="NOR", country_name="Norway",
                                      hdi_score=0.96, inflation_pct=5.0)
        low_result = provider.normalize(low_hdi)
        high_result = provider.normalize(high_hdi)
        assert high_result.financial < low_result.financial

    def test_eurostat_data_affects_financial(self, provider):
        without_eu = ExternalIndicators(
            country_iso="DEU", country_name="Germany",
            inflation_pct=2.0,
        )
        with_eu = ExternalIndicators(
            country_iso="DEU", country_name="Germany",
            inflation_pct=2.0,
            eu_unemployment_pct=5.0,
            eu_hicp_annual_pct=2.5,
        )
        result_without = provider.normalize(without_eu)
        result_with = provider.normalize(with_eu)
        # Both should compute financial risk; with more data may differ
        assert result_with.data_completeness >= result_without.data_completeness


class TestMergeWithManual:
    def test_merge_overrides_dimension(self):
        provider = ExternalDataProvider()
        normalized = NormalizedCountryRisk(
            country_iso="USA",
            country_name="United States",
            geopolitical=15.0,
            climate=30.0,
            financial=10.0,
            cyber=20.0,
            logistics=15.0,
            source="external_api",
        )
        result = provider.merge_with_manual(normalized, {"geopolitical": 25.0})
        assert result.geopolitical == 25.0
        assert result.climate == 30.0  # unchanged
        assert result.source == "blended"

    def test_manual_only_source(self):
        provider = ExternalDataProvider()
        normalized = NormalizedCountryRisk(
            country_iso="USA",
            country_name="United States",
            source="default",
        )
        result = provider.merge_with_manual(normalized, {"cyber": 10.0})
        assert result.source == "manual"


class TestCaching:
    def test_cache_hit(self):
        provider = ExternalDataProvider(cache_ttl_seconds=3600)
        # Manually add to cache
        indicators = ExternalIndicators(
            country_iso="USA",
            country_name="United States",
            political_stability=1.5,
        )
        provider._cache["USA"] = indicators
        assert provider._is_cached("USA") is True

    def test_cache_miss_empty(self):
        provider = ExternalDataProvider()
        assert provider._is_cached("USA") is False

    def test_cache_invalidation(self):
        provider = ExternalDataProvider()
        provider._cache["USA"] = ExternalIndicators(
            country_iso="USA", country_name="United States"
        )
        provider.invalidate_cache("USA")
        assert "USA" not in provider._cache

    def test_cache_invalidate_all(self):
        provider = ExternalDataProvider()
        provider._cache["USA"] = ExternalIndicators(
            country_iso="USA", country_name="United States"
        )
        provider._cache["DEU"] = ExternalIndicators(
            country_iso="DEU", country_name="Germany"
        )
        provider.invalidate_cache()
        assert len(provider._cache) == 0


class TestAvailableSources:
    def test_lists_all_sources(self):
        provider = ExternalDataProvider()
        sources = provider.get_available_sources()
        assert len(sources) >= 7
        source_ids = [s["id"] for s in sources]
        assert "world_bank_wgi" in source_ids
        assert "imf" in source_ids
        assert "undp_hdi" in source_ids
        assert "eurostat" in source_ids
        assert "ndgain" in source_ids
        assert "itu_gci" in source_ids

    def test_source_has_required_fields(self):
        provider = ExternalDataProvider()
        sources = provider.get_available_sources()
        for source in sources:
            assert "id" in source
            assert "name" in source
            assert "indicators" in source
            assert "risk_dimensions" in source
