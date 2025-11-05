"""Early warning indicators for stablecoin depegs."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class WarningSignal:
    """Represents a single warning signal."""

    indicator: str
    value: float
    threshold: float
    warning: bool
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "value": self.value,
            "threshold": self.threshold,
            "warning": self.warning,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details
        }


class EarlyWarningSystem:
    """Detect early warning signals for stablecoin depegs."""

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize early warning system.

        Args:
            thresholds: Custom warning thresholds
        """
        self.thresholds = thresholds or {
            "price_deviation": 0.005,      # 0.5% from peg
            "price_deviation_high": 0.02,  # 2% from peg (high severity)
            "volume_spike": 2.0,           # 2x normal volume
            "volume_spike_high": 5.0,      # 5x normal volume
            "pool_imbalance": 0.40,        # 40% imbalance in Curve pools
            "pool_imbalance_high": 0.60,   # 60% imbalance
            "redemption_spike": 3.0,       # 3x normal redemptions
            "liquidity_drop": 0.20,        # 20% liquidity decrease
            "liquidity_drop_high": 0.40,   # 40% decrease
            "volatility_spike": 2.0,       # 2x normal volatility
            "correlation_break": 0.5,      # Correlation drops below 0.5
        }
        self.history: List[Dict] = []

    def check_price_deviation(
        self,
        prices: pd.Series,
        peg_price: float = 1.0
    ) -> WarningSignal:
        """
        Check for sustained price deviation from peg.

        Args:
            prices: Series of historical prices
            peg_price: Target peg price

        Returns:
            WarningSignal with deviation analysis
        """
        if len(prices) == 0:
            return WarningSignal(
                indicator="price_deviation",
                value=0,
                threshold=self.thresholds["price_deviation"],
                warning=False,
                severity="LOW"
            )

        current_price = prices.iloc[-1]
        deviation = abs(current_price - peg_price)

        # Calculate trend
        trend = 0.0
        if len(prices) >= 24:
            recent_avg = prices.iloc[-24:].mean()
            prior_avg = prices.iloc[-48:-24].mean() if len(prices) >= 48 else prices.mean()
            trend = recent_avg - prior_avg

        # Determine severity
        if deviation > self.thresholds.get("price_deviation_high", 0.02):
            severity = "CRITICAL" if deviation > 0.05 else "HIGH"
        elif deviation > self.thresholds["price_deviation"]:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        warning = deviation > self.thresholds["price_deviation"]

        return WarningSignal(
            indicator="price_deviation",
            value=deviation,
            threshold=self.thresholds["price_deviation"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "current_price": current_price,
                "trend_24h": trend,
                "deviation_direction": "below" if current_price < peg_price else "above"
            }
        )

    def check_volume_spike(
        self,
        current_volume: float,
        historical_avg: float
    ) -> WarningSignal:
        """
        Check for abnormal trading volume.

        Args:
            current_volume: Current period volume
            historical_avg: Historical average volume

        Returns:
            WarningSignal with volume analysis
        """
        if historical_avg == 0:
            ratio = 0
        else:
            ratio = current_volume / historical_avg

        # Determine severity
        if ratio > self.thresholds.get("volume_spike_high", 5.0):
            severity = "CRITICAL"
        elif ratio > self.thresholds["volume_spike"]:
            severity = "HIGH" if ratio > 3.0 else "MEDIUM"
        else:
            severity = "LOW"

        warning = ratio > self.thresholds["volume_spike"]

        return WarningSignal(
            indicator="volume_spike",
            value=ratio,
            threshold=self.thresholds["volume_spike"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "current_volume": current_volume,
                "historical_avg": historical_avg,
                "volume_multiple": ratio
            }
        )

    def check_curve_pool_imbalance(
        self,
        pool_composition: Dict[str, float]
    ) -> WarningSignal:
        """
        Check Curve pool imbalance (major depeg indicator).

        Args:
            pool_composition: Dict mapping token to balance

        Returns:
            WarningSignal with imbalance analysis
        """
        total = sum(pool_composition.values())
        if total == 0 or len(pool_composition) == 0:
            return WarningSignal(
                indicator="pool_imbalance",
                value=0,
                threshold=self.thresholds["pool_imbalance"],
                warning=False,
                severity="LOW"
            )

        # Calculate expected equal share
        shares = [v / total for v in pool_composition.values()]
        expected_share = 1 / len(shares)

        # Maximum deviation from equal share
        max_deviation = max(abs(s - expected_share) for s in shares)

        # Find the imbalanced token
        imbalanced_token = None
        for token, balance in pool_composition.items():
            share = balance / total
            if abs(share - expected_share) == max_deviation:
                imbalanced_token = token
                break

        # Determine severity
        if max_deviation > self.thresholds.get("pool_imbalance_high", 0.60):
            severity = "CRITICAL"
        elif max_deviation > self.thresholds["pool_imbalance"]:
            severity = "HIGH"
        elif max_deviation > 0.25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        warning = max_deviation > self.thresholds["pool_imbalance"]

        return WarningSignal(
            indicator="pool_imbalance",
            value=max_deviation,
            threshold=self.thresholds["pool_imbalance"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "composition": pool_composition,
                "shares": dict(zip(pool_composition.keys(), shares)),
                "imbalanced_token": imbalanced_token,
                "expected_share": expected_share
            }
        )

    def check_liquidity_drop(
        self,
        current_liquidity: float,
        previous_liquidity: float
    ) -> WarningSignal:
        """
        Check for sudden liquidity withdrawals.

        Args:
            current_liquidity: Current liquidity amount
            previous_liquidity: Previous period liquidity

        Returns:
            WarningSignal with liquidity analysis
        """
        if previous_liquidity == 0:
            change = 0
        else:
            change = (previous_liquidity - current_liquidity) / previous_liquidity

        # Determine severity
        if change > self.thresholds.get("liquidity_drop_high", 0.40):
            severity = "CRITICAL"
        elif change > self.thresholds["liquidity_drop"]:
            severity = "HIGH"
        elif change > 0.10:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        warning = change > self.thresholds["liquidity_drop"]

        return WarningSignal(
            indicator="liquidity_drop",
            value=change,
            threshold=self.thresholds["liquidity_drop"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "current_liquidity": current_liquidity,
                "previous_liquidity": previous_liquidity,
                "absolute_change": previous_liquidity - current_liquidity,
                "is_increase": change < 0
            }
        )

    def check_volatility_spike(
        self,
        prices: pd.Series,
        lookback: int = 24,
        baseline_lookback: int = 168  # 1 week in hours
    ) -> WarningSignal:
        """
        Check for volatility spike in price movements.

        Args:
            prices: Price series
            lookback: Recent period for current volatility
            baseline_lookback: Period for baseline volatility

        Returns:
            WarningSignal with volatility analysis
        """
        if len(prices) < lookback:
            return WarningSignal(
                indicator="volatility_spike",
                value=0,
                threshold=self.thresholds["volatility_spike"],
                warning=False,
                severity="LOW"
            )

        # Calculate returns
        returns = prices.pct_change().dropna()

        # Current volatility (recent period)
        current_vol = returns.iloc[-lookback:].std() if len(returns) >= lookback else returns.std()

        # Baseline volatility
        if len(returns) >= baseline_lookback:
            baseline_vol = returns.iloc[-baseline_lookback:-lookback].std()
        else:
            baseline_vol = returns.std()

        # Volatility ratio
        if baseline_vol > 0:
            vol_ratio = current_vol / baseline_vol
        else:
            vol_ratio = 1.0

        # Determine severity
        if vol_ratio > 4.0:
            severity = "CRITICAL"
        elif vol_ratio > self.thresholds["volatility_spike"]:
            severity = "HIGH" if vol_ratio > 3.0 else "MEDIUM"
        else:
            severity = "LOW"

        warning = vol_ratio > self.thresholds["volatility_spike"]

        return WarningSignal(
            indicator="volatility_spike",
            value=vol_ratio,
            threshold=self.thresholds["volatility_spike"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "current_volatility": current_vol,
                "baseline_volatility": baseline_vol,
                "volatility_ratio": vol_ratio
            }
        )

    def check_correlation_break(
        self,
        prices_a: pd.Series,
        prices_b: pd.Series,
        window: int = 24
    ) -> WarningSignal:
        """
        Check for correlation break between two stablecoins.

        Args:
            prices_a: First stablecoin prices
            prices_b: Second stablecoin prices
            window: Rolling window for correlation

        Returns:
            WarningSignal with correlation analysis
        """
        if len(prices_a) < window or len(prices_b) < window:
            return WarningSignal(
                indicator="correlation_break",
                value=1.0,
                threshold=self.thresholds["correlation_break"],
                warning=False,
                severity="LOW"
            )

        # Align series
        combined = pd.DataFrame({
            "a": prices_a,
            "b": prices_b
        }).dropna()

        if len(combined) < window:
            return WarningSignal(
                indicator="correlation_break",
                value=1.0,
                threshold=self.thresholds["correlation_break"],
                warning=False,
                severity="LOW"
            )

        # Calculate rolling correlation
        correlation = combined["a"].rolling(window).corr(combined["b"]).iloc[-1]

        # Determine severity
        if correlation < 0.3:
            severity = "CRITICAL"
        elif correlation < self.thresholds["correlation_break"]:
            severity = "HIGH"
        elif correlation < 0.7:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        warning = correlation < self.thresholds["correlation_break"]

        return WarningSignal(
            indicator="correlation_break",
            value=correlation,
            threshold=self.thresholds["correlation_break"],
            warning=warning,
            severity=severity,
            timestamp=datetime.utcnow(),
            details={
                "current_correlation": correlation,
                "window": window
            }
        )

    def aggregate_warnings(
        self,
        signals: List[WarningSignal]
    ) -> Dict[str, Any]:
        """
        Aggregate multiple warning signals into overall risk assessment.

        Args:
            signals: List of WarningSignal objects

        Returns:
            Aggregated risk assessment
        """
        warnings = [s for s in signals if s.warning]

        severity_scores = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        max_severity = max(
            (severity_scores.get(s.severity, 0) for s in signals),
            default=0
        )

        severity_labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}

        # Calculate aggregate score
        aggregate_score = sum(severity_scores[s.severity] for s in signals) / max(len(signals), 1)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_warnings": len(warnings),
            "warning_indicators": [w.indicator for w in warnings],
            "overall_severity": severity_labels[max_severity],
            "aggregate_score": aggregate_score,
            "recommendation": self._get_recommendation(len(warnings), max_severity),
            "signals": [s.to_dict() for s in signals]
        }

    def _get_recommendation(self, warning_count: int, severity: int) -> str:
        """Generate recommendation based on warnings."""
        if severity >= 3:
            return "CRITICAL: Immediate action required. Consider reducing exposure."
        elif severity >= 2 or warning_count >= 3:
            return "HIGH ALERT: Close monitoring required. Prepare contingency plans."
        elif severity >= 1 or warning_count >= 2:
            return "ELEVATED: Increased monitoring recommended."
        else:
            return "NORMAL: No immediate concerns."

    def run_full_check(
        self,
        stablecoin: str,
        price_history: pd.Series,
        current_volume: float,
        avg_volume: float,
        pool_composition: Dict[str, float],
        current_liquidity: float,
        previous_liquidity: float
    ) -> Dict[str, Any]:
        """
        Run all early warning checks for a stablecoin.

        Args:
            stablecoin: Stablecoin symbol
            price_history: Historical price series
            current_volume: Current trading volume
            avg_volume: Average historical volume
            pool_composition: DEX pool composition
            current_liquidity: Current liquidity
            previous_liquidity: Previous period liquidity

        Returns:
            Comprehensive warning assessment
        """
        signals = [
            self.check_price_deviation(price_history),
            self.check_volume_spike(current_volume, avg_volume),
            self.check_curve_pool_imbalance(pool_composition),
            self.check_liquidity_drop(current_liquidity, previous_liquidity),
            self.check_volatility_spike(price_history),
        ]

        result = self.aggregate_warnings(signals)
        result["stablecoin"] = stablecoin

        # Store in history
        self.history.append(result)

        return result

    def get_alert_history(
        self,
        stablecoin: Optional[str] = None,
        min_severity: str = "MEDIUM"
    ) -> List[Dict]:
        """
        Get historical alerts.

        Args:
            stablecoin: Filter by stablecoin (optional)
            min_severity: Minimum severity to include

        Returns:
            Filtered alert history
        """
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        min_level = severity_order.get(min_severity, 1)

        filtered = []
        for alert in self.history:
            if stablecoin and alert.get("stablecoin") != stablecoin:
                continue
            if severity_order.get(alert.get("overall_severity"), 0) >= min_level:
                filtered.append(alert)

        return filtered
