"""Stablecoin data model."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class StablecoinType(Enum):
    """Classification of stablecoin mechanism types."""
    FIAT_BACKED = "fiat-backed"
    CRYPTO_BACKED = "crypto-backed"
    ALGORITHMIC = "algorithmic"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, type_str: str) -> "StablecoinType":
        """Convert string to StablecoinType."""
        mapping = {
            "fiat-backed": cls.FIAT_BACKED,
            "fiat_backed": cls.FIAT_BACKED,
            "fiat": cls.FIAT_BACKED,
            "crypto-backed": cls.CRYPTO_BACKED,
            "crypto_backed": cls.CRYPTO_BACKED,
            "crypto": cls.CRYPTO_BACKED,
            "algorithmic": cls.ALGORITHMIC,
            "algo": cls.ALGORITHMIC,
            "hybrid": cls.HYBRID,
        }
        return mapping.get(type_str.lower(), cls.UNKNOWN)


@dataclass
class Stablecoin:
    """Represents a stablecoin and its properties."""

    symbol: str
    name: str
    stablecoin_type: StablecoinType
    contract_address: str
    chain: str = "ethereum"
    market_cap: float = 0.0
    current_price: float = 1.0
    coingecko_id: Optional[str] = None
    issuer: Optional[str] = None

    # Collateral information (for crypto-backed stablecoins)
    collateral: List[str] = field(default_factory=list)
    collateral_ratio: float = 1.0

    # Multi-chain presence
    chains: List[str] = field(default_factory=list)
    chain_distribution: Dict[str, float] = field(default_factory=dict)

    # Exposure tracking
    protocol_exposures: Dict[str, float] = field(default_factory=dict)
    pool_exposures: Dict[str, float] = field(default_factory=dict)

    # Risk metrics
    concentration_risk: float = 0.0
    liquidity_depth: float = 0.0
    peg_stability_score: float = 1.0

    # Metadata
    defillama_id: Optional[int] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.stablecoin_type, str):
            self.stablecoin_type = StablecoinType.from_string(self.stablecoin_type)
        if not self.chains and self.chain:
            self.chains = [self.chain]

    @property
    def type(self) -> StablecoinType:
        """Alias for stablecoin_type for backward compatibility."""
        return self.stablecoin_type

    def total_exposure(self) -> float:
        """Calculate total exposure across all protocols."""
        return sum(self.protocol_exposures.values())

    def total_pool_liquidity(self) -> float:
        """Calculate total liquidity in pools."""
        return sum(self.pool_exposures.values())

    def is_depegged(self, threshold: float = 0.02) -> bool:
        """Check if stablecoin is currently depegged."""
        return abs(self.current_price - 1.0) > threshold

    def depeg_severity(self) -> float:
        """Calculate severity of current depeg (0 = pegged)."""
        return abs(self.current_price - 1.0)

    def depeg_direction(self) -> str:
        """Get direction of depeg."""
        if self.current_price < 0.99:
            return "below"
        elif self.current_price > 1.01:
            return "above"
        return "pegged"

    def top_exposures(self, n: int = 10) -> List[tuple]:
        """Get top N protocol exposures."""
        sorted_exposures = sorted(
            self.protocol_exposures.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_exposures[:n]

    def top_pools(self, n: int = 10) -> List[tuple]:
        """Get top N pool exposures."""
        sorted_pools = sorted(
            self.pool_exposures.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_pools[:n]

    def exposure_to_protocol(self, protocol: str) -> float:
        """Get exposure to a specific protocol."""
        return self.protocol_exposures.get(protocol, 0.0)

    def concentration_hhi(self) -> float:
        """Calculate Herfindahl-Hirschman Index for protocol concentration."""
        total = self.total_exposure()
        if total == 0:
            return 0.0
        shares = [v / total for v in self.protocol_exposures.values()]
        return sum(s ** 2 for s in shares)

    def is_crypto_backed(self) -> bool:
        """Check if this is a crypto-backed stablecoin."""
        return self.stablecoin_type in [
            StablecoinType.CRYPTO_BACKED,
            StablecoinType.HYBRID
        ]

    def has_stablecoin_collateral(self, stablecoins: List[str]) -> bool:
        """Check if this stablecoin uses other stablecoins as collateral."""
        return bool(set(self.collateral) & set(stablecoins))

    def risk_factors(self) -> List[str]:
        """Get list of risk factors based on stablecoin type."""
        factors = []

        if self.stablecoin_type == StablecoinType.FIAT_BACKED:
            factors.extend([
                "Banking counterparty risk",
                "Regulatory risk",
                "Reserve transparency"
            ])
        elif self.stablecoin_type == StablecoinType.CRYPTO_BACKED:
            factors.extend([
                "Collateral volatility",
                "Liquidation cascade risk",
                "Oracle manipulation risk"
            ])
        elif self.stablecoin_type == StablecoinType.ALGORITHMIC:
            factors.extend([
                "Death spiral risk",
                "Confidence dependency",
                "Mechanism failure risk"
            ])
        elif self.stablecoin_type == StablecoinType.HYBRID:
            factors.extend([
                "Combined mechanism risks",
                "Complexity risk",
                "Collateral + algorithmic risks"
            ])

        # Add concentration risk if applicable
        if self.concentration_hhi() > 0.25:
            factors.append("High protocol concentration")

        # Add liquidity risk
        if self.liquidity_depth < self.market_cap * 0.05:
            factors.append("Low liquidity depth")

        return factors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "type": self.stablecoin_type.value,
            "contract_address": self.contract_address,
            "chain": self.chain,
            "market_cap": self.market_cap,
            "current_price": self.current_price,
            "coingecko_id": self.coingecko_id,
            "issuer": self.issuer,
            "collateral": self.collateral,
            "collateral_ratio": self.collateral_ratio,
            "chains": self.chains,
            "total_exposure": self.total_exposure(),
            "is_depegged": self.is_depegged(),
            "risk_factors": self.risk_factors()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stablecoin":
        """Create Stablecoin from dictionary."""
        return cls(
            symbol=data["symbol"],
            name=data.get("name", data["symbol"]),
            stablecoin_type=StablecoinType.from_string(data.get("type", "unknown")),
            contract_address=data.get("contract_address", ""),
            chain=data.get("chain", "ethereum"),
            market_cap=data.get("market_cap", 0.0),
            current_price=data.get("current_price", 1.0),
            coingecko_id=data.get("coingecko_id"),
            issuer=data.get("issuer"),
            collateral=data.get("collateral", []),
            collateral_ratio=data.get("collateral_ratio", 1.0),
            chains=data.get("chains", []),
        )

    def __repr__(self) -> str:
        return f"Stablecoin({self.symbol}, type={self.stablecoin_type.value}, mcap=${self.market_cap:,.0f})"

    def __hash__(self) -> int:
        return hash(self.symbol)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Stablecoin):
            return self.symbol == other.symbol
        return False
