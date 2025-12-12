#!/usr/bin/env python3
"""Build dependency graph from collected data."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.models.stablecoin import Stablecoin, StablecoinType
from src.models.protocol import Protocol
from src.models.exposure import Exposure, ExposureType
from src.analysis.dependency_graph import DependencyGraph
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level
    )


def load_stablecoins(data_dir: Path) -> list:
    """Load stablecoin data."""
    file_path = data_dir / "stablecoins.json"
    if not file_path.exists():
        logger.warning(f"Stablecoin file not found: {file_path}")
        return []

    with open(file_path) as f:
        data = json.load(f)

    stablecoins = []
    for item in data:
        try:
            stablecoin = Stablecoin(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                stablecoin_type=StablecoinType.UNKNOWN,
                contract_address=item.get("address", ""),
                market_cap=item.get("circulating", {}).get("peggedUSD", 0) or 0,
                defillama_id=item.get("id")
            )
            stablecoins.append(stablecoin)
        except Exception as e:
            logger.debug(f"Skipping stablecoin: {e}")

    return stablecoins


def load_protocols(data_dir: Path) -> list:
    """Load protocol data."""
    file_path = data_dir / "protocols.json"
    if not file_path.exists():
        logger.warning(f"Protocol file not found: {file_path}")
        return []

    with open(file_path) as f:
        data = json.load(f)

    protocols = []
    for item in data:
        try:
            protocol = Protocol.from_defillama(item)
            if protocol.tvl and protocol.tvl > 0:
                protocols.append(protocol)
        except Exception as e:
            logger.debug(f"Skipping protocol: {e}")

    return protocols


def load_exposures(data_dir: Path, protocols: list) -> list:
    """Load and create exposure relationships."""
    file_path = data_dir / "exposure_matrix.json"
    if not file_path.exists():
        logger.warning(f"Exposure file not found: {file_path}")
        return []

    with open(file_path) as f:
        matrix = json.load(f)

    # Create lookup for protocol TVL
    protocol_tvl = {p.slug: p.tvl for p in protocols}

    exposures = []
    for protocol_slug, stablecoin_exposures in matrix.items():
        tvl = protocol_tvl.get(protocol_slug, 1)

        for stablecoin, amount in stablecoin_exposures.items():
            if amount > 0:
                exposure = Exposure(
                    protocol_name=protocol_slug,
                    stablecoin_symbol=stablecoin,
                    exposure_type=ExposureType.LIQUIDITY,
                    amount_usd=amount,
                    percentage_of_tvl=amount / tvl if tvl > 0 else 0,
                    source="defillama"
                )
                exposures.append(exposure)

    return exposures


def build_graph(
    stablecoins: list,
    protocols: list,
    exposures: list
) -> DependencyGraph:
    """Build the dependency graph."""
    graph = DependencyGraph()
    graph.build_from_data(stablecoins, protocols, exposures)
    return graph


def main():
    parser = argparse.ArgumentParser(
        description="Build stablecoin-protocol dependency graph"
    )

    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory with raw data files"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Output directory for processed data"
    )
    parser.add_argument(
        "--min-tvl",
        type=float,
        default=1_000_000,
        help="Minimum protocol TVL to include (default: 1M)"
    )
    parser.add_argument(
        "--export-graph",
        action="store_true",
        help="Export graph for visualization"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    logger.info("=" * 60)
    logger.info("Building Dependency Graph")
    logger.info("=" * 60)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading stablecoins...")
    stablecoins = load_stablecoins(args.data_dir)
    logger.info(f"Loaded {len(stablecoins)} stablecoins")

    logger.info("Loading protocols...")
    protocols = load_protocols(args.data_dir)
    protocols = [p for p in protocols if p.tvl >= args.min_tvl]
    logger.info(f"Loaded {len(protocols)} protocols (TVL >= ${args.min_tvl:,.0f})")

    logger.info("Loading exposures...")
    exposures = load_exposures(args.data_dir, protocols)
    logger.info(f"Loaded {len(exposures)} exposure relationships")

    # Build graph
    logger.info("Building dependency graph...")
    graph = build_graph(stablecoins, protocols, exposures)

    # Get summary
    summary = graph.summary()
    logger.info(f"Graph summary:")
    logger.info(f"  Nodes: {summary['nodes']}")
    logger.info(f"  Edges: {summary['edges']}")
    logger.info(f"  Stablecoins: {summary['stablecoins']}")
    logger.info(f"  Protocols: {summary['protocols']}")
    logger.info(f"  Total exposure: ${summary['total_exposure_usd']:,.0f}")

    # Calculate centrality
    logger.info("Calculating centrality metrics...")
    centrality = graph.calculate_centrality_metrics()

    # Save centrality
    centrality_file = args.output_dir / "centrality_metrics.csv"
    centrality.to_csv(centrality_file, index=False)
    logger.info(f"Saved centrality metrics to {centrality_file}")

    # Find systemic chokepoints
    logger.info("Identifying systemic chokepoints...")
    chokepoints = graph.find_systemic_chokepoints()

    logger.info("Top 5 systemic chokepoints:")
    for stablecoin, score in chokepoints[:5]:
        logger.info(f"  {stablecoin}: {score:,.0f}")

    # Export for visualization
    if args.export_graph:
        logger.info("Exporting graph for visualization...")
        viz_data = graph.export_for_visualization()
        viz_file = args.output_dir / "graph_visualization.json"
        with open(viz_file, "w") as f:
            json.dump(viz_data, f, indent=2)
        logger.info(f"Saved visualization data to {viz_file}")

    # Save processed data
    logger.info("Saving processed data...")

    stablecoins_processed = [s.to_dict() for s in stablecoins]
    with open(args.output_dir / "stablecoins_processed.json", "w") as f:
        json.dump(stablecoins_processed, f, indent=2)

    protocols_processed = [p.to_dict() for p in protocols]
    with open(args.output_dir / "protocols_processed.json", "w") as f:
        json.dump(protocols_processed, f, indent=2)

    exposures_processed = [e.to_dict() for e in exposures]
    with open(args.output_dir / "exposures_processed.json", "w") as f:
        json.dump(exposures_processed, f, indent=2)

    logger.info("=" * 60)
    logger.info("Graph building complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
