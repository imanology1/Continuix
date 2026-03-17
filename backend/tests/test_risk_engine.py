"""Tests for the Risk Intelligence Engine."""

import pytest
from app.services.risk_engine import RiskEngine


@pytest.fixture
def engine():
    return RiskEngine()


class TestSupplierScoring:
    def test_high_risk_country(self, engine):
        result = engine.score_supplier(
            supplier_id="s1", name="Test Supplier",
            country="Russia", tier="tier_1",
        )
        assert result.overall > 40
        assert result.geopolitical > 50

    def test_low_risk_country(self, engine):
        result = engine.score_supplier(
            supplier_id="s2", name="Test Supplier",
            country="Singapore", tier="tier_1",
        )
        assert result.overall < 20

    def test_sole_source_penalty(self, engine):
        normal = engine.score_supplier(
            supplier_id="s1", name="Test",
            country="Germany", tier="tier_1", is_sole_source=False,
        )
        sole = engine.score_supplier(
            supplier_id="s1", name="Test",
            country="Germany", tier="tier_1", is_sole_source=True,
        )
        assert sole.overall > normal.overall
        assert "Single-source supplier" in str(sole.factors)

    def test_tier_modifier(self, engine):
        t1 = engine.score_supplier("s1", "T1", "China", "tier_1")
        t3 = engine.score_supplier("s2", "T3", "China", "tier_3")
        # Higher tier (deeper) should have slightly higher risk
        assert t3.geopolitical >= t1.geopolitical

    def test_low_reliability_penalty(self, engine):
        good = engine.score_supplier("s1", "Good", "Germany", "tier_1", reliability_score=0.95)
        bad = engine.score_supplier("s2", "Bad", "Germany", "tier_1", reliability_score=0.6)
        assert bad.logistics > good.logistics

    def test_risk_factors_populated(self, engine):
        result = engine.score_supplier(
            "s1", "Test", "Taiwan", "tier_2",
            is_sole_source=True, reliability_score=0.7,
        )
        assert len(result.factors) > 0

    def test_unknown_country_uses_default(self, engine):
        result = engine.score_supplier("s1", "Test", "Narnia", "tier_1")
        assert result.overall > 0


class TestFacilityScoring:
    def test_high_utilization_penalty(self, engine):
        low = engine.score_facility("f1", "Factory", "Germany", "factory", utilization=0.5)
        high = engine.score_facility("f2", "Factory", "Germany", "factory", utilization=0.95)
        assert high.logistics > low.logistics

    def test_port_type_modifier(self, engine):
        factory = engine.score_facility("f1", "Factory", "China", "factory")
        port = engine.score_facility("f2", "Port", "China", "port")
        assert port.logistics > factory.logistics


class TestRouteScoring:
    def test_chokepoint_penalty(self, engine):
        normal = engine.score_route("r1", "China", "United States", "ocean")
        choke = engine.score_route(
            "r2", "China", "United States", "ocean",
            passes_through_chokepoint=True, chokepoint_name="Strait of Malacca",
        )
        assert choke.overall > normal.overall

    def test_long_transit_penalty(self, engine):
        short = engine.score_route("r1", "China", "Japan", "ocean", transit_time_days=3)
        long = engine.score_route("r2", "China", "Netherlands", "ocean", transit_time_days=30)
        assert long.logistics > short.logistics


class TestClassification:
    def test_high_risk(self, engine):
        assert engine.classify_risk(75) == "high"

    def test_medium_risk(self, engine):
        assert engine.classify_risk(45) == "medium"

    def test_low_risk(self, engine):
        assert engine.classify_risk(15) == "low"


class TestNetworkSummary:
    def test_summary(self, engine):
        assessments = [
            engine.score_supplier("s1", "A", "Russia", "tier_1"),
            engine.score_supplier("s2", "B", "Singapore", "tier_1"),
            engine.score_supplier("s3", "C", "China", "tier_2"),
        ]
        summary = engine.compute_network_risk_summary(assessments)
        assert summary["total_entities"] == 3
        assert summary["avg_score"] > 0
        assert "Russia" in summary["by_country"]

    def test_empty_summary(self, engine):
        summary = engine.compute_network_risk_summary([])
        assert summary["total_entities"] == 0
