"""Tests for the Flexible Risk Calculator."""

import pytest
from app.services.risk_calculator import RiskCalculator, RiskInput, CalculatedRisk


@pytest.fixture
def calculator():
    return RiskCalculator()


class TestBasicCalculation:
    def test_empty_input_returns_defaults(self, calculator):
        inputs = RiskInput(country_iso="USA", country_name="United States")
        result = calculator.calculate(inputs)
        assert result.geopolitical == 50.0  # default when no data
        assert result.data_completeness == 0.0

    def test_full_input_high_completeness(self, calculator):
        inputs = RiskInput(
            country_iso="DEU", country_name="Germany",
            political_stability=1.5,
            govt_effectiveness=1.8,
            climate_vulnerability=20.0,
            climate_readiness=75.0,
            inflation_pct=2.5,
            gdp_growth_pct=1.2,
            hdi_score=0.95,
            cybersecurity_index=90.0,
            logistics_performance=4.2,
            infrastructure_quality=5.5,
        )
        result = calculator.calculate(inputs)
        assert result.data_completeness >= 0.4
        assert result.source == "manual"

    def test_all_scores_in_range(self, calculator):
        inputs = RiskInput(
            country_iso="CHN", country_name="China",
            political_stability=-0.5,
            inflation_pct=3.0,
            gdp_growth_pct=5.0,
            cybersecurity_index=60.0,
            logistics_performance=3.5,
        )
        result = calculator.calculate(inputs)
        for dim in ["geopolitical", "climate", "financial", "cyber", "logistics", "overall"]:
            score = getattr(result, dim)
            assert 0 <= score <= 100, f"{dim} = {score} out of range"


class TestGeopoliticalCalculation:
    def test_high_stability_low_risk(self, calculator):
        inputs = RiskInput(
            country_iso="NOR", country_name="Norway",
            political_stability=2.0,
            govt_effectiveness=2.0,
        )
        result = calculator.calculate(inputs)
        assert result.geopolitical < 20

    def test_low_stability_high_risk(self, calculator):
        inputs = RiskInput(
            country_iso="SYR", country_name="Syria",
            political_stability=-2.0,
            govt_effectiveness=-1.5,
        )
        result = calculator.calculate(inputs)
        assert result.geopolitical > 70

    def test_sanctions_increase_risk(self, calculator):
        base = RiskInput(country_iso="RUS", country_name="Russia",
                         political_stability=-0.5)
        with_sanctions = RiskInput(country_iso="RUS", country_name="Russia",
                                   political_stability=-0.5, sanctions_active=True)
        base_result = calculator.calculate(base)
        sanctions_result = calculator.calculate(with_sanctions)
        assert sanctions_result.geopolitical > base_result.geopolitical


class TestFinancialCalculation:
    def test_high_inflation_high_risk(self, calculator):
        inputs = RiskInput(
            country_iso="ARG", country_name="Argentina",
            inflation_pct=25.0,
        )
        result = calculator.calculate(inputs)
        assert result.financial > 60

    def test_negative_growth_high_risk(self, calculator):
        inputs = RiskInput(
            country_iso="VEN", country_name="Venezuela",
            gdp_growth_pct=-5.0,
        )
        result = calculator.calculate(inputs)
        assert result.financial > 60

    def test_high_hdi_low_risk(self, calculator):
        inputs = RiskInput(
            country_iso="NOR", country_name="Norway",
            hdi_score=0.96,
        )
        result = calculator.calculate(inputs)
        assert result.financial < 15

    def test_credit_rating_affects_risk(self, calculator):
        aaa = RiskInput(country_iso="DEU", country_name="Germany",
                        sovereign_credit_rating="AAA")
        ccc = RiskInput(country_iso="ARG", country_name="Argentina",
                        sovereign_credit_rating="CCC")
        assert calculator.calculate(aaa).financial < calculator.calculate(ccc).financial


class TestClimateCalculation:
    def test_high_vulnerability(self, calculator):
        inputs = RiskInput(
            country_iso="BGD", country_name="Bangladesh",
            climate_vulnerability=75.0,
        )
        result = calculator.calculate(inputs)
        assert result.climate > 60

    def test_readiness_reduces_risk(self, calculator):
        vulnerable = RiskInput(country_iso="BGD", country_name="Bangladesh",
                               climate_vulnerability=75.0)
        with_readiness = RiskInput(country_iso="BGD", country_name="Bangladesh",
                                   climate_vulnerability=75.0, climate_readiness=80.0)
        result_v = calculator.calculate(vulnerable)
        result_r = calculator.calculate(with_readiness)
        assert result_r.climate < result_v.climate


class TestCyberCalculation:
    def test_high_gci_low_risk(self, calculator):
        inputs = RiskInput(
            country_iso="USA", country_name="United States",
            cybersecurity_index=95.0,
        )
        result = calculator.calculate(inputs)
        assert result.cyber < 15

    def test_low_gci_high_risk(self, calculator):
        inputs = RiskInput(
            country_iso="SOM", country_name="Somalia",
            cybersecurity_index=10.0,
        )
        result = calculator.calculate(inputs)
        assert result.cyber > 70


class TestLogisticsCalculation:
    def test_high_lpi_low_risk(self, calculator):
        inputs = RiskInput(
            country_iso="DEU", country_name="Germany",
            logistics_performance=4.2,
        )
        result = calculator.calculate(inputs)
        assert result.logistics < 30

    def test_low_lpi_high_risk(self, calculator):
        inputs = RiskInput(
            country_iso="AFG", country_name="Afghanistan",
            logistics_performance=1.5,
        )
        result = calculator.calculate(inputs)
        assert result.logistics > 60


class TestCalculationDetails:
    def test_details_included(self, calculator):
        inputs = RiskInput(
            country_iso="USA", country_name="United States",
            political_stability=1.0,
            inflation_pct=3.5,
        )
        result = calculator.calculate(inputs)
        assert "geopolitical" in result.calculation_details
        assert "financial" in result.calculation_details
        assert len(result.calculation_details["geopolitical"]) > 0
        assert result.calculation_details["geopolitical"][0]["indicator"] == "political_stability"


class TestDefaultsFallback:
    def test_uses_defaults_when_provided(self, calculator):
        inputs = RiskInput(country_iso="USA", country_name="United States")
        defaults = {"geopolitical": 15.0, "climate": 30.0}
        result = calculator.calculate(inputs, defaults=defaults)
        assert result.geopolitical == 15.0
        assert result.climate == 30.0

    def test_data_overrides_defaults(self, calculator):
        inputs = RiskInput(
            country_iso="USA", country_name="United States",
            political_stability=2.0,
        )
        defaults = {"geopolitical": 50.0}
        result = calculator.calculate(inputs, defaults=defaults)
        assert result.geopolitical < 50.0  # real data overrides default


class TestOverallScore:
    def test_overall_is_weighted(self, calculator):
        inputs = RiskInput(
            country_iso="CHN", country_name="China",
            political_stability=-0.5,
            climate_vulnerability=50.0,
            inflation_pct=3.0,
            cybersecurity_index=60.0,
            logistics_performance=3.8,
        )
        result = calculator.calculate(inputs)
        expected = (
            result.geopolitical * 0.25
            + result.climate * 0.20
            + result.financial * 0.20
            + result.cyber * 0.15
            + result.logistics * 0.20
        )
        assert abs(result.overall - expected) < 1.0
