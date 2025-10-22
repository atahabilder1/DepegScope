"""The Graph collector for DeFi protocol data."""

import os
import requests
from typing import Dict, List, Optional, Any
from loguru import logger

try:
    from config.settings import THEGRAPH_API_KEY
except ImportError:
    THEGRAPH_API_KEY = os.getenv("THEGRAPH_API_KEY")


class TheGraphCollector:
    """Collect data from The Graph subgraphs."""

    # Subgraph endpoints for major DeFi protocols
    SUBGRAPHS = {
        "uniswap_v3": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "uniswap_v2": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
        "aave_v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
        "aave_v2": "https://api.thegraph.com/subgraphs/name/aave/protocol-v2",
        "compound_v3": "https://api.thegraph.com/subgraphs/name/compound-finance/compound-v3",
        "curve": "https://api.thegraph.com/subgraphs/name/convex-community/curve-pools",
        "maker": "https://api.thegraph.com/subgraphs/name/makerdao/maker-protocol",
        "balancer_v2": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize The Graph collector.

        Args:
            api_key: The Graph API key for gateway access
        """
        self.api_key = api_key or THEGRAPH_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"

    def _query_subgraph(
        self,
        subgraph_url: str,
        query: str,
        variables: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Execute a GraphQL query against a subgraph.

        Args:
            subgraph_url: Subgraph endpoint URL
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Query response data or None on failure
        """
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables

            response = self.session.post(subgraph_url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            return data.get("data")

        except Exception as e:
            logger.error(f"Subgraph query failed: {e}")
            return None

    def get_uniswap_v3_pools(
        self,
        stablecoin_addresses: List[str],
        min_tvl: float = 100_000
    ) -> List[Dict]:
        """
        Get Uniswap V3 pools containing stablecoins.

        Args:
            stablecoin_addresses: List of stablecoin token addresses
            min_tvl: Minimum TVL in USD

        Returns:
            List of pool data
        """
        query = """
        query GetPools($tokens: [String!], $minTvl: BigDecimal) {
            pools(
                where: {
                    or: [
                        {token0_in: $tokens},
                        {token1_in: $tokens}
                    ],
                    totalValueLockedUSD_gte: $minTvl
                },
                first: 100,
                orderBy: totalValueLockedUSD,
                orderDirection: desc
            ) {
                id
                token0 { id symbol decimals }
                token1 { id symbol decimals }
                totalValueLockedUSD
                volumeUSD
                feeTier
                liquidity
                token0Price
                token1Price
            }
        }
        """

        variables = {
            "tokens": [addr.lower() for addr in stablecoin_addresses],
            "minTvl": str(min_tvl)
        }

        data = self._query_subgraph(self.SUBGRAPHS["uniswap_v3"], query, variables)
        if data:
            return data.get("pools", [])
        return []

    def get_aave_reserves(self) -> List[Dict]:
        """Get Aave reserve data including stablecoin deposits."""
        query = """
        {
            reserves(first: 100) {
                id
                symbol
                name
                decimals
                totalLiquidity
                totalCurrentVariableDebt
                totalDeposits
                liquidityRate
                variableBorrowRate
                utilizationRate
                price { priceInEth }
            }
        }
        """

        data = self._query_subgraph(self.SUBGRAPHS["aave_v3"], query)
        if data:
            return data.get("reserves", [])
        return []

    def get_curve_pools(self) -> List[Dict]:
        """Get Curve pool data."""
        query = """
        {
            pools(first: 100, orderBy: totalValueLockedUSD, orderDirection: desc) {
                id
                name
                symbol
                coins
                coinDecimals
                totalValueLockedUSD
                volumeUSD
                lpToken
                virtualPrice
            }
        }
        """

        data = self._query_subgraph(self.SUBGRAPHS["curve"], query)
        if data:
            return data.get("pools", [])
        return []

    def get_maker_collateral_types(self) -> List[Dict]:
        """Get MakerDAO collateral types and DAI exposure."""
        query = """
        {
            collateralTypes(first: 50) {
                id
                totalDebt
                totalCollateral
                rate
                liquidationRatio
                stabilityFee
            }
        }
        """

        data = self._query_subgraph(self.SUBGRAPHS["maker"], query)
        if data:
            return data.get("collateralTypes", [])
        return []

    def get_compound_markets(self) -> List[Dict]:
        """Get Compound market data."""
        query = """
        {
            markets(first: 50) {
                id
                symbol
                name
                totalSupply
                totalBorrows
                supplyRate
                borrowRate
                collateralFactor
                underlyingPriceUSD
            }
        }
        """

        data = self._query_subgraph(self.SUBGRAPHS["compound_v3"], query)
        if data:
            return data.get("markets", [])
        return []

    def get_balancer_pools(
        self,
        stablecoin_addresses: List[str]
    ) -> List[Dict]:
        """Get Balancer pools containing stablecoins."""
        query = """
        query GetPools($tokens: [String!]) {
            pools(
                where: { tokensList_contains: $tokens },
                first: 100,
                orderBy: totalLiquidity,
                orderDirection: desc
            ) {
                id
                name
                symbol
                poolType
                totalLiquidity
                totalSwapVolume
                swapFee
                tokens {
                    address
                    symbol
                    balance
                    weight
                }
            }
        }
        """

        variables = {"tokens": [addr.lower() for addr in stablecoin_addresses]}

        data = self._query_subgraph(self.SUBGRAPHS["balancer_v2"], query, variables)
        if data:
            return data.get("pools", [])
        return []

    def get_protocol_tvl_breakdown(self, protocol: str) -> Optional[Dict]:
        """
        Get TVL breakdown by token for a protocol.

        Args:
            protocol: Protocol name (must be in SUBGRAPHS)

        Returns:
            TVL breakdown data
        """
        if protocol not in self.SUBGRAPHS:
            logger.warning(f"No subgraph for protocol: {protocol}")
            return None

        # Generic TVL query (protocol-specific queries should be used in practice)
        query = """
        {
            protocol(id: "1") {
                totalValueLockedUSD
            }
        }
        """

        return self._query_subgraph(self.SUBGRAPHS[protocol], query)

    def get_recent_swaps(
        self,
        pool_id: str,
        subgraph: str = "uniswap_v3",
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent swaps for a pool.

        Args:
            pool_id: Pool identifier
            subgraph: Which DEX subgraph to query
            limit: Maximum number of swaps

        Returns:
            List of swap data
        """
        query = """
        query GetSwaps($poolId: String!, $limit: Int!) {
            swaps(
                where: { pool: $poolId },
                first: $limit,
                orderBy: timestamp,
                orderDirection: desc
            ) {
                id
                timestamp
                amount0
                amount1
                amountUSD
                sender
            }
        }
        """

        variables = {"poolId": pool_id.lower(), "limit": limit}

        data = self._query_subgraph(self.SUBGRAPHS.get(subgraph, ""), query, variables)
        if data:
            return data.get("swaps", [])
        return []
