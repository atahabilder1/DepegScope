"""Tests for analysis modules."""

import pytest
import pandas as pd

from src.analysis.dependency_graph import DependencyGraph
from src.analysis.risk_metrics import RiskCalculator, RiskScore
from src.analysis.contagion_model import ContagionAnalyzer


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_graph_creation(self):
        """Test empty graph creation."""
        graph = DependencyGraph()
        assert graph.graph is not None
        summary = graph.summary()
        assert summary["nodes"] == 0
        assert summary["edges"] == 0

    def test_build_from_data(self, sample_stablecoins, sample_protocols, sample_exposures):
        """Test building graph from data."""
        graph = DependencyGraph()
        graph.build_from_data(sample_stablecoins, sample_protocols, sample_exposures)

        summary = graph.summary()
        assert summary["nodes"] > 0
        assert summary["edges"] > 0
        assert summary["stablecoins"] == len(sample_stablecoins)
        assert summary["protocols"] == len(sample_protocols)

    def test_add_stablecoin(self):
        """Test adding a stablecoin node."""
        graph = DependencyGraph()
        graph.add_stablecoin(
            symbol="USDC",
            market_cap=25_000_000_000,
            stablecoin_type="fiat_backed"
        )

        assert "USDC" in graph.get_stablecoins()
        node_data = graph.graph.nodes["USDC"]
        assert node_data["type"] == "stablecoin"
        assert node_data["market_cap"] == 25_000_000_000

    def test_add_protocol(self):
        """Test adding a protocol node."""
        graph = DependencyGraph()
        graph.add_protocol(
            name="aave",
            tvl=10_000_000_000,
            category="lending"
        )

        assert "aave" in graph.get_protocols()
        node_data = graph.graph.nodes["aave"]
        assert node_data["type"] == "protocol"
        assert node_data["tvl"] == 10_000_000_000

    def test_add_exposure(self):
        """Test adding an exposure edge."""
        graph = DependencyGraph()
        graph.add_stablecoin(symbol="USDC", market_cap=25e9)
        graph.add_protocol(name="aave", tvl=10e9)
        graph.add_exposure("aave", "USDC", 3_000_000_000)

        assert graph.graph.has_edge("aave", "USDC")
        edge_data = graph.graph.edges["aave", "USDC"]
        assert edge_data["amount_usd"] == 3_000_000_000

    def test_get_stablecoin_exposure(self, sample_graph):
        """Test calculating total exposure to a stablecoin."""
        exposure = sample_graph.get_stablecoin_exposure("USDC")
        assert exposure > 0

    def test_get_protocols_exposed_to(self, sample_graph):
        """Test getting protocols exposed to a stablecoin."""
        protocols = sample_graph.get_protocols_exposed_to("USDC")
        assert len(protocols) > 0
        assert all(isinstance(p, str) for p in protocols)

    def test_calculate_centrality_metrics(self, sample_graph):
        """Test centrality metric calculation."""
        centrality = sample_graph.calculate_centrality_metrics()

        assert isinstance(centrality, pd.DataFrame)
        assert "entity" in centrality.columns
        assert "type" in centrality.columns
        assert "degree_centrality" in centrality.columns
        assert len(centrality) > 0

    def test_calculate_blast_radius(self, sample_graph):
        """Test blast radius calculation."""
        blast_radius = sample_graph.calculate_blast_radius("USDC", severity=0.10)

        assert isinstance(blast_radius, (int, float))
        assert blast_radius >= 0

    def test_blast_radius_scales_with_severity(self, sample_graph):
        """Test that blast radius increases with severity."""
        low = sample_graph.calculate_blast_radius("USDC", severity=0.05)
        high = sample_graph.calculate_blast_radius("USDC", severity=0.20)

        assert high >= low

    def test_find_systemic_chokepoints(self, sample_graph):
        """Test systemic chokepoint identification."""
        chokepoints = sample_graph.find_systemic_chokepoints()

        assert isinstance(chokepoints, list)
        assert len(chokepoints) > 0
        # Each item should be (stablecoin, risk_score)
        for item in chokepoints:
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], (int, float))

    def test_simulate_cascade(self, sample_graph):
        """Test cascade simulation."""
        cascade = sample_graph.simulate_cascade("USDC", severity=0.10)

        assert isinstance(cascade, list)
        # Should have at least one step
        assert len(cascade) >= 1

    def test_export_for_visualization(self, sample_graph):
        """Test graph export for visualization."""
        viz_data = sample_graph.export_for_visualization()

        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert len(viz_data["nodes"]) > 0


