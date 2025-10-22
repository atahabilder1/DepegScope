"""DeFiLlama API collector for TVL and protocol data."""

import requests
from typing import Dict, List, Optional, Any
from loguru import logger
import time
from functools import lru_cache

try:
    from config.settings import DEFILLAMA_BASE_URL, DEFILLAMA_STABLECOINS_URL
except ImportError:
    DEFILLAMA_BASE_URL = "https://api.llama.fi"
    DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi"


class DeFiLlamaCollector:
    """Collect data from DeFiLlama API."""

    def __init__(self, rate_limit: float = 0.5):
        """
        Initialize DeFiLlama collector.

        Args:
            rate_limit: Minimum seconds between requests
        """
        self.base_url = DEFILLAMA_BASE_URL
        self.stablecoins_url = DEFILLAMA_STABLECOINS_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "DepegScope/1.0"
        })
        self.rate_limit = rate_limit
        self._last_request_time = 0

    def _rate_limited_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited request."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        response = self.session.get(url, params=params, timeout=30)
        self._last_request_time = time.time()
        response.raise_for_status()
        return response

    def get_all_protocols(self) -> List[Dict]:
        """Fetch all protocols with TVL data."""
        url = f"{self.base_url}/protocols"
        response = self._rate_limited_request(url)
        protocols = response.json()
        logger.info(f"Fetched {len(protocols)} protocols from DeFiLlama")
        return protocols

    def get_protocol_tvl(self, protocol_slug: str) -> Dict:
        """
        Get detailed TVL breakdown for a protocol.

        Args:
            protocol_slug: Protocol identifier (e.g., 'aave', 'uniswap')

        Returns:
            Protocol details including TVL breakdown by token and chain
        """
        url = f"{self.base_url}/protocol/{protocol_slug}"
        response = self._rate_limited_request(url)
        return response.json()

    def get_protocol_tvl_history(self, protocol_slug: str) -> List[Dict]:
        """Get historical TVL for a protocol."""
        data = self.get_protocol_tvl(protocol_slug)
        return data.get("tvl", [])

    def get_stablecoins(self) -> List[Dict]:
        """Fetch all stablecoins data."""
        url = f"{self.stablecoins_url}/stablecoins"
        response = self._rate_limited_request(url)
        data = response.json()
        stablecoins = data.get("peggedAssets", [])
        logger.info(f"Fetched {len(stablecoins)} stablecoins from DeFiLlama")
        return stablecoins

    def get_stablecoin_charts(self, stablecoin_id: int) -> Dict:
        """
        Get historical data for a stablecoin.

        Args:
            stablecoin_id: DeFiLlama stablecoin ID

        Returns:
            Historical market cap and price data
        """
        url = f"{self.stablecoins_url}/stablecoin/{stablecoin_id}"
        response = self._rate_limited_request(url)
        return response.json()

    def get_stablecoin_prices(self) -> List[Dict]:
        """Get current prices for all stablecoins."""
        url = f"{self.stablecoins_url}/stablecoinprices"
        response = self._rate_limited_request(url)
        return response.json()

    def get_stablecoin_chains(self) -> Dict:
        """Get stablecoin distribution across chains."""
        url = f"{self.stablecoins_url}/stablecoinchains"
        response = self._rate_limited_request(url)
        return response.json()

    def get_pools(self) -> List[Dict]:
        """Fetch all liquidity pools."""
        url = "https://yields.llama.fi/pools"
        response = self._rate_limited_request(url)
        data = response.json()
        pools = data.get("data", [])
        logger.info(f"Fetched {len(pools)} pools from DeFiLlama")
        return pools

    def get_protocol_treasury(self, protocol_slug: str) -> Dict:
        """Get treasury holdings for a protocol."""
        url = f"{self.base_url}/treasury/{protocol_slug}"
        try:
            response = self._rate_limited_request(url)
            return response.json()
        except requests.exceptions.HTTPError:
            logger.warning(f"No treasury data for {protocol_slug}")
            return {}

    def get_stablecoin_pools(self, min_tvl: float = 100_000) -> List[Dict]:
        """
        Filter pools containing stablecoins.

        Args:
            min_tvl: Minimum TVL in USD to include pool

        Returns:
            List of pools containing at least one stablecoin
        """
        pools = self.get_pools()
        stablecoin_symbols = {
            "USDT", "USDC", "DAI", "FRAX", "TUSD", "LUSD",
            "sUSD", "USDe", "GHO", "crvUSD", "FDUSD", "PYUSD",
            "USDP", "GUSD", "MIM", "BUSD"
        }

        stablecoin_pools = []
        for pool in pools:
            # Check TVL threshold
            if pool.get("tvlUsd", 0) < min_tvl:
                continue

            # Check if pool contains stablecoins
            symbol = pool.get("symbol", "").upper()
            tokens = set(symbol.replace("/", "-").split("-"))

            if tokens & stablecoin_symbols:
                # Calculate stablecoin composition
                pool["stablecoin_tokens"] = list(tokens & stablecoin_symbols)
                pool["stablecoin_count"] = len(pool["stablecoin_tokens"])
                stablecoin_pools.append(pool)

        logger.info(f"Found {len(stablecoin_pools)} stablecoin pools with TVL >= ${min_tvl:,.0f}")
        return stablecoin_pools

    def get_protocol_stablecoin_exposure(self, protocol_slug: str) -> Dict[str, float]:
        """
        Calculate a protocol's exposure to each stablecoin.

        Args:
            protocol_slug: Protocol identifier

        Returns:
            Dict mapping stablecoin symbol to USD exposure
        """
        stablecoin_symbols = {
            "USDT", "USDC", "DAI", "FRAX", "TUSD", "LUSD",
            "sUSD", "USDe", "GHO", "crvUSD", "FDUSD", "PYUSD"
        }

        try:
            data = self.get_protocol_tvl(protocol_slug)
        except Exception as e:
            logger.warning(f"Failed to get TVL for {protocol_slug}: {e}")
            return {}

        exposures = {}

        # Check token breakdown if available
        tokens = data.get("tokens", [])
        if tokens:
            for token_data in tokens:
                symbol = token_data.get("symbol", "").upper()
                if symbol in stablecoin_symbols:
                    exposures[symbol] = exposures.get(symbol, 0) + token_data.get("value", 0)

        # Also check currentChainTvls for stablecoin mentions
        chain_tvls = data.get("currentChainTvls", {})
        for chain, tvl in chain_tvls.items():
            chain_upper = chain.upper()
            for stable in stablecoin_symbols:
                if stable in chain_upper:
                    exposures[stable] = exposures.get(stable, 0) + tvl

        return exposures

    def get_top_protocols_by_tvl(self, limit: int = 100) -> List[Dict]:
        """Get top protocols sorted by TVL."""
        protocols = self.get_all_protocols()
        sorted_protocols = sorted(
            protocols,
            key=lambda x: x.get("tvl", 0) or 0,
            reverse=True
        )
        return sorted_protocols[:limit]

    def get_protocols_by_category(self, category: str) -> List[Dict]:
        """
        Get protocols filtered by category.

        Args:
            category: Category like 'Lending', 'Dexes', 'Bridge', etc.

        Returns:
            List of protocols in that category
        """
        protocols = self.get_all_protocols()
        return [p for p in protocols if p.get("category", "").lower() == category.lower()]

    def build_exposure_matrix(self, protocol_slugs: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Build a matrix of protocol -> stablecoin exposures.

        Args:
            protocol_slugs: List of protocol identifiers

        Returns:
            Nested dict: {protocol: {stablecoin: exposure_usd}}
        """
        matrix = {}
        for slug in protocol_slugs:
            try:
                exposures = self.get_protocol_stablecoin_exposure(slug)
                if exposures:
                    matrix[slug] = exposures
            except Exception as e:
                logger.warning(f"Failed to get exposure for {slug}: {e}")
                continue

        logger.info(f"Built exposure matrix for {len(matrix)} protocols")
        return matrix
