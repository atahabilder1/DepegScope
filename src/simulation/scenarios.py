"""Predefined depeg scenarios for simulation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from loguru import logger
import json
from pathlib import Path

from .environment import DeFiEnvironment


@dataclass
class DepegScenario:
    """Definition of a depeg scenario to simulate."""

    name: str
    description: str
    trigger_stablecoin: str
    initial_severity: float = 0.1

    # Optional cascade triggers
    secondary_triggers: List[Dict] = field(default_factory=list)

    # Timing
    trigger_step: int = 0
    secondary_trigger_delays: List[int] = field(default_factory=list)

    # Environment modifications
    config_overrides: Dict[str, Any] = field(default_factory=dict)

    # Expected outcomes (for validation)
    expected_outcomes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger_stablecoin": self.trigger_stablecoin,
            "initial_severity": self.initial_severity,
            "secondary_triggers": self.secondary_triggers,
            "trigger_step": self.trigger_step,
            "config_overrides": self.config_overrides,
            "expected_outcomes": self.expected_outcomes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DepegScenario":
        """Create from dictionary."""
        return cls(**data)


class ScenarioRunner:
    """Runner for executing depeg scenarios."""

    def __init__(
        self,
        stablecoins: List[Dict],
        protocols: List[Dict],
        base_config: Optional[Dict] = None
    ):
        """
        Initialize scenario runner.

        Args:
            stablecoins: Base stablecoin configurations
            protocols: Base protocol configurations
            base_config: Base simulation configuration
        """
        self.stablecoins = stablecoins
        self.protocols = protocols
        self.base_config = base_config or {
            "depeg_threshold": 0.02,
            "max_steps": 100,
            "confidence_decay_rate": 0.1,
            "noise_std": 0.01,
            "algorithmic_death_spiral_factor": 0.9,
        }
        self.results_history: List[Dict] = []

    def run_scenario(
        self,
        scenario: DepegScenario,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a single scenario.

        Args:
            scenario: Scenario to run
            seed: Random seed for reproducibility

        Returns:
            Simulation results
        """
        logger.info(f"Running scenario: {scenario.name}")

        # Merge config
        config = {**self.base_config, **scenario.config_overrides}

        # Create environment
        env = DeFiEnvironment(
            stablecoins=self.stablecoins,
            protocols=self.protocols,
            config=config,
            seed=seed
        )

        # Apply initial trigger
        if scenario.trigger_step == 0:
            env.trigger_depeg(scenario.trigger_stablecoin, scenario.initial_severity)

        # Run simulation with potential secondary triggers
        step = 0
        while env.running and step < config.get("max_steps", 100):
            env.step()
            step += 1

            # Check for delayed initial trigger
            if step == scenario.trigger_step:
                env.trigger_depeg(scenario.trigger_stablecoin, scenario.initial_severity)

            # Check for secondary triggers
            for i, secondary in enumerate(scenario.secondary_triggers):
                delay = (
                    scenario.secondary_trigger_delays[i]
                    if i < len(scenario.secondary_trigger_delays)
                    else 10
                )
                if step == scenario.trigger_step + delay:
                    env.trigger_depeg(
                        secondary["stablecoin"],
                        secondary.get("severity", 0.05)
                    )

        # Get results
        results = env.get_results()
        results["scenario"] = scenario.to_dict()
        results["seed"] = seed

        # Store in history
        self.results_history.append(results)

        logger.info(
            f"Scenario {scenario.name} complete: "
            f"{results['depegged_stablecoins']} depegged, "
            f"{results['distressed_protocols']} distressed, "
            f"${results['total_tvl_lost']:,.0f} TVL lost"
        )

        return results

    def run_monte_carlo(
        self,
        scenario: DepegScenario,
        n_runs: int = 100,
        seed_start: int = 42
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation of a scenario.

        Args:
            scenario: Scenario to simulate
            n_runs: Number of simulation runs
            seed_start: Starting seed for reproducibility

        Returns:
            Aggregated Monte Carlo results
        """
        logger.info(f"Running Monte Carlo simulation: {n_runs} runs")

        all_results = []
        for i in range(n_runs):
            result = self.run_scenario(scenario, seed=seed_start + i)
            all_results.append({
                "run": i,
                "tvl_lost": result["total_tvl_lost"],
                "depegged": result["depegged_stablecoins"],
                "distressed": result["distressed_protocols"],
                "steps": result["steps"],
                "contagion_index": result["contagion_index"]
            })

        # Calculate statistics
        import numpy as np

        tvl_losses = [r["tvl_lost"] for r in all_results]
        depegged_counts = [r["depegged"] for r in all_results]
        distressed_counts = [r["distressed"] for r in all_results]

        return {
            "scenario": scenario.name,
            "n_runs": n_runs,
            "tvl_loss": {
                "mean": np.mean(tvl_losses),
                "std": np.std(tvl_losses),
                "min": np.min(tvl_losses),
                "max": np.max(tvl_losses),
                "median": np.median(tvl_losses),
                "percentile_95": np.percentile(tvl_losses, 95),
                "percentile_99": np.percentile(tvl_losses, 99)
            },
            "depegged_stablecoins": {
                "mean": np.mean(depegged_counts),
                "max": np.max(depegged_counts)
            },
            "distressed_protocols": {
                "mean": np.mean(distressed_counts),
                "max": np.max(distressed_counts)
            },
            "all_results": all_results
        }

    def run_sensitivity_analysis(
        self,
        scenario: DepegScenario,
        parameter: str,
        values: List[float],
        n_runs_per_value: int = 10
    ) -> Dict[str, Any]:
        """
        Run sensitivity analysis on a parameter.

        Args:
            scenario: Base scenario
            parameter: Parameter to vary (e.g., 'initial_severity')
            values: Values to test
            n_runs_per_value: Monte Carlo runs per value

        Returns:
            Sensitivity analysis results
        """
        logger.info(f"Running sensitivity analysis on {parameter}")

        results = []
        for value in values:
            # Modify scenario
            modified_scenario = DepegScenario(
                name=f"{scenario.name}_{parameter}_{value}",
                description=scenario.description,
                trigger_stablecoin=scenario.trigger_stablecoin,
                initial_severity=(
                    value if parameter == "initial_severity"
                    else scenario.initial_severity
                ),
                config_overrides={
                    **scenario.config_overrides,
                    parameter: value
                } if parameter not in ["initial_severity"] else scenario.config_overrides
            )

            # Run Monte Carlo
            mc_results = self.run_monte_carlo(
                modified_scenario,
                n_runs=n_runs_per_value
            )

            results.append({
                "parameter_value": value,
                "tvl_loss_mean": mc_results["tvl_loss"]["mean"],
                "tvl_loss_std": mc_results["tvl_loss"]["std"],
                "depegged_mean": mc_results["depegged_stablecoins"]["mean"],
                "distressed_mean": mc_results["distressed_protocols"]["mean"]
            })

        return {
            "parameter": parameter,
            "values": values,
            "results": results
        }

    def compare_scenarios(
        self,
        scenarios: List[DepegScenario],
        n_runs: int = 50
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios.

        Args:
            scenarios: List of scenarios to compare
            n_runs: Monte Carlo runs per scenario

        Returns:
            Comparison results
        """
        comparisons = []
        for scenario in scenarios:
            mc_results = self.run_monte_carlo(scenario, n_runs=n_runs)
            comparisons.append({
                "scenario": scenario.name,
                "trigger": scenario.trigger_stablecoin,
                "severity": scenario.initial_severity,
                "tvl_loss_mean": mc_results["tvl_loss"]["mean"],
                "tvl_loss_95": mc_results["tvl_loss"]["percentile_95"],
                "depegged_mean": mc_results["depegged_stablecoins"]["mean"],
                "distressed_mean": mc_results["distressed_protocols"]["mean"]
            })

        return {
            "comparisons": comparisons,
            "n_runs": n_runs
        }


# Predefined scenarios based on historical events
PREDEFINED_SCENARIOS = {
    "usdc_svb": DepegScenario(
        name="USDC SVB Crisis",
        description="Simulation of March 2023 USDC depeg due to SVB collapse",
        trigger_stablecoin="USDC",
        initial_severity=0.13,  # Dropped to $0.87
        secondary_triggers=[
            {"stablecoin": "DAI", "severity": 0.11},
            {"stablecoin": "FRAX", "severity": 0.13}
        ],
        secondary_trigger_delays=[2, 3],
        expected_outcomes={
            "recovery_steps": 72,  # 3 days in hourly steps
        }
    ),

    "ust_collapse": DepegScenario(
        name="UST Terra Collapse",
        description="Simulation of May 2022 UST algorithmic stablecoin death spiral",
        trigger_stablecoin="UST",  # Would need UST in stablecoin list
        initial_severity=0.10,
        config_overrides={
            "algorithmic_death_spiral_factor": 0.85,  # Aggressive spiral
            "confidence_decay_rate": 0.15
        },
        expected_outcomes={
            "final_price": 0.01,
            "total_loss_billions": 60
        }
    ),

    "moderate_usdt_fud": DepegScenario(
        name="Moderate USDT FUD Event",
        description="Moderate confidence crisis in USDT",
        trigger_stablecoin="USDT",
        initial_severity=0.05,
        config_overrides={
            "confidence_decay_rate": 0.05,
            "peg_support_strength": 0.02  # Strong arb support
        }
    ),

    "algorithmic_cascade": DepegScenario(
        name="Algorithmic Stablecoin Cascade",
        description="Cascade failure starting from algorithmic stablecoin",
        trigger_stablecoin="USDe",
        initial_severity=0.15,
        config_overrides={
            "algorithmic_death_spiral_factor": 0.88
        }
    ),

    "multi_stable_stress": DepegScenario(
        name="Multi-Stablecoin Stress Test",
        description="Simultaneous stress on multiple stablecoins",
        trigger_stablecoin="USDC",
        initial_severity=0.08,
        secondary_triggers=[
            {"stablecoin": "USDT", "severity": 0.05},
            {"stablecoin": "DAI", "severity": 0.06}
        ],
        secondary_trigger_delays=[0, 0]  # Simultaneous
    )
}


def get_scenario(name: str) -> Optional[DepegScenario]:
    """Get predefined scenario by name."""
    return PREDEFINED_SCENARIOS.get(name)


def list_scenarios() -> List[str]:
    """List available predefined scenarios."""
    return list(PREDEFINED_SCENARIOS.keys())
