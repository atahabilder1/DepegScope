"""Risk metrics and scoring for stablecoins and protocols."""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger

from src.analysis.dependency_graph import DependencyGraph


@dataclass
class RiskScore:
    """Composite risk score for a stablecoin or protocol."""

    entity_name: str
    entity_type: str  # "stablecoin" or "protocol"

    # Component scores (0-1, higher = more risky)
    concentration_risk: float = 0.0
    liquidity_risk: float = 0.0
    contagion_risk: float = 0.0
    collateral_risk: float = 0.0
    mechanism_risk: float = 0.0

    # Computed
    @property
    def composite_score(self) -> float:
        """Weighted composite risk score."""
        weights = {
            "concentration": 0.20,
            "liquidity": 0.20,
            "contagion": 0.30,
            "collateral": 0.15,
            "mechanism": 0.15
        }
        return (
            weights["concentration"] * self.concentration_risk +
            weights["liquidity"] * self.liquidity_risk +
            weights["contagion"] * self.contagion_risk +
            weights["collateral"] * self.collateral_risk +
            weights["mechanism"] * self.mechanism_risk
        )

    @property
    def risk_level(self) -> str:
        """Categorical risk level."""
        score = self.composite_score
        if score < 0.25:
            return "LOW"
        elif score < 0.50:
            return "MEDIUM"
        elif score < 0.75:
            return "HIGH"
        else:
            return "CRITICAL"

    @property
    def risk_color(self) -> str:
        """Color code for risk level."""
        level = self.risk_level
        colors = {
            "LOW": "green",
            "MEDIUM": "yellow",
            "HIGH": "orange",
            "CRITICAL": "red"
        }
        return colors.get(level, "gray")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "concentration_risk": self.concentration_risk,
            "liquidity_risk": self.liquidity_risk,
            "contagion_risk": self.contagion_risk,
            "collateral_risk": self.collateral_risk,
            "mechanism_risk": self.mechanism_risk,
            "composite_score": self.composite_score,
            "risk_level": self.risk_level
        }


