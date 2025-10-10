"""Exposure relationship model."""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from enum import Enum
from datetime import datetime


class ExposureType(Enum):
    """Types of exposure relationships."""
    COLLATERAL = "collateral"       # Stablecoin used as collateral
    LIQUIDITY = "liquidity"         # Stablecoin in liquidity pool
    TREASURY = "treasury"           # Held in protocol treasury
    BORROWED = "borrowed"           # Borrowed stablecoin
    BACKING = "backing"             # Backs another stablecoin
    RESERVE = "reserve"             # Held in reserves
    YIELD = "yield"                 # Deployed in yield strategies
    BRIDGE = "bridge"               # Locked in bridge contract

    @classmethod
    def from_string(cls, type_str: str) -> "ExposureType":
        """Convert string to ExposureType."""
        mapping = {
            "collateral": cls.COLLATERAL,
            "liquidity": cls.LIQUIDITY,
            "lp": cls.LIQUIDITY,
            "treasury": cls.TREASURY,
            "borrowed": cls.BORROWED,
            "borrow": cls.BORROWED,
            "backing": cls.BACKING,
            "reserve": cls.RESERVE,
            "reserves": cls.RESERVE,
            "yield": cls.YIELD,
            "farming": cls.YIELD,
            "bridge": cls.BRIDGE,
        }
        return mapping.get(type_str.lower(), cls.LIQUIDITY)


@dataclass
class Exposure:
    """Represents an exposure relationship between protocol and stablecoin."""

    protocol_name: str
    stablecoin_symbol: str
    exposure_type: ExposureType
    amount_usd: float
    percentage_of_tvl: float
    chain: str = "ethereum"

    # For collateral relationships
    collateral_ratio: Optional[float] = None
    liquidation_threshold: Optional[float] = None

    # For pool/liquidity relationships
    pool_address: Optional[str] = None
    pool_share: Optional[float] = None

    # For backing relationships (stablecoin -> stablecoin)
    backing_stablecoin: Optional[str] = None
    backing_percentage: Optional[float] = None

    # Metadata
    source: str = "defillama"  # Data source
    confidence: float = 1.0  # Data confidence score
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.exposure_type, str):
            self.exposure_type = ExposureType.from_string(self.exposure_type)

    def risk_score(self) -> float:
        """
        Calculate risk score for this exposure.

        Returns:
            Risk score between 0 and 1
        """
        base_score = self.percentage_of_tvl

        # Higher risk for collateral exposures (liquidation risk)
        if self.exposure_type == ExposureType.COLLATERAL:
            base_score *= 1.5

        # Higher risk for backing relationships (stablecoin depends on stablecoin)
        if self.exposure_type == ExposureType.BACKING:
            base_score *= 2.0

        # Higher risk for bridge exposures (smart contract risk)
        if self.exposure_type == ExposureType.BRIDGE:
            base_score *= 1.3

        # Lower confidence = higher risk
        base_score *= (2 - self.confidence)

        return min(base_score, 1.0)

    def severity_level(self) -> str:
        """Get severity level of this exposure."""
        score = self.risk_score()
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.50:
            return "HIGH"
        elif score >= 0.25:
            return "MEDIUM"
        return "LOW"

    def is_significant(self, threshold: float = 0.05) -> bool:
        """Check if exposure is significant (above threshold)."""
        return self.percentage_of_tvl >= threshold

    def is_collateral_exposure(self) -> bool:
        """Check if this is a collateral-type exposure."""
        return self.exposure_type in [
            ExposureType.COLLATERAL,
            ExposureType.BACKING
        ]

    def is_liquidity_exposure(self) -> bool:
        """Check if this is a liquidity-type exposure."""
        return self.exposure_type in [
            ExposureType.LIQUIDITY,
            ExposureType.YIELD
        ]

    def cascade_impact(self, depeg_severity: float) -> float:
        """
        Calculate the cascade impact if the stablecoin depegs.

        Args:
            depeg_severity: Severity of depeg (0-1, where 1 = 100% loss)

        Returns:
            Estimated impact in USD
        """
        impact = self.amount_usd * depeg_severity

        # Collateral exposures can cascade (liquidations)
        if self.exposure_type == ExposureType.COLLATERAL:
            if self.liquidation_threshold and depeg_severity > (1 - self.liquidation_threshold):
                impact *= 1.5  # Additional liquidation impact

        return impact

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "protocol_name": self.protocol_name,
            "stablecoin_symbol": self.stablecoin_symbol,
            "exposure_type": self.exposure_type.value,
            "amount_usd": self.amount_usd,
            "percentage_of_tvl": self.percentage_of_tvl,
            "chain": self.chain,
            "collateral_ratio": self.collateral_ratio,
            "liquidation_threshold": self.liquidation_threshold,
            "pool_address": self.pool_address,
            "risk_score": self.risk_score(),
            "severity_level": self.severity_level(),
            "source": self.source,
            "confidence": self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Exposure":
        """Create Exposure from dictionary."""
        return cls(
            protocol_name=data["protocol_name"],
            stablecoin_symbol=data["stablecoin_symbol"],
            exposure_type=ExposureType.from_string(data.get("exposure_type", "liquidity")),
            amount_usd=data.get("amount_usd", 0.0),
            percentage_of_tvl=data.get("percentage_of_tvl", 0.0),
            chain=data.get("chain", "ethereum"),
            collateral_ratio=data.get("collateral_ratio"),
            liquidation_threshold=data.get("liquidation_threshold"),
            pool_address=data.get("pool_address"),
            pool_share=data.get("pool_share"),
            source=data.get("source", "unknown"),
            confidence=data.get("confidence", 1.0)
        )

    def __repr__(self) -> str:
        return (
            f"Exposure({self.protocol_name} -> {self.stablecoin_symbol}, "
            f"type={self.exposure_type.value}, ${self.amount_usd:,.0f})"
        )


