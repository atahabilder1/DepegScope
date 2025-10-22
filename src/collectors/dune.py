"""Dune Analytics collector for on-chain data."""

import os
import time
from typing import Dict, List, Optional, Any
from loguru import logger

try:
    from dune_client.client import DuneClient
    from dune_client.query import QueryBase
    from dune_client.types import QueryParameter
    DUNE_AVAILABLE = True
except ImportError:
    DUNE_AVAILABLE = False
    logger.warning("dune-client not installed. Dune collector will be limited.")

try:
    from config.settings import DUNE_API_KEY
except ImportError:
    DUNE_API_KEY = os.getenv("DUNE_API_KEY")


class DuneCollector:
    """Collect on-chain data from Dune Analytics."""

    # Pre-defined query IDs for stablecoin analysis
    QUERIES = {
        "stablecoin_transfers": 3456789,  # Example query ID
        "protocol_tvl_breakdown": 3456790,
        "curve_pool_balances": 3456791,
        "liquidation_events": 3456792,
        "whale_movements": 3456793,
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Dune collector.

        Args:
            api_key: Dune Analytics API key
        """
        self.api_key = api_key or DUNE_API_KEY
        self.client = None

        if DUNE_AVAILABLE and self.api_key:
            try:
                self.client = DuneClient(self.api_key)
                logger.info("Dune Analytics client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Dune client: {e}")

    def is_available(self) -> bool:
        """Check if Dune client is available."""
        return self.client is not None

    def execute_query(
        self,
        query_id: int,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict]]:
        """
        Execute a Dune query and return results.

        Args:
            query_id: Dune query ID
            parameters: Optional query parameters

        Returns:
            List of result rows or None on failure
        """
        if not self.is_available():
            logger.warning("Dune client not available")
            return None

        try:
            query = QueryBase(query_id=query_id)

            if parameters:
                query_params = [
                    QueryParameter.text_type(k, str(v))
                    for k, v in parameters.items()
                ]
                results = self.client.run_query(query, query_params)
            else:
                results = self.client.run_query(query)

            if results and results.result:
                return results.result.rows

            return None

        except Exception as e:
            logger.error(f"Dune query {query_id} failed: {e}")
            return None

    def get_stablecoin_transfer_volume(
        self,
        stablecoin: str,
        days: int = 30
    ) -> Optional[List[Dict]]:
        """
        Get transfer volume for a stablecoin.

        Args:
            stablecoin: Stablecoin symbol
            days: Number of days to look back

        Returns:
            Daily transfer volume data
        """
        # This would use a custom Dune query
        # For now, return placeholder
        logger.info(f"Would fetch {stablecoin} transfer volume for {days} days")
        return None

    def get_curve_pool_composition(self, pool_address: str) -> Optional[Dict]:
        """
        Get current composition of a Curve pool.

        Args:
            pool_address: Ethereum address of the Curve pool

        Returns:
            Pool composition data
        """
        # This would query Curve pool state from Dune
        logger.info(f"Would fetch Curve pool {pool_address} composition")
        return None

    def get_protocol_stablecoin_holdings(
        self,
        protocol_addresses: List[str]
    ) -> Optional[List[Dict]]:
        """
        Get stablecoin holdings for a list of protocol addresses.

        Args:
            protocol_addresses: List of protocol contract addresses

        Returns:
            Holdings data per address
        """
        logger.info(f"Would fetch holdings for {len(protocol_addresses)} addresses")
        return None

    def get_liquidation_events(
        self,
        protocol: str,
        days: int = 30
    ) -> Optional[List[Dict]]:
        """
        Get recent liquidation events for a lending protocol.

        Args:
            protocol: Protocol name (e.g., 'aave', 'compound')
            days: Number of days to look back

        Returns:
            Liquidation event data
        """
        logger.info(f"Would fetch {protocol} liquidations for {days} days")
        return None

    def get_whale_stablecoin_movements(
        self,
        stablecoin: str,
        min_amount: float = 1_000_000
    ) -> Optional[List[Dict]]:
        """
        Get large stablecoin transfers (whale movements).

        Args:
            stablecoin: Stablecoin symbol
            min_amount: Minimum transfer amount in USD

        Returns:
            Large transfer data
        """
        logger.info(f"Would fetch {stablecoin} whale movements >= ${min_amount:,.0f}")
        return None

    def get_redemption_data(
        self,
        stablecoin: str,
        days: int = 7
    ) -> Optional[List[Dict]]:
        """
        Get redemption/mint data for a stablecoin.

        Args:
            stablecoin: Stablecoin symbol
            days: Number of days to look back

        Returns:
            Mint/redeem data
        """
        logger.info(f"Would fetch {stablecoin} redemption data for {days} days")
        return None


class DuneQueryBuilder:
    """Helper class to build custom Dune queries."""

    @staticmethod
    def stablecoin_balance_query(
        token_address: str,
        holder_addresses: List[str]
    ) -> str:
        """Build a query for stablecoin balances."""
        holders_list = ", ".join([f"'{addr}'" for addr in holder_addresses])
        return f"""
        SELECT
            holder,
            balance / 1e18 as balance_tokens,
            balance / 1e18 * price as balance_usd
        FROM erc20_ethereum.evt_Transfer
        WHERE contract_address = '{token_address}'
        AND holder IN ({holders_list})
        """

    @staticmethod
    def pool_imbalance_query(pool_address: str) -> str:
        """Build a query for pool balance imbalance over time."""
        return f"""
        SELECT
            block_time,
            token_a_balance,
            token_b_balance,
            ABS(token_a_balance - token_b_balance) /
                NULLIF(token_a_balance + token_b_balance, 0) as imbalance_ratio
        FROM curve_pools
        WHERE pool_address = '{pool_address}'
        ORDER BY block_time DESC
        LIMIT 1000
        """