class RiskCalculator:
    """Calculate various risk metrics for the DeFi ecosystem."""

    # Risk weights for different collateral types
    COLLATERAL_RISK_WEIGHTS = {
        "USDC": 0.1,    # Low risk - fiat-backed
        "USDT": 0.2,    # Medium-low - fiat-backed but less transparent
        "DAI": 0.3,     # Medium - crypto-backed
        "ETH": 0.5,     # Higher - volatile
        "WBTC": 0.5,    # Higher - volatile + wrapped
        "stETH": 0.55,  # Higher - liquid staking derivative
        "wstETH": 0.55,
        "WETH": 0.5,
        "other": 0.6,   # Unknown = higher risk
    }

    # Risk weights for stablecoin mechanisms
    MECHANISM_RISK_WEIGHTS = {
        "fiat-backed": 0.2,
        "crypto-backed": 0.4,
        "algorithmic": 0.8,
        "hybrid": 0.5,
        "unknown": 0.6
    }

    def __init__(self, dependency_graph: DependencyGraph):
        """
        Initialize risk calculator.

        Args:
            dependency_graph: DependencyGraph instance
        """
        self.graph = dependency_graph

    def calculate_concentration_risk(
        self,
        exposures: Dict[str, float]
    ) -> float:
        """
        Calculate Herfindahl-Hirschman Index for exposure concentration.

        Args:
            exposures: Dict mapping entity to USD exposure

        Returns:
            Normalized HHI (0-1, higher = more concentrated)
        """
        total = sum(exposures.values())
        if total == 0:
            return 0.0

        shares = [v / total for v in exposures.values()]
        hhi = sum(s ** 2 for s in shares)

        # Normalize to 0-1 (HHI ranges from 1/n to 1)
        n = len(shares)
        if n <= 1:
            return 1.0

        min_hhi = 1 / n
        normalized = (hhi - min_hhi) / (1 - min_hhi)
        return min(max(normalized, 0), 1)

    def calculate_liquidity_risk(
        self,
        market_cap: float,
        daily_volume: float,
        pool_depth: float
    ) -> float:
        """
        Calculate liquidity risk based on market metrics.

        Args:
            market_cap: Total market capitalization
            daily_volume: 24h trading volume
            pool_depth: Total DEX liquidity depth

        Returns:
            Liquidity risk score (0-1, higher = more risky)
        """
        if market_cap <= 0:
            return 1.0

        # Volume ratio (higher is better)
        volume_ratio = daily_volume / market_cap
        volume_score = 1 - min(volume_ratio * 10, 1)  # Cap at 10% daily volume

        # Pool depth ratio (higher is better)
        depth_ratio = pool_depth / market_cap
        depth_score = 1 - min(depth_ratio * 5, 1)  # Cap at 20% depth

        return (volume_score + depth_score) / 2

    def calculate_contagion_risk(self, stablecoin: str) -> float:
        """
        Calculate contagion risk based on dependency graph.

        Args:
            stablecoin: Stablecoin symbol

        Returns:
            Contagion risk score (0-1, higher = more risky)
        """
        blast = self.graph.calculate_blast_radius(stablecoin)

        # Normalize by total ecosystem TVL
        total_tvl = sum(p.tvl for p in self.graph.protocols.values())
        if total_tvl == 0:
            return 0.0

        tvl_at_risk_ratio = blast["total_tvl_at_risk"] / total_tvl

        # Factor in cascade depth
        depth_factor = min(blast["cascade_depth"] / 5, 1)

        # Factor in stablecoin contagion (extra dangerous)
        stablecoin_factor = 1 + (blast["stablecoins_affected"] * 0.2)

        return min(tvl_at_risk_ratio * depth_factor * stablecoin_factor, 1.0)

    def calculate_collateral_risk(
        self,
        collateral_composition: Dict[str, float]
    ) -> float:
        """
        Calculate collateral risk for crypto-backed stablecoins.

        Args:
            collateral_composition: Dict mapping collateral asset to USD amount

        Returns:
            Collateral risk score (0-1, higher = more risky)
        """
        if not collateral_composition:
            return 0.0  # No collateral = fiat-backed, lower risk

        total = sum(collateral_composition.values())
        if total == 0:
            return 0.5

        weighted_risk = 0
        for asset, amount in collateral_composition.items():
            weight = self.COLLATERAL_RISK_WEIGHTS.get(
                asset.upper(),
                self.COLLATERAL_RISK_WEIGHTS["other"]
            )
            weighted_risk += (amount / total) * weight

        return weighted_risk

    def calculate_mechanism_risk(self, stablecoin_type: str) -> float:
        """
        Calculate risk based on stablecoin mechanism.

        Args:
            stablecoin_type: Type of stablecoin mechanism

        Returns:
            Mechanism risk score (0-1)
        """
        return self.MECHANISM_RISK_WEIGHTS.get(
            stablecoin_type.lower(),
            self.MECHANISM_RISK_WEIGHTS["unknown"]
        )

    def calculate_protocol_risk(
        self,
        protocol_slug: str
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a protocol.

        Args:
            protocol_slug: Protocol identifier

        Returns:
            RiskScore object
        """
        if protocol_slug not in self.graph.protocols:
            return RiskScore(entity_name=protocol_slug, entity_type="protocol")

        protocol = self.graph.protocols[protocol_slug]

        # Concentration risk
        concentration = self.calculate_concentration_risk(
            protocol.stablecoin_holdings
        )

        # Contagion risk (sum of exposure to each stablecoin's contagion risk)
        contagion = 0.0
        for stablecoin, exposure in protocol.stablecoin_holdings.items():
            if protocol.tvl > 0 and stablecoin in self.graph.stablecoins:
                exposure_ratio = exposure / protocol.tvl
                stable_contagion = self.calculate_contagion_risk(stablecoin)
                contagion += exposure_ratio * stable_contagion
        contagion = min(contagion, 1.0)

        return RiskScore(
            entity_name=protocol_slug,
            entity_type="protocol",
            concentration_risk=concentration,
            contagion_risk=contagion,
            liquidity_risk=0.0,  # Would need additional data
            collateral_risk=0.0,
            mechanism_risk=0.0
        )

    def calculate_stablecoin_risk(
        self,
        symbol: str,
        market_cap: Optional[float] = None,
        daily_volume: Optional[float] = None,
        pool_depth: Optional[float] = None
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for a stablecoin.

        Args:
            symbol: Stablecoin symbol
            market_cap: Optional market cap override
            daily_volume: Optional daily volume
            pool_depth: Optional liquidity depth

        Returns:
            RiskScore object
        """
        if symbol not in self.graph.stablecoins:
            return RiskScore(entity_name=symbol, entity_type="stablecoin")

        stablecoin = self.graph.stablecoins[symbol]
        mcap = market_cap or stablecoin.market_cap

        # Concentration risk (in protocol exposures)
        concentration = self.calculate_concentration_risk(
            stablecoin.protocol_exposures
        )

        # Liquidity risk
        liquidity = self.calculate_liquidity_risk(
            mcap,
            daily_volume or mcap * 0.05,  # Default 5% volume
            pool_depth or mcap * 0.1       # Default 10% depth
        )

        # Contagion risk
        contagion = self.calculate_contagion_risk(symbol)

        # Collateral risk
        collateral_comp = {c: 1.0 for c in stablecoin.collateral}  # Simplified
        collateral = self.calculate_collateral_risk(collateral_comp)

        # Mechanism risk
        mechanism = self.calculate_mechanism_risk(stablecoin.stablecoin_type.value)

        return RiskScore(
            entity_name=symbol,
            entity_type="stablecoin",
            concentration_risk=concentration,
            liquidity_risk=liquidity,
            contagion_risk=contagion,
            collateral_risk=collateral,
            mechanism_risk=mechanism
        )

    def generate_risk_report(self) -> pd.DataFrame:
        """
        Generate comprehensive risk report for all stablecoins.

        Returns:
            DataFrame with risk metrics for all stablecoins
        """
        reports = []

        for symbol, stablecoin in self.graph.stablecoins.items():
            score = self.calculate_stablecoin_risk(symbol)

            reports.append({
                "symbol": symbol,
                "type": stablecoin.stablecoin_type.value,
                "market_cap": stablecoin.market_cap,
                "concentration_risk": score.concentration_risk,
                "liquidity_risk": score.liquidity_risk,
                "contagion_risk": score.contagion_risk,
                "collateral_risk": score.collateral_risk,
                "mechanism_risk": score.mechanism_risk,
                "composite_score": score.composite_score,
                "risk_level": score.risk_level
            })

        df = pd.DataFrame(reports)
        return df.sort_values("composite_score", ascending=False)

    def generate_protocol_risk_report(self) -> pd.DataFrame:
        """
        Generate risk report for all protocols.

        Returns:
            DataFrame with risk metrics for all protocols
        """
        reports = []

        for slug, protocol in self.graph.protocols.items():
            score = self.calculate_protocol_risk(slug)

            reports.append({
                "protocol": slug,
                "category": protocol.category.value,
                "tvl": protocol.tvl,
                "stablecoin_exposure": protocol.total_stablecoin_exposure(),
                "concentration_risk": score.concentration_risk,
                "contagion_risk": score.contagion_risk,
                "composite_score": score.composite_score,
                "risk_level": score.risk_level
            })

        df = pd.DataFrame(reports)
        return df.sort_values("composite_score", ascending=False)

    def calculate_ecosystem_risk(self) -> Dict[str, Any]:
        """
        Calculate overall ecosystem risk metrics.

        Returns:
            Ecosystem-wide risk assessment
        """
        stablecoin_scores = [
            self.calculate_stablecoin_risk(s).composite_score
            for s in self.graph.stablecoins
        ]

        protocol_scores = [
            self.calculate_protocol_risk(p).composite_score
            for p in self.graph.protocols
        ]

        # Weighted average by market cap / TVL
        total_mcap = sum(s.market_cap for s in self.graph.stablecoins.values())
        total_tvl = sum(p.tvl for p in self.graph.protocols.values())

        weighted_stable_risk = sum(
            self.calculate_stablecoin_risk(s).composite_score *
            (self.graph.stablecoins[s].market_cap / max(total_mcap, 1))
            for s in self.graph.stablecoins
        )

        weighted_protocol_risk = sum(
            self.calculate_protocol_risk(p).composite_score *
            (self.graph.protocols[p].tvl / max(total_tvl, 1))
            for p in self.graph.protocols
        )

        return {
            "avg_stablecoin_risk": np.mean(stablecoin_scores) if stablecoin_scores else 0,
            "max_stablecoin_risk": max(stablecoin_scores) if stablecoin_scores else 0,
            "weighted_stablecoin_risk": weighted_stable_risk,
            "avg_protocol_risk": np.mean(protocol_scores) if protocol_scores else 0,
            "max_protocol_risk": max(protocol_scores) if protocol_scores else 0,
            "weighted_protocol_risk": weighted_protocol_risk,
            "overall_ecosystem_risk": (weighted_stable_risk + weighted_protocol_risk) / 2,
            "high_risk_stablecoins": [
                s for s in self.graph.stablecoins
                if self.calculate_stablecoin_risk(s).risk_level in ["HIGH", "CRITICAL"]
            ],
            "high_risk_protocols": [
                p for p in self.graph.protocols
                if self.calculate_protocol_risk(p).risk_level in ["HIGH", "CRITICAL"]
            ]
        }

    def calculate_var(
        self,
        confidence_level: float = 0.95,
        n_simulations: int = 1000
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) for the ecosystem.

        Args:
            confidence_level: VaR confidence level
            n_simulations: Number of Monte Carlo simulations

        Returns:
            VaR metrics
        """
        # Simulate potential losses
        losses = []
        total_tvl = sum(p.tvl for p in self.graph.protocols.values())

        for _ in range(n_simulations):
            # Random depeg scenario
            stablecoin = np.random.choice(list(self.graph.stablecoins.keys()))
            severity = np.random.uniform(0.05, 0.3)

            blast = self.graph.calculate_blast_radius(stablecoin, severity)
            losses.append(blast["total_tvl_at_risk"])

        losses = np.array(losses)
        var_value = np.percentile(losses, confidence_level * 100)
        cvar_value = losses[losses >= var_value].mean()

        return {
            "var": var_value,
            "cvar": cvar_value,
            "confidence_level": confidence_level,
            "max_loss": losses.max(),
            "mean_loss": losses.mean(),
            "loss_std": losses.std(),
            "var_as_percent_tvl": var_value / max(total_tvl, 1) * 100
        }