@dataclass
class ExposureMatrix:
    """Matrix of protocol-stablecoin exposures."""

    exposures: List[Exposure] = field(default_factory=list)
    protocols: set = field(default_factory=set)
    stablecoins: set = field(default_factory=set)

    def add_exposure(self, exposure: Exposure):
        """Add an exposure to the matrix."""
        self.exposures.append(exposure)
        self.protocols.add(exposure.protocol_name)
        self.stablecoins.add(exposure.stablecoin_symbol)

    def get_protocol_exposures(self, protocol: str) -> List[Exposure]:
        """Get all exposures for a protocol."""
        return [e for e in self.exposures if e.protocol_name == protocol]

    def get_stablecoin_exposures(self, stablecoin: str) -> List[Exposure]:
        """Get all exposures for a stablecoin."""
        return [e for e in self.exposures if e.stablecoin_symbol == stablecoin]

    def get_exposure(self, protocol: str, stablecoin: str) -> Optional[Exposure]:
        """Get specific exposure between protocol and stablecoin."""
        for e in self.exposures:
            if e.protocol_name == protocol and e.stablecoin_symbol == stablecoin:
                return e
        return None

    def total_exposure_to_stablecoin(self, stablecoin: str) -> float:
        """Get total ecosystem exposure to a stablecoin."""
        return sum(
            e.amount_usd for e in self.exposures
            if e.stablecoin_symbol == stablecoin
        )

    def protocols_exposed_to(self, stablecoin: str, min_ratio: float = 0.05) -> List[str]:
        """Get protocols significantly exposed to a stablecoin."""
        return list(set(
            e.protocol_name for e in self.exposures
            if e.stablecoin_symbol == stablecoin and e.percentage_of_tvl >= min_ratio
        ))

    def high_risk_exposures(self, threshold: float = 0.5) -> List[Exposure]:
        """Get exposures with risk score above threshold."""
        return [e for e in self.exposures if e.risk_score() >= threshold]

    def to_dataframe(self):
        """Convert to pandas DataFrame (requires pandas)."""
        import pandas as pd
        return pd.DataFrame([e.to_dict() for e in self.exposures])

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_exposures": len(self.exposures),
            "protocols_count": len(self.protocols),
            "stablecoins_count": len(self.stablecoins),
            "total_exposure_usd": sum(e.amount_usd for e in self.exposures),
            "high_risk_count": len(self.high_risk_exposures()),
            "exposure_types": list(set(e.exposure_type.value for e in self.exposures))
        }
