"""Price feed collector for stablecoin prices."""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
import time

try:
    from config.settings import COINGECKO_BASE_URL, COINGECKO_API_KEY
except ImportError:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    COINGECKO_API_KEY = None

# Mapping of stablecoin symbols to CoinGecko IDs
COINGECKO_IDS = {
    "USDT": "tether",
    "USDC": "usd-coin",
    "DAI": "dai",
    "FRAX": "frax",
    "LUSD": "liquity-usd",
    "sUSD": "nusd",
    "USDe": "ethena-usde",
    "GHO": "gho",
    "crvUSD": "crvusd",
    "FDUSD": "first-digital-usd",
    "TUSD": "true-usd",
    "USDP": "paxos-standard",
    "GUSD": "gemini-dollar",
    "PYUSD": "paypal-usd",
    "MIM": "magic-internet-money",
    "BUSD": "binance-usd",
}


class PriceFeedCollector:
    """Collect historical and real-time stablecoin prices."""

    def __init__(self, api_key: Optional[str] = None, rate_limit: float = 6.0):
        """
        Initialize price feed collector.

        Args:
            api_key: Optional CoinGecko API key for higher rate limits
            rate_limit: Minimum seconds between requests (default 6s for free tier)
        """
        self.base_url = COINGECKO_BASE_URL
        self.api_key = api_key or COINGECKO_API_KEY
        self.session = requests.Session()
        # CoinGecko free tier: 10-30 calls/min, use 6s to be safe
        self.rate_limit = rate_limit if not self.api_key else 1.5
        self._last_request_time = 0

        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        self.session.headers.update(headers)

    def _rate_limited_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited request."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        response = self.session.get(url, params=params, timeout=30)
        self._last_request_time = time.time()
        response.raise_for_status()
        return response

    def get_price_history(
        self,
        coin_id: str,
        days: int = 365,
        vs_currency: str = "usd"
    ) -> pd.DataFrame:
        """
        Get historical price data.

        Args:
            coin_id: CoinGecko coin identifier
            days: Number of days of history
            vs_currency: Quote currency

        Returns:
            DataFrame with timestamp index and price column
        """
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily" if days > 90 else "hourly"
        }

        response = self._rate_limited_request(url, params)
        data = response.json()

        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # Add market cap and volume if available
        if "market_caps" in data:
            mc_df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
            mc_df["timestamp"] = pd.to_datetime(mc_df["timestamp"], unit="ms")
            mc_df.set_index("timestamp", inplace=True)
            df = df.join(mc_df["market_cap"], how="left")

        if "total_volumes" in data:
            vol_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
            vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
            vol_df.set_index("timestamp", inplace=True)
            df = df.join(vol_df["volume"], how="left")

        logger.info(f"Fetched {len(df)} price points for {coin_id}")
        return df

    def get_stablecoin_history(
        self,
        symbol: str,
        days: int = 365
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a stablecoin by symbol.

        Args:
            symbol: Stablecoin symbol (e.g., 'USDC')
            days: Number of days of history

        Returns:
            DataFrame with price history or None if not found
        """
        coin_id = COINGECKO_IDS.get(symbol.upper())
        if not coin_id:
            logger.warning(f"No CoinGecko ID for {symbol}")
            return None

        try:
            return self.get_price_history(coin_id, days)
        except Exception as e:
            logger.error(f"Failed to get history for {symbol}: {e}")
            return None

    def detect_depeg_events(
        self,
        prices: pd.DataFrame,
        threshold: float = 0.02,
        min_duration_hours: int = 1
    ) -> List[Dict]:
        """
        Detect depeg events from price history.

        Args:
            prices: DataFrame with 'price' column
            threshold: Deviation threshold from $1.00
            min_duration_hours: Minimum event duration

        Returns:
            List of depeg event dictionaries
        """
        df = prices.copy()
        df["deviation"] = abs(df["price"] - 1.0)
        df["is_depegged"] = df["deviation"] > threshold

        # Find contiguous depeg periods
        df["depeg_group"] = (df["is_depegged"] != df["is_depegged"].shift()).cumsum()

        depeg_events = []
        for group_id, group in df[df["is_depegged"]].groupby("depeg_group"):
            duration_hours = (group.index.max() - group.index.min()).total_seconds() / 3600

            if duration_hours < min_duration_hours:
                continue

            event = {
                "start_date": group.index.min(),
                "end_date": group.index.max(),
                "duration_hours": duration_hours,
                "min_price": group["price"].min(),
                "max_price": group["price"].max(),
                "max_deviation": group["deviation"].max(),
                "direction": "below" if group["price"].min() < 1.0 else "above",
                "avg_price": group["price"].mean(),
            }
            depeg_events.append(event)

        return depeg_events

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple stablecoins.

        Args:
            symbols: List of stablecoin symbols

        Returns:
            Dict mapping symbol to current price
        """
        coin_ids = []
        symbol_to_id = {}
        for symbol in symbols:
            coin_id = COINGECKO_IDS.get(symbol.upper())
            if coin_id:
                coin_ids.append(coin_id)
                symbol_to_id[coin_id] = symbol.upper()

        if not coin_ids:
            return {}

        url = f"{self.base_url}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd"
        }

        response = self._rate_limited_request(url, params)
        data = response.json()

        prices = {}
        for coin_id, price_data in data.items():
            symbol = symbol_to_id.get(coin_id)
            if symbol and "usd" in price_data:
                prices[symbol] = price_data["usd"]

        return prices

    def get_detailed_coin_data(self, coin_id: str) -> Dict:
        """Get detailed data for a specific coin."""
        url = f"{self.base_url}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "true",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }

        response = self._rate_limited_request(url, params)
        return response.json()

    def calculate_volatility(
        self,
        prices: pd.DataFrame,
        window: int = 30
    ) -> pd.Series:
        """
        Calculate rolling volatility of price deviations.

        Args:
            prices: DataFrame with 'price' column
            window: Rolling window in periods

        Returns:
            Series of rolling volatility values
        """
        deviations = prices["price"] - 1.0
        return deviations.rolling(window=window).std()

    def find_correlation_breaks(
        self,
        price_a: pd.DataFrame,
        price_b: pd.DataFrame,
        window: int = 30,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Find periods where two stablecoins decorrelated.

        Args:
            price_a: First stablecoin price history
            price_b: Second stablecoin price history
            window: Rolling correlation window
            threshold: Correlation threshold for "break"

        Returns:
            List of correlation break events
        """
        # Align the dataframes
        combined = pd.DataFrame({
            "price_a": price_a["price"],
            "price_b": price_b["price"]
        }).dropna()

        # Calculate rolling correlation
        correlation = combined["price_a"].rolling(window).corr(combined["price_b"])

        # Find breaks
        breaks = []
        is_broken = correlation < threshold
        break_groups = (is_broken != is_broken.shift()).cumsum()

        for group_id, group in correlation[is_broken].groupby(break_groups[is_broken]):
            breaks.append({
                "start_date": group.index.min(),
                "end_date": group.index.max(),
                "min_correlation": group.min(),
                "duration_periods": len(group)
            })

        return breaks

    def get_all_stablecoin_prices(self, days: int = 365) -> Dict[str, pd.DataFrame]:
        """
        Get price history for all known stablecoins.

        Args:
            days: Number of days of history

        Returns:
            Dict mapping symbol to price DataFrame
        """
        histories = {}
        for symbol, coin_id in COINGECKO_IDS.items():
            try:
                df = self.get_price_history(coin_id, days)
                histories[symbol] = df
                logger.info(f"Fetched {symbol} price history")
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue

        return histories

    def calculate_peg_stability_score(
        self,
        prices: pd.DataFrame,
        threshold: float = 0.01
    ) -> Dict:
        """
        Calculate a peg stability score for a stablecoin.

        Args:
            prices: DataFrame with 'price' column
            threshold: Deviation threshold for "stable"

        Returns:
            Dict with stability metrics
        """
        deviations = abs(prices["price"] - 1.0)

        return {
            "time_within_peg": (deviations <= threshold).mean(),
            "max_deviation": deviations.max(),
            "avg_deviation": deviations.mean(),
            "std_deviation": deviations.std(),
            "depeg_count": len(self.detect_depeg_events(prices, threshold)),
            "worst_price": prices["price"].min(),
            "periods_analyzed": len(prices)
        }