class TestRiskCalculator:
    """Tests for RiskCalculator class."""

    def test_risk_calculator_creation(self, sample_graph):
        """Test RiskCalculator creation."""
        calc = RiskCalculator(sample_graph)
        assert calc is not None

    def test_calculate_stablecoin_risk(self, sample_graph):
        """Test stablecoin risk calculation."""
        calc = RiskCalculator(sample_graph)
        risk = calc.calculate_stablecoin_risk("USDC")

        assert isinstance(risk, RiskScore)
        assert risk.entity_name == "USDC"
        assert risk.entity_type == "stablecoin"
        assert 0 <= risk.overall_score <= 1

    def test_calculate_protocol_risk(self, sample_graph):
        """Test protocol risk calculation."""
        calc = RiskCalculator(sample_graph)
        risk = calc.calculate_protocol_risk("aave")

        assert isinstance(risk, RiskScore)
        assert risk.entity_name == "aave"
        assert risk.entity_type == "protocol"

    def test_calculate_concentration_risk(self, sample_graph):
        """Test concentration risk (HHI) calculation."""
        calc = RiskCalculator(sample_graph)
        hhi = calc.calculate_concentration_risk("aave")

        assert isinstance(hhi, float)
        assert 0 <= hhi <= 1

    def test_generate_risk_report(self, sample_graph):
        """Test risk report generation."""
        calc = RiskCalculator(sample_graph)
        report = calc.generate_risk_report()

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0

    def test_generate_protocol_risk_report(self, sample_graph):
        """Test protocol risk report generation."""
        calc = RiskCalculator(sample_graph)
        report = calc.generate_protocol_risk_report()

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0

    def test_calculate_ecosystem_risk(self, sample_graph):
        """Test ecosystem-wide risk calculation."""
        calc = RiskCalculator(sample_graph)
        ecosystem = calc.calculate_ecosystem_risk()

        assert isinstance(ecosystem, dict)
        assert "overall_ecosystem_risk" in ecosystem

    def test_calculate_var(self, sample_graph):
        """Test VaR calculation."""
        calc = RiskCalculator(sample_graph)
        var_metrics = calc.calculate_var(confidence=0.95, n_simulations=100)

        assert isinstance(var_metrics, dict)
        assert "var" in var_metrics
        assert "cvar" in var_metrics


class TestContagionAnalyzer:
    """Tests for ContagionAnalyzer class."""

    def test_contagion_analyzer_creation(self, sample_graph):
        """Test ContagionAnalyzer creation."""
        analyzer = ContagionAnalyzer(sample_graph)
        assert analyzer is not None

    def test_analyze_static_contagion(self, sample_graph):
        """Test static contagion analysis."""
        analyzer = ContagionAnalyzer(sample_graph)
        result = analyzer.analyze_static_contagion("USDC", severity=0.10)

        assert isinstance(result, dict)
        assert "direct_impact" in result
        assert "total_tvl_at_risk" in result

    def test_analyze_dynamic_contagion(self, sample_graph):
        """Test dynamic contagion simulation."""
        analyzer = ContagionAnalyzer(sample_graph)
        result = analyzer.analyze_dynamic_contagion(
            trigger="USDC",
            severity=0.10,
            max_steps=50,
            seed=42
        )

        assert isinstance(result, dict)
        assert "steps" in result

    def test_get_cascade_paths(self, sample_graph):
        """Test cascade path extraction."""
        analyzer = ContagionAnalyzer(sample_graph)
        paths = analyzer.get_cascade_paths("USDC", max_depth=3)

        assert isinstance(paths, list)


class TestRiskScore:
    """Tests for RiskScore dataclass."""

    def test_risk_score_creation(self):
        """Test RiskScore creation."""
        from datetime import datetime

        risk = RiskScore(
            entity_name="USDC",
            entity_type="stablecoin",
            overall_score=0.35,
            concentration_risk=0.20,
            contagion_risk=0.40,
            market_risk=0.30,
            liquidity_risk=0.25,
            factors={"factor1": 0.5},
            timestamp=datetime.now()
        )

        assert risk.entity_name == "USDC"
        assert risk.overall_score == 0.35
        assert risk.factors == {"factor1": 0.5}
