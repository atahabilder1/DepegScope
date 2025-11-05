"""Contagion analysis model combining dependency graphs with simulation."""

from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from loguru import logger

from src.models.stablecoin import Stablecoin
from src.models.protocol import Protocol
from src.models.exposure import Exposure
from src.analysis.dependency_graph import DependencyGraph
from src.simulation.environment import DeFiEnvironment
from src.simulation.scenarios import DepegScenario, ScenarioRunner


class ContagionAnalyzer:
    """
    Comprehensive contagion analysis combining static graph analysis
    with dynamic agent-based simulation.
    """

    def __init__(
        self,
        stablecoins: List[Stablecoin],
        protocols: List[Protocol],
        exposures: List[Exposure]
    ):
        """
        Initialize contagion analyzer.

        Args:
            stablecoins: List of stablecoin objects
            protocols: List of protocol objects
            exposures: List of exposure relationships
        """
        self.stablecoins = {s.symbol: s for s in stablecoins}
        self.protocols = {p.slug: p for p in protocols}
        self.exposures = exposures

        # Build dependency graph
        self.graph = DependencyGraph()
        self.graph.build_from_data(stablecoins, protocols, exposures)

        # Prepare data for simulation
        self._stablecoin_configs = self._prepare_stablecoin_configs()
        self._protocol_configs = self._prepare_protocol_configs()

        logger.info(
            f"ContagionAnalyzer initialized with {len(stablecoins)} stablecoins, "
            f"{len(protocols)} protocols"
        )

    def _prepare_stablecoin_configs(self) -> List[Dict]:
        """Prepare stablecoin configurations for simulation."""
        configs = []
        for symbol, stablecoin in self.stablecoins.items():
            configs.append({
                "symbol": symbol,
                "market_cap": stablecoin.market_cap,
                "collateral": stablecoin.collateral,
                "collateral_ratio": stablecoin.collateral_ratio,
                "is_algorithmic": stablecoin.stablecoin_type.value == "algorithmic",
                "stablecoin_type": stablecoin.stablecoin_type.value
            })
        return configs

    def _prepare_protocol_configs(self) -> List[Dict]:
        """Prepare protocol configurations for simulation."""
        configs = []
        for slug, protocol in self.protocols.items():
            configs.append({
                "name": slug,
                "tvl": protocol.tvl,
                "exposures": protocol.stablecoin_holdings,
                "category": protocol.category.value,
                "liquidation_threshold": 0.8
            })
        return configs

    def analyze_static_contagion(
        self,
        trigger_stablecoin: str,
        depeg_severity: float = 0.1
    ) -> Dict[str, Any]:
        """
        Perform static contagion analysis using dependency graph.

        Args:
            trigger_stablecoin: Initial depegging stablecoin
            depeg_severity: Severity of depeg (0-1)

        Returns:
            Static analysis results
        """
        # Get blast radius
        blast = self.graph.calculate_blast_radius(trigger_stablecoin, depeg_severity)

        # Get cascade path
        cascade_path = self.graph.get_cascade_path(trigger_stablecoin)

        # Get dependent stablecoins
        dependent_stables = self.graph.get_downstream_stablecoins(trigger_stablecoin)

        # Calculate centrality of trigger
        centrality = self.graph.calculate_centrality_metrics()
        trigger_centrality = centrality[centrality["node"] == trigger_stablecoin]

        return {
            "trigger": trigger_stablecoin,
            "depeg_severity": depeg_severity,
            "blast_radius": blast,
            "cascade_path": cascade_path,
            "cascade_depth": len(cascade_path),
            "dependent_stablecoins": dependent_stables,
            "trigger_centrality": trigger_centrality.to_dict("records")[0] if len(trigger_centrality) > 0 else {},
            "analysis_type": "static"
        }

    def simulate_contagion(
        self,
        trigger_stablecoin: str,
        severity: float = 0.1,
        max_steps: int = 100,
        seed: Optional[int] = None,
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run dynamic contagion simulation.

        Args:
            trigger_stablecoin: Stablecoin to trigger depeg
            severity: Initial severity of depeg
            max_steps: Maximum simulation steps
            seed: Random seed for reproducibility
            config: Additional simulation configuration

        Returns:
            Simulation results
        """
        sim_config = {
            "depeg_threshold": 0.02,
            "max_steps": max_steps,
            "confidence_decay_rate": 0.1,
            "noise_std": 0.01,
            "algorithmic_death_spiral_factor": 0.9,
            **(config or {})
        }

        # Create environment
        env = DeFiEnvironment(
            stablecoins=self._stablecoin_configs,
            protocols=self._protocol_configs,
            config=sim_config,
            seed=seed
        )

        # Trigger depeg
        env.trigger_depeg(trigger_stablecoin, severity)

        # Run simulation
        results = env.run_simulation()
        results["analysis_type"] = "simulation"
        results["trigger"] = trigger_stablecoin
        results["initial_severity"] = severity

        return results

    def compare_static_vs_simulation(
        self,
        trigger_stablecoin: str,
        severity: float = 0.1,
        n_simulations: int = 10
    ) -> Dict[str, Any]:
        """
        Compare static graph analysis with simulation results.

        Args:
            trigger_stablecoin: Stablecoin to analyze
            severity: Depeg severity
            n_simulations: Number of simulation runs for averaging

        Returns:
            Comparison results
        """
        # Static analysis
        static_results = self.analyze_static_contagion(trigger_stablecoin, severity)

        # Run multiple simulations
        sim_results = []
        for i in range(n_simulations):
            result = self.simulate_contagion(
                trigger_stablecoin,
                severity,
                seed=42 + i
            )
            sim_results.append({
                "tvl_lost": result["total_tvl_lost"],
                "depegged": result["depegged_stablecoins"],
                "distressed": result["distressed_protocols"],
                "steps": result["steps"]
            })

        # Aggregate simulation results
        avg_tvl_lost = np.mean([r["tvl_lost"] for r in sim_results])
        avg_depegged = np.mean([r["depegged"] for r in sim_results])
        avg_distressed = np.mean([r["distressed"] for r in sim_results])

        return {
            "trigger": trigger_stablecoin,
            "severity": severity,
            "static_analysis": {
                "tvl_at_risk": static_results["blast_radius"]["total_tvl_at_risk"],
                "protocols_affected": static_results["blast_radius"]["protocols_affected"],
                "stablecoins_affected": static_results["blast_radius"]["stablecoins_affected"],
                "cascade_depth": static_results["cascade_depth"]
            },
            "simulation_analysis": {
                "avg_tvl_lost": avg_tvl_lost,
                "avg_depegged": avg_depegged,
                "avg_distressed": avg_distressed,
                "std_tvl_lost": np.std([r["tvl_lost"] for r in sim_results]),
                "n_runs": n_simulations
            },
            "comparison": {
                "static_to_sim_ratio": (
                    static_results["blast_radius"]["total_tvl_at_risk"] / max(avg_tvl_lost, 1)
                    if avg_tvl_lost > 0 else 0
                )
            }
        }

    def identify_systemic_risks(self) -> Dict[str, Any]:
        """
        Identify systemic risks in the ecosystem.

        Returns:
            Systemic risk analysis
        """
        # Get chokepoints from graph
        chokepoints = self.graph.find_systemic_chokepoints()

        # Identify feedback loops
        feedback_loops = self.graph.identify_feedback_loops()

        # Calculate centrality
        centrality = self.graph.calculate_centrality_metrics()

        # Find most central stablecoins
        stablecoin_centrality = centrality[centrality["type"] == "stablecoin"]
        top_stablecoins = stablecoin_centrality.nlargest(5, "pagerank")

        # Find most exposed protocols
        protocol_centrality = centrality[centrality["type"] == "protocol"]
        top_protocols = protocol_centrality.nlargest(5, "in_degree_weighted")

        # Run stress tests on top chokepoints
        stress_results = []
        for stablecoin, _ in chokepoints[:3]:  # Top 3 chokepoints
            result = self.simulate_contagion(stablecoin, severity=0.2, seed=42)
            stress_results.append({
                "stablecoin": stablecoin,
                "tvl_lost": result["total_tvl_lost"],
                "depegged_count": result["depegged_stablecoins"],
                "distressed_count": result["distressed_protocols"]
            })

        return {
            "chokepoints": [{"stablecoin": s, "risk_score": r} for s, r in chokepoints],
            "feedback_loops": feedback_loops,
            "top_central_stablecoins": top_stablecoins.to_dict("records"),
            "top_exposed_protocols": top_protocols.to_dict("records"),
            "stress_test_results": stress_results,
            "summary": {
                "total_chokepoints": len(chokepoints),
                "feedback_loop_count": len(feedback_loops),
                "highest_risk_stablecoin": chokepoints[0][0] if chokepoints else None
            }
        }

    def scenario_analysis(
        self,
        scenarios: List[DepegScenario],
        n_runs: int = 50
    ) -> Dict[str, Any]:
        """
        Run multiple scenario analyses.

        Args:
            scenarios: List of scenarios to analyze
            n_runs: Monte Carlo runs per scenario

        Returns:
            Scenario comparison results
        """
        runner = ScenarioRunner(
            stablecoins=self._stablecoin_configs,
            protocols=self._protocol_configs
        )

        return runner.compare_scenarios(scenarios, n_runs=n_runs)

    def generate_risk_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive risk report.

        Returns:
            Full risk report
        """
        logger.info("Generating comprehensive risk report...")

        # Graph summary
        graph_summary = self.graph.summary()

        # Systemic risks
        systemic_risks = self.identify_systemic_risks()

        # Individual stablecoin risks
        stablecoin_risks = []
        for symbol in self.stablecoins:
            static = self.analyze_static_contagion(symbol, 0.1)
            stablecoin_risks.append({
                "symbol": symbol,
                "tvl_at_risk": static["blast_radius"]["total_tvl_at_risk"],
                "cascade_depth": static["cascade_depth"],
                "dependent_stablecoins": len(static["dependent_stablecoins"]),
                "centrality": static["trigger_centrality"]
            })

        # Sort by risk
        stablecoin_risks = sorted(
            stablecoin_risks,
            key=lambda x: x["tvl_at_risk"],
            reverse=True
        )

        return {
            "report_type": "contagion_risk",
            "graph_summary": graph_summary,
            "systemic_risks": systemic_risks,
            "stablecoin_risks": stablecoin_risks,
            "recommendations": self._generate_recommendations(systemic_risks, stablecoin_risks)
        }

    def _generate_recommendations(
        self,
        systemic_risks: Dict,
        stablecoin_risks: List[Dict]
    ) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []

        # High concentration risks
        if systemic_risks["summary"]["total_chokepoints"] > 3:
            recommendations.append(
                "CRITICAL: Multiple systemic chokepoints identified. "
                "Consider diversifying stablecoin exposure across protocols."
            )

        # Feedback loops
        if systemic_risks["summary"]["feedback_loop_count"] > 0:
            recommendations.append(
                "WARNING: Feedback loops detected in dependency graph. "
                "These can amplify contagion effects during stress events."
            )

        # Top risk stablecoins
        if stablecoin_risks:
            top_risk = stablecoin_risks[0]
            recommendations.append(
                f"MONITOR: {top_risk['symbol']} has highest contagion risk "
                f"(${top_risk['tvl_at_risk']:,.0f} TVL at risk). "
                "Consider early warning monitoring."
            )

        return recommendations

    def export_analysis(self, filepath: str):
        """Export analysis to JSON file."""
        import json
        from pathlib import Path

        report = self.generate_risk_report()

        # Convert non-serializable objects
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict("records")
            return obj

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=convert)

        logger.info(f"Analysis exported to {filepath}")
