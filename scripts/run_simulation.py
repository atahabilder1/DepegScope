#!/usr/bin/env python3
"""Run contagion simulation scenarios."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.simulation.environment import DeFiEnvironment
from src.simulation.scenarios import (
    ScenarioRunner, DepegScenario,
    PREDEFINED_SCENARIOS, get_scenario, list_scenarios
)
from config.settings import PROCESSED_DATA_DIR


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level
    )


def load_simulation_data(data_dir: Path):
    """Load processed data for simulation."""
    stablecoins_file = data_dir / "stablecoins_processed.json"
    protocols_file = data_dir / "protocols_processed.json"

    if not stablecoins_file.exists():
        raise FileNotFoundError(f"Stablecoins file not found: {stablecoins_file}")

    with open(stablecoins_file) as f:
        stablecoins_data = json.load(f)

    # Convert to simulation format
    stablecoins = []
    for s in stablecoins_data:
        stablecoins.append({
            "symbol": s.get("symbol", ""),
            "market_cap": s.get("market_cap", 1e9),
            "collateral": s.get("collateral", []),
            "is_algorithmic": s.get("type") == "algorithmic",
            "stablecoin_type": s.get("type", "unknown")
        })

    protocols = []
    if protocols_file.exists():
        with open(protocols_file) as f:
            protocols_data = json.load(f)

        for p in protocols_data:
            protocols.append({
                "name": p.get("slug", p.get("name", "")),
                "tvl": p.get("tvl", 1e8),
                "exposures": p.get("stablecoin_holdings", {}),
                "category": p.get("category", "other")
            })

    return stablecoins, protocols


def run_single_scenario(
    stablecoins: list,
    protocols: list,
    trigger: str,
    severity: float,
    max_steps: int,
    seed: int
) -> dict:
    """Run a single depeg scenario."""
    config = {
        "depeg_threshold": 0.02,
        "max_steps": max_steps,
        "confidence_decay_rate": 0.1,
        "noise_std": 0.01,
        "algorithmic_death_spiral_factor": 0.9,
    }

    env = DeFiEnvironment(
        stablecoins=stablecoins,
        protocols=protocols,
        config=config,
        seed=seed
    )

    env.trigger_depeg(trigger, severity)
    results = env.run_simulation()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run DepegScope contagion simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Predefined scenarios:
{chr(10).join(f'  - {name}' for name in list_scenarios())}

Examples:
  %(prog)s --trigger USDC --severity 0.1
  %(prog)s --scenario usdc_svb
  %(prog)s --trigger USDT --monte-carlo 100
        """
    )

    parser.add_argument(
        "--trigger", "-t",
        type=str,
        help="Stablecoin to trigger depeg"
    )
    parser.add_argument(
        "--severity", "-s",
        type=float,
        default=0.1,
        help="Initial depeg severity (0-1, default: 0.1)"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=list_scenarios(),
        help="Use a predefined scenario"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum simulation steps (default: 100)"
    )
    parser.add_argument(
        "--monte-carlo", "-m",
        type=int,
        help="Run Monte Carlo simulation with N runs"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Directory with processed data"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file for results (JSON)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Validate arguments
    if not args.trigger and not args.scenario:
        parser.error("Either --trigger or --scenario must be specified")

    logger.info("=" * 60)
    logger.info("DepegScope Contagion Simulation")
    logger.info("=" * 60)

    # Load data
    logger.info(f"Loading data from {args.data_dir}")
    try:
        stablecoins, protocols = load_simulation_data(args.data_dir)
        logger.info(f"Loaded {len(stablecoins)} stablecoins, {len(protocols)} protocols")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Run 'python scripts/build_graph.py' first to create processed data")
        sys.exit(1)

    # Determine scenario
    if args.scenario:
        scenario = get_scenario(args.scenario)
        trigger = scenario.trigger_stablecoin
        severity = scenario.initial_severity
        logger.info(f"Using predefined scenario: {args.scenario}")
    else:
        trigger = args.trigger
        severity = args.severity
        scenario = None

    logger.info(f"Trigger: {trigger}")
    logger.info(f"Severity: {severity * 100:.1f}%")

    # Run simulation
    if args.monte_carlo:
        logger.info(f"Running Monte Carlo simulation ({args.monte_carlo} runs)...")

        runner = ScenarioRunner(stablecoins, protocols)

        if scenario:
            mc_results = runner.run_monte_carlo(
                scenario,
                n_runs=args.monte_carlo,
                seed_start=args.seed
            )
        else:
            custom_scenario = DepegScenario(
                name="custom",
                description="Custom scenario",
                trigger_stablecoin=trigger,
                initial_severity=severity
            )
            mc_results = runner.run_monte_carlo(
                custom_scenario,
                n_runs=args.monte_carlo,
                seed_start=args.seed
            )

        logger.info("=" * 60)
        logger.info("Monte Carlo Results:")
        logger.info(f"  Mean TVL Lost: ${mc_results['tvl_loss']['mean']:,.0f}")
        logger.info(f"  Std Dev: ${mc_results['tvl_loss']['std']:,.0f}")
        logger.info(f"  95th Percentile: ${mc_results['tvl_loss']['percentile_95']:,.0f}")
        logger.info(f"  99th Percentile: ${mc_results['tvl_loss']['percentile_99']:,.0f}")
        logger.info(f"  Avg Depegged: {mc_results['depegged_stablecoins']['mean']:.1f}")
        logger.info(f"  Avg Distressed: {mc_results['distressed_protocols']['mean']:.1f}")

        results = mc_results

    else:
        logger.info("Running single simulation...")
        results = run_single_scenario(
            stablecoins, protocols,
            trigger, severity,
            args.max_steps, args.seed
        )

        logger.info("=" * 60)
        logger.info("Simulation Results:")
        logger.info(f"  Steps: {results['steps']}")
        logger.info(f"  Total TVL Lost: ${results['total_tvl_lost']:,.0f}")
        logger.info(f"  Depegged Stablecoins: {results['depegged_stablecoins']}")
        logger.info(f"  Distressed Protocols: {results['distressed_protocols']}")
        logger.info(f"  Contagion Index: {results['contagion_index']:.3f}")

    logger.info("=" * 60)

    # Save results
    if args.output:
        # Convert DataFrames to dicts
        output_data = {}
        for key, value in results.items():
            if hasattr(value, 'to_dict'):
                output_data[key] = value.to_dict()
            else:
                output_data[key] = value

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
