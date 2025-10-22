"""Data collectors for DepegScope."""

from .defillama import DeFiLlamaCollector
from .price_feeds import PriceFeedCollector, COINGECKO_IDS

__all__ = ["DeFiLlamaCollector", "PriceFeedCollector", "COINGECKO_IDS"]
