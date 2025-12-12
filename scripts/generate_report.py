#!/usr/bin/env python3
"""Generate comprehensive risk report."""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.models.stablecoin import Stablecoin, StablecoinType
from src.models.protocol import Protocol
from src.models.exposure import Exposure, ExposureType
from src.analysis.dependency_graph import DependencyGraph
from src.analysis.risk_metrics import RiskCalculator
from src.analysis.contagion_model import ContagionAnalyzer
from src.visualization.risk_dashboard import RiskDashboard
from src.visualization.network_plots import NetworkVisualizer
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


def load_data(data_dir: Path):
    """Load processed data."""
    stablecoins = []
    protocols = []
    exposures = []

    # Load stablecoins
    stables_file = data_dir / "stablecoins_processed.json"
    if stables_file.exists():
        with open(stables_file) as f:
            data = json.load(f)
        stablecoins = [Stablecoin.from_dict(s) for s in data]

    # Load protocols
    protocols_file = data_dir / "protocols_processed.json"
    if protocols_file.exists():
        with open(protocols_file) as f:
            data = json.load(f)
        protocols = [Protocol.from_dict(p) for p in data]

    # Load exposures
    exposures_file = data_dir / "exposures_processed.json"
    if exposures_file.exists():
        with open(exposures_file) as f:
            data = json.load(f)
        exposures = [Exposure.from_dict(e) for e in data]

    return stablecoins, protocols, exposures


def main():
    parser = argparse.ArgumentParser(
        description="Generate DepegScope risk report"
    )

    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Directory with processed data"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("reports"),
        help="Output directory for reports"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "html", "all"],
        default="all",
        help="Report format (default: all)"
    )
    parser.add_argument(
        "--generate-plots",
        action="store_true",
        help="Generate visualization plots"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger.info("=" * 60)
    logger.info("Generating Risk Report")
    logger.info("=" * 60)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Load data
    logger.info("Loading data...")
    stablecoins, protocols, exposures = load_data(args.data_dir)

    if not stablecoins:
        logger.error("No stablecoin data found. Run build_graph.py first.")
        sys.exit(1)

    logger.info(f"Loaded {len(stablecoins)} stablecoins, {len(protocols)} protocols")

    # Build graph and calculate risks
    logger.info("Building dependency graph...")
    graph = DependencyGraph()
    graph.build_from_data(stablecoins, protocols, exposures)

    logger.info("Calculating risk metrics...")
    risk_calc = RiskCalculator(graph)

    # Generate reports
    stablecoin_risks = risk_calc.generate_risk_report()
    protocol_risks = risk_calc.generate_protocol_risk_report()
    ecosystem_risk = risk_calc.calculate_ecosystem_risk()

    # Calculate VaR
    logger.info("Calculating Value at Risk...")
    var_metrics = risk_calc.calculate_var()

    # Identify systemic risks
    logger.info("Identifying systemic risks...")
    chokepoints = graph.find_systemic_chokepoints()
    centrality = graph.calculate_centrality_metrics()

    # Compile full report
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_stablecoins": len(stablecoins),
            "total_protocols": len(protocols),
            "total_exposures": len(exposures),
            "ecosystem_risk_score": ecosystem_risk.get("overall_ecosystem_risk", 0),
            "var_95": var_metrics.get("var", 0),
            "cvar_95": var_metrics.get("cvar", 0)
        },
        "stablecoin_risks": stablecoin_risks.to_dict("records"),
        "protocol_risks": protocol_risks.to_dict("records"),
        "ecosystem_risk": ecosystem_risk,
        "var_metrics": var_metrics,
        "systemic_chokepoints": [
            {"stablecoin": s, "risk_score": r}
            for s, r in chokepoints[:10]
        ],
        "high_risk_entities": {
            "stablecoins": ecosystem_risk.get("high_risk_stablecoins", []),
            "protocols": ecosystem_risk.get("high_risk_protocols", [])
        }
    }

    # Save JSON report
    if args.format in ["json", "all"]:
        json_file = args.output_dir / f"risk_report_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"JSON report saved to {json_file}")

    # Generate plots
    if args.generate_plots:
        plots_dir = args.output_dir / "plots"
        plots_dir.mkdir(exist_ok=True)

        logger.info("Generating visualizations...")

        # Risk dashboard
        try:
            dashboard = RiskDashboard()
            fig = dashboard.create_risk_summary_dashboard(
                stablecoin_risks,
                protocol_risks,
                ecosystem_risk,
                save_path=plots_dir / f"risk_dashboard_{timestamp}.png"
            )
            logger.info("Risk dashboard generated")
        except Exception as e:
            logger.warning(f"Dashboard generation failed: {e}")

        # Network visualization
        try:
            net_viz = NetworkVisualizer(graph)
            fig = net_viz.plot_dependency_network(
                save_path=plots_dir / f"network_{timestamp}.png"
            )
            logger.info("Network visualization generated")
        except Exception as e:
            logger.warning(f"Network visualization failed: {e}")

        # Interactive network
        try:
            fig = net_viz.create_interactive_network(
                save_path=plots_dir / f"network_interactive_{timestamp}.html"
            )
            logger.info("Interactive network generated")
        except Exception as e:
            logger.warning(f"Interactive network failed: {e}")

    # Print summary
    logger.info("=" * 60)
    logger.info("Report Summary")
    logger.info("=" * 60)
    logger.info(f"Ecosystem Risk Score: {ecosystem_risk.get('overall_ecosystem_risk', 0):.3f}")
    logger.info(f"VaR (95%): ${var_metrics.get('var', 0):,.0f}")
    logger.info(f"CVaR (95%): ${var_metrics.get('cvar', 0):,.0f}")
    logger.info("")
    logger.info("Top 5 Systemic Chokepoints:")
    for s, r in chokepoints[:5]:
        logger.info(f"  {s}: {r:,.0f}")
    logger.info("")
    logger.info(f"High Risk Stablecoins: {len(ecosystem_risk.get('high_risk_stablecoins', []))}")
    logger.info(f"High Risk Protocols: {len(ecosystem_risk.get('high_risk_protocols', []))}")
    logger.info("=" * 60)
    logger.info(f"Full report saved to {args.output_dir}")


if __name__ == "__main__":
    main()
