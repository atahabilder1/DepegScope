"""DeFi Protocol data model."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ProtocolCategory(Enum):
    """Classification of DeFi protocol types."""
    LENDING = "lending"
    DEX = "dex"
    YIELD = "yield"
    BRIDGE = "bridge"
    CDP = "cdp"
    DERIVATIVES = "derivatives"
    LIQUID_STAKING = "liquid_staking"
    STABLECOIN = "stablecoin"
    INSURANCE = "insurance"
    OPTIONS = "options"
    SYNTHETICS = "synthetics"
    OTHER = "other"

    @classmethod
    def from_string(cls, category_str: str) -> "ProtocolCategory":
        """Convert string to ProtocolCategory."""
        mapping = {
            "lending": cls.LENDING,
            "lend": cls.LENDING,
            "dex": cls.DEX,
            "dexes": cls.DEX,
            "exchange": cls.DEX,
            "yield": cls.YIELD,
            "yield aggregator": cls.YIELD,
            "farm": cls.YIELD,
            "bridge": cls.BRIDGE,
            "cross chain": cls.BRIDGE,
            "cdp": cls.CDP,
            "collateralized debt": cls.CDP,
            "derivatives": cls.DERIVATIVES,
            "perps": cls.DERIVATIVES,
            "liquid staking": cls.LIQUID_STAKING,
            "staking": cls.LIQUID_STAKING,
            "stablecoin": cls.STABLECOIN,
            "insurance": cls.INSURANCE,
            "options": cls.OPTIONS,
            "synthetics": cls.SYNTHETICS,
        }
        return mapping.get(category_str.lower(), cls.OTHER)


@dataclass
class Protocol:
    """Represents a DeFi protocol and its stablecoin exposure."""

    name: str
    slug: str
    category: ProtocolCategory
    chain: str = "ethereum"
    tvl: float = 0.0

    # Multi-chain presence
    chains: List[str] = field(default_factory=list)
    chain_tvls: Dict[str, float] = field(default_factory=dict)

    # Stablecoin holdings
    stablecoin_holdings: Dict[str, float] = field(default_factory=dict)

    # Protocol dependencies
    collateral_from: List[str] = field(default_factory=list)  # Stablecoins used as collateral
    borrows_from: List[str] = field(default_factory=list)     # Protocols borrowed from
    lends_to: List[str] = field(default_factory=list)         # Protocols lent to
    depends_on: List[str] = field(default_factory=list)       # General dependencies

    # Risk metrics
    stablecoin_concentration: float = 0.0  # % of TVL in stablecoins
    largest_stablecoin_exposure: str = ""
    risk_score: float = 0.0

    # Metadata
    defillama_slug: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    logo: Optional[str] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.category, str):
            self.category = ProtocolCategory.from_string(self.category)
        if not self.chains and self.chain:
            self.chains = [self.chain]
        self._update_derived_fields()

    def _update_derived_fields(self):
        """Update derived fields based on current data."""
        if self.stablecoin_holdings:
            # Find largest exposure
            if self.stablecoin_holdings:
                self.largest_stablecoin_exposure = max(
                    self.stablecoin_holdings,
                    key=self.stablecoin_holdings.get
                )

            # Calculate stablecoin concentration
            if self.tvl > 0:
                self.stablecoin_concentration = (
                    self.total_stablecoin_exposure() / self.tvl
                )

    def total_stablecoin_exposure(self) -> float:
        """Total USD value in stablecoins."""
        return sum(self.stablecoin_holdings.values())

    def stablecoin_ratio(self) -> float:
        """Ratio of stablecoin TVL to total TVL."""
        if self.tvl == 0:
            return 0.0
        return self.total_stablecoin_exposure() / self.tvl

    def exposure_to(self, stablecoin: str) -> float:
        """Get exposure to a specific stablecoin."""
        return self.stablecoin_holdings.get(stablecoin, 0.0)

    def exposure_ratio_to(self, stablecoin: str) -> float:
        """Get exposure ratio to a specific stablecoin."""
        if self.tvl == 0:
            return 0.0
        return self.exposure_to(stablecoin) / self.tvl

    def would_cascade(
        self,
        depegged_stablecoin: str,
        threshold: float = 0.10
    ) -> bool:
        """Check if this protocol would be affected by a stablecoin depeg."""
        exposure_ratio = self.exposure_ratio_to(depegged_stablecoin)
        return exposure_ratio >= threshold

    def cascade_severity(self, depegged_stablecoin: str, depeg_amount: float) -> float:
        """
        Calculate the severity of cascade impact.

        Args:
            depegged_stablecoin: Symbol of depegging stablecoin
            depeg_amount: Amount of depeg (e.g., 0.1 for 10% drop)

        Returns:
            Estimated TVL loss in USD
        """
        exposure = self.exposure_to(depegged_stablecoin)
        return exposure * depeg_amount

    def top_stablecoin_exposures(self, n: int = 5) -> List[tuple]:
        """Get top N stablecoin exposures."""
        sorted_exposures = sorted(
            self.stablecoin_holdings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_exposures[:n]

    def uses_stablecoin_as_collateral(self, stablecoin: str) -> bool:
        """Check if protocol uses a stablecoin as collateral."""
        return stablecoin.upper() in [c.upper() for c in self.collateral_from]

    def exposure_hhi(self) -> float:
        """Calculate Herfindahl-Hirschman Index for stablecoin concentration."""
        total = self.total_stablecoin_exposure()
        if total == 0:
            return 0.0
        shares = [v / total for v in self.stablecoin_holdings.values()]
        return sum(s ** 2 for s in shares)

    def is_lending_protocol(self) -> bool:
        """Check if this is a lending protocol."""
        return self.category == ProtocolCategory.LENDING

    def is_dex(self) -> bool:
        """Check if this is a DEX."""
        return self.category == ProtocolCategory.DEX

    def is_bridge(self) -> bool:
        """Check if this is a bridge."""
        return self.category == ProtocolCategory.BRIDGE

    def dependency_count(self) -> int:
        """Count total dependencies."""
        return (
            len(self.collateral_from) +
            len(self.borrows_from) +
            len(self.lends_to) +
            len(self.depends_on)
        )

    def add_stablecoin_exposure(self, stablecoin: str, amount: float):
        """Add or update stablecoin exposure."""
        if stablecoin in self.stablecoin_holdings:
            self.stablecoin_holdings[stablecoin] += amount
        else:
            self.stablecoin_holdings[stablecoin] = amount
        self._update_derived_fields()

    def risk_factors(self) -> List[str]:
        """Get list of risk factors for this protocol."""
        factors = []

        # High stablecoin concentration
        if self.stablecoin_ratio() > 0.5:
            factors.append("High stablecoin concentration")

        # Single stablecoin dependency
        if self.exposure_hhi() > 0.5:
            factors.append("Single stablecoin dependency")

        # Bridge-specific risks
        if self.is_bridge():
            factors.append("Cross-chain bridge risk")

        # Lending-specific risks
        if self.is_lending_protocol():
            factors.append("Liquidation cascade risk")

        # Multi-chain complexity
        if len(self.chains) > 3:
            factors.append("Multi-chain complexity")

        return factors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "slug": self.slug,
            "category": self.category.value,
            "chain": self.chain,
            "chains": self.chains,
            "tvl": self.tvl,
            "stablecoin_holdings": self.stablecoin_holdings,
            "total_stablecoin_exposure": self.total_stablecoin_exposure(),
            "stablecoin_ratio": self.stablecoin_ratio(),
            "largest_stablecoin_exposure": self.largest_stablecoin_exposure,
            "collateral_from": self.collateral_from,
            "risk_factors": self.risk_factors()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Protocol":
        """Create Protocol from dictionary."""
        return cls(
            name=data.get("name", data.get("slug", "")),
            slug=data.get("slug", ""),
            category=ProtocolCategory.from_string(data.get("category", "other")),
            chain=data.get("chain", "ethereum"),
            chains=data.get("chains", []),
            tvl=data.get("tvl", 0.0),
            stablecoin_holdings=data.get("stablecoin_holdings", {}),
            collateral_from=data.get("collateral_from", []),
            borrows_from=data.get("borrows_from", []),
            lends_to=data.get("lends_to", []),
        )

    @classmethod
    def from_defillama(cls, data: Dict[str, Any]) -> "Protocol":
        """Create Protocol from DeFiLlama API response."""
        return cls(
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            category=ProtocolCategory.from_string(data.get("category", "other")),
            chain=data.get("chain", "ethereum"),
            chains=data.get("chains", []),
            tvl=data.get("tvl", 0) or 0,
            defillama_slug=data.get("slug"),
            website=data.get("url"),
            twitter=data.get("twitter"),
            logo=data.get("logo"),
        )

    def __repr__(self) -> str:
        return f"Protocol({self.name}, category={self.category.value}, tvl=${self.tvl:,.0f})"

    def __hash__(self) -> int:
        return hash(self.slug)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Protocol):
            return self.slug == other.slug
        return False
