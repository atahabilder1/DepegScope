#!/usr/bin/env python3
"""Collect all data needed for DepegScope analysis.

Two modes available:
  --free       Use only free APIs (DeFiLlama) - no rate limits
  --premium    Use CoinGecko API for price history (requires API key)

Default is --free mode.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from tqdm import tqdm

from src.collectors.defillama import DeFiLlamaCollector
from src.collectors.price_feeds import PriceFeedCollector, COINGECKO_IDS
from config.settings import RAW_DATA_DIR, MAJOR_STABLECOINS


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level
    )


def collect_stablecoins(collector: DeFiLlamaCollector, output_dir: Path) -> int:
    """Collect stablecoin data from DeFiLlama."""
    logger.info("Collecting stablecoin data from DeFiLlama...")
    stablecoins = collector.get_stablecoins()

    output_file = output_dir / "stablecoins.json"
    with open(output_file, "w") as f:
        json.dump(stablecoins, f, indent=2)

    logger.info(f"Saved {len(stablecoins)} stablecoins to {output_file}")
    return len(stablecoins)


def collect_protocols(collector: DeFiLlamaCollector, output_dir: Path) -> int:
    """Collect protocol data from DeFiLlama."""
    logger.info("Collecting protocol data from DeFiLlama...")
    protocols = collector.get_all_protocols()

    output_file = output_dir / "protocols.json"
    with open(output_file, "w") as f:
        json.dump(protocols, f, indent=2)

    logger.info(f"Saved {len(protocols)} protocols to {output_file}")
    return len(protocols)


def collect_pools(collector: DeFiLlamaCollector, output_dir: Path, min_tvl: float) -> int:
    """Collect stablecoin pool data."""
    logger.info(f"Collecting stablecoin pools (min TVL: ${min_tvl:,.0f})...")
    pools = collector.get_stablecoin_pools(min_tvl=min_tvl)

    output_file = output_dir / "stablecoin_pools.json"
    with open(output_file, "w") as f:
        json.dump(pools, f, indent=2)

    logger.info(f"Saved {len(pools)} stablecoin pools to {output_file}")
    return len(pools)


def collect_price_history(
    collector: PriceFeedCollector,
    output_dir: Path,
    days: int,
    stablecoins: list
) -> int:
    """Collect historical price data for stablecoins."""
    logger.info(f"Collecting price history ({days} days) for stablecoins...")
    price_history = {}
    collected = 0

    for symbol in tqdm(stablecoins, desc="Collecting prices"):
        coin_id = COINGECKO_IDS.get(symbol)
        if not coin_id:
            logger.warning(f"No CoinGecko ID for {symbol}, skipping")
            continue

        try:
            df = collector.get_price_history(coin_id, days=days)
            # Convert to serializable format - use string keys for timestamps
            timestamps = [str(t) for t in df.index]
            price_history[symbol] = {
                "prices": {str(k): v for k, v in df["price"].to_dict().items()},
                "timestamps": timestamps,
            }
            if "market_cap" in df.columns:
                price_history[symbol]["market_cap"] = {str(k): v for k, v in df["market_cap"].to_dict().items()}
            if "volume" in df.columns:
                price_history[symbol]["volume"] = {str(k): v for k, v in df["volume"].to_dict().items()}

            collected += 1
            logger.debug(f"Collected {symbol} price history")
        except Exception as e:
            logger.warning(f"Failed to collect {symbol}: {e}")

    output_file = output_dir / "price_history.json"
    with open(output_file, "w") as f:
        json.dump(price_history, f, indent=2, default=str)

    logger.info(f"Saved price history for {collected} stablecoins to {output_file}")
    return collected


def collect_exposures(
    collector: DeFiLlamaCollector,
    output_dir: Path,
    top_n: int
) -> int:
    """Collect protocol stablecoin exposures (legacy method)."""
    logger.info(f"Collecting stablecoin exposures for top {top_n} protocols...")

    top_protocols = collector.get_top_protocols_by_tvl(limit=top_n)
    slugs = [p["slug"] for p in top_protocols if "slug" in p]

    exposure_matrix = collector.build_exposure_matrix(slugs)

    output_file = output_dir / "exposure_matrix.json"
    with open(output_file, "w") as f:
        json.dump(exposure_matrix, f, indent=2)

    logger.info(f"Saved exposure matrix for {len(exposure_matrix)} protocols")
    return len(exposure_matrix)


def build_exposure_from_pools(output_dir: Path, min_exposure: float = 100_000) -> int:
    """Build exposure matrix from pools data (FREE - no API key needed).

    This extracts protocol-stablecoin relationships from pool data.
    """
    pools_file = output_dir / "stablecoin_pools.json"
    if not pools_file.exists():
        logger.error("Pools file not found. Run pool collection first.")
        return 0

    logger.info("Building exposure matrix from pools data (FREE)...")

    with open(pools_file) as f:
        pools = json.load(f)

    # Known stablecoin symbols to detect
    stablecoin_symbols = {
        'USDT', 'USDC', 'DAI', 'FRAX', 'LUSD', 'USDS', 'USDe', 'GHO',
        'crvUSD', 'FDUSD', 'TUSD', 'USDP', 'GUSD', 'PYUSD', 'MIM',
        'BUSD', 'sUSD', 'RAI', 'DOLA', 'ALUSD', 'USDD', 'USX', 'OUSD',
        'EURS', 'EURT', 'EURC', 'agEUR', 'USDJ', 'USDN', 'FEI'
    }

    exposure_matrix = defaultdict(lambda: defaultdict(float))

    for pool in pools:
        project = pool.get('project', 'unknown')
        symbol = pool.get('symbol', '')
        tvl = pool.get('tvlUsd', 0) or 0

        # Extract stablecoins from pool symbol
        for stable in stablecoin_symbols:
            if stable.upper() in symbol.upper():
                exposure_matrix[project][stable] += tvl

    # Filter and convert to regular dict
    exposure_dict = {}
    for protocol, exposures in exposure_matrix.items():
        total = sum(exposures.values())
        if total >= min_exposure:
            exposure_dict[protocol] = dict(exposures)

    # Save
    output_file = output_dir / "exposure_matrix.json"
    with open(output_file, "w") as f:
        json.dump(exposure_dict, f, indent=2)

    total_relationships = sum(len(v) for v in exposure_dict.values())
    logger.info(f"Built exposure matrix: {len(exposure_dict)} protocols, {total_relationships} relationships")

    return total_relationships


def main():
    parser = argparse.ArgumentParser(
        description="Collect data for DepegScope analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  --free       Use only DeFiLlama (FREE, no rate limits) [DEFAULT]
  --premium    Use CoinGecko API for price history (requires API key)

Examples:
  %(prog)s                          # Free mode - DeFiLlama only
  %(prog)s --free                   # Explicitly use free mode
  %(prog)s --premium --days 90      # Premium mode with 90 days history
  %(prog)s --premium --api-key KEY  # Premium mode with API key
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--free",
        action="store_true",
        default=True,
        help="Use only free APIs (DeFiLlama) - DEFAULT"
    )
    mode_group.add_argument(
        "--premium",
        action="store_true",
        help="Use CoinGecko API for price history (requires API key)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="CoinGecko API key (for premium mode)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=RAW_DATA_DIR,
        help="Output directory for data files"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=365,
        help="Days of price history to collect (default: 365, premium only)"
    )
    parser.add_argument(
        "--top-protocols", "-t",
        type=int,
        default=100,
        help="Number of top protocols for exposure collection (default: 100)"
    )
    parser.add_argument(
        "--min-pool-tvl",
        type=float,
        default=100_000,
        help="Minimum pool TVL to include (default: 100000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # If premium is set, free should be False
    if args.premium:
        args.free = False

    setup_logging(args.verbose)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("DepegScope Data Collection")
    logger.info("=" * 60)
    mode_str = "FREE (DeFiLlama only)" if args.free else "PREMIUM (with CoinGecko)"
    logger.info(f"Mode: {mode_str}")
    logger.info(f"Output directory: {args.output_dir}")
    if not args.free:
        logger.info(f"Price history: {args.days} days")

    # Initialize collectors
    llama = DeFiLlamaCollector()

    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "free" if args.free else "premium",
        "stablecoins": 0,
        "protocols": 0,
        "pools": 0,
        "prices": 0,
        "exposures": 0
    }

    try:
        # 1. Collect stablecoins (FREE)
        stats["stablecoins"] = collect_stablecoins(llama, args.output_dir)

        # 2. Collect protocols (FREE)
        stats["protocols"] = collect_protocols(llama, args.output_dir)

        # 3. Collect pools (FREE)
        stats["pools"] = collect_pools(llama, args.output_dir, args.min_pool_tvl)

        # 4. Build exposure matrix from pools (FREE)
        stats["exposures"] = build_exposure_from_pools(args.output_dir, args.min_pool_tvl)

        # 5. Collect price history (PREMIUM only)
        if not args.free:
            logger.info("Collecting price history (PREMIUM)...")
            price_collector = PriceFeedCollector(api_key=args.api_key)
            stats["prices"] = collect_price_history(
                price_collector,
                args.output_dir,
                args.days,
                MAJOR_STABLECOINS
            )
        else:
            logger.info("Skipping price history (FREE mode - use --premium for this)")
            stats["prices"] = 0

        # Save collection stats
        stats_file = args.output_dir / "collection_stats.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

        logger.info("=" * 60)
        logger.info("Data collection complete!")
        logger.info(f"  Mode: {stats['mode'].upper()}")
        logger.info(f"  Stablecoins: {stats['stablecoins']}")
        logger.info(f"  Protocols: {stats['protocols']}")
        logger.info(f"  Pools: {stats['pools']}")
        logger.info(f"  Exposures: {stats['exposures']}")
        if not args.free:
            logger.info(f"  Price histories: {stats['prices']}")
        logger.info("=" * 60)

        if args.free:
            logger.info("TIP: Run with --premium for price history data")

    except KeyboardInterrupt:
        logger.warning("Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
