"""Etherscan collector for on-chain data."""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from loguru import logger

try:
    from config.settings import ETHERSCAN_API_KEY
except ImportError:
    ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")


class EtherscanCollector:
    """Collect on-chain data from Etherscan API."""

    BASE_URL = "https://api.etherscan.io/api"

    # Stablecoin contract addresses
    STABLECOIN_ADDRESSES = {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI": "0x6B175474E89094C44Da98b954EescdeCB5f6f",
        "FRAX": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
        "TUSD": "0x0000000000085d4780B73119b644AE5ecd22b376",
        "USDP": "0x8E870D67F660D95d5be530380D0eC0bd388289E1",
        "GUSD": "0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd",
        "LUSD": "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0",
        "sUSD": "0x57Ab1ec28D129707052df4dF418D58a2D46d5f51",
        "USDe": "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3",
        "GHO": "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f",
        "crvUSD": "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E",
        "PYUSD": "0x6c3ea9036406852006290770BEdFcAbA0e23A0e8",
    }

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 0.2):
        """
        Initialize Etherscan collector.

        Args:
            api_key: Etherscan API key
            rate_limit: Minimum seconds between requests
        """
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.session = requests.Session()
        self.rate_limit = rate_limit
        self._last_request_time = 0

        if not self.api_key:
            logger.warning("No Etherscan API key provided. Rate limits will be strict.")

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make a rate-limited request to Etherscan."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        if self.api_key:
            params["apikey"] = self.api_key

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            self._last_request_time = time.time()
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "0":
                error_msg = data.get("message", "Unknown error")
                if "rate limit" in error_msg.lower():
                    logger.warning("Etherscan rate limit hit, waiting...")
                    time.sleep(5)
                    return self._make_request(params)
                logger.warning(f"Etherscan error: {error_msg}")
                return None

            return data

        except Exception as e:
            logger.error(f"Etherscan request failed: {e}")
            return None

    def get_token_supply(self, contract_address: str) -> Optional[float]:
        """
        Get total supply of an ERC20 token.

        Args:
            contract_address: Token contract address

        Returns:
            Total supply as float or None
        """
        params = {
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": contract_address
        }

        data = self._make_request(params)
        if data and "result" in data:
            try:
                # Most stablecoins have 6 or 18 decimals
                supply = int(data["result"])
                # Assume 6 decimals for USDT/USDC style, 18 for DAI style
                if supply > 1e24:  # Likely 18 decimals
                    return supply / 1e18
                return supply / 1e6
            except (ValueError, TypeError):
                return None
        return None

    def get_stablecoin_supply(self, symbol: str) -> Optional[float]:
        """
        Get total supply of a stablecoin by symbol.

        Args:
            symbol: Stablecoin symbol (e.g., 'USDC')

        Returns:
            Total supply or None
        """
        address = self.STABLECOIN_ADDRESSES.get(symbol.upper())
        if not address:
            logger.warning(f"Unknown stablecoin: {symbol}")
            return None
        return self.get_token_supply(address)

    def get_token_balance(
        self,
        contract_address: str,
        holder_address: str
    ) -> Optional[float]:
        """
        Get token balance for a specific holder.

        Args:
            contract_address: Token contract address
            holder_address: Holder wallet address

        Returns:
            Balance as float or None
        """
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": contract_address,
            "address": holder_address,
            "tag": "latest"
        }

        data = self._make_request(params)
        if data and "result" in data:
            try:
                balance = int(data["result"])
                if balance > 1e24:
                    return balance / 1e18
                return balance / 1e6
            except (ValueError, TypeError):
                return None
        return None

    def get_token_transfers(
        self,
        contract_address: str,
        address: Optional[str] = None,
        start_block: int = 0,
        end_block: int = 99999999,
        page: int = 1,
        offset: int = 100
    ) -> List[Dict]:
        """
        Get ERC20 token transfer events.

        Args:
            contract_address: Token contract address
            address: Filter by specific address (optional)
            start_block: Starting block number
            end_block: Ending block number
            page: Page number for pagination
            offset: Number of results per page

        Returns:
            List of transfer events
        """
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "startblock": start_block,
            "endblock": end_block,
            "page": page,
            "offset": offset,
            "sort": "desc"
        }

        if address:
            params["address"] = address

        data = self._make_request(params)
        if data and "result" in data:
            return data["result"] if isinstance(data["result"], list) else []
        return []

    def get_token_holders(
        self,
        contract_address: str,
        page: int = 1,
        offset: int = 100
    ) -> List[Dict]:
        """
        Get top token holders (requires Etherscan Pro).

        Args:
            contract_address: Token contract address
            page: Page number
            offset: Results per page

        Returns:
            List of holder data
        """
        params = {
            "module": "token",
            "action": "tokenholderlist",
            "contractaddress": contract_address,
            "page": page,
            "offset": offset
        }

        data = self._make_request(params)
        if data and "result" in data:
            return data["result"] if isinstance(data["result"], list) else []
        return []

    def get_contract_abi(self, contract_address: str) -> Optional[str]:
        """
        Get the ABI for a verified contract.

        Args:
            contract_address: Contract address

        Returns:
            ABI JSON string or None
        """
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address
        }

        data = self._make_request(params)
        if data and "result" in data:
            return data["result"]
        return None

    def get_gas_price(self) -> Optional[Dict]:
        """Get current gas prices."""
        params = {
            "module": "gastracker",
            "action": "gasoracle"
        }

        data = self._make_request(params)
        if data and "result" in data:
            return data["result"]
        return None

    def get_eth_price(self) -> Optional[float]:
        """Get current ETH price in USD."""
        params = {
            "module": "stats",
            "action": "ethprice"
        }

        data = self._make_request(params)
        if data and "result" in data:
            try:
                return float(data["result"].get("ethusd", 0))
            except (ValueError, TypeError):
                return None
        return None

    def get_internal_transactions(
        self,
        address: str,
        start_block: int = 0,
        end_block: int = 99999999
    ) -> List[Dict]:
        """
        Get internal transactions for an address.

        Args:
            address: Wallet or contract address
            start_block: Starting block
            end_block: Ending block

        Returns:
            List of internal transactions
        """
        params = {
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc"
        }

        data = self._make_request(params)
        if data and "result" in data:
            return data["result"] if isinstance(data["result"], list) else []
        return []

    def get_all_stablecoin_supplies(self) -> Dict[str, float]:
        """
        Get current supply for all known stablecoins.

        Returns:
            Dict mapping symbol to supply
        """
        supplies = {}
        for symbol, address in self.STABLECOIN_ADDRESSES.items():
            supply = self.get_token_supply(address)
            if supply is not None:
                supplies[symbol] = supply
                logger.info(f"{symbol} supply: {supply:,.0f}")

        return supplies

    def get_protocol_stablecoin_holdings(
        self,
        protocol_address: str
    ) -> Dict[str, float]:
        """
        Get stablecoin holdings for a protocol address.

        Args:
            protocol_address: Protocol treasury or vault address

        Returns:
            Dict mapping stablecoin symbol to balance
        """
        holdings = {}
        for symbol, token_address in self.STABLECOIN_ADDRESSES.items():
            balance = self.get_token_balance(token_address, protocol_address)
            if balance and balance > 0:
                holdings[symbol] = balance

        return holdings
