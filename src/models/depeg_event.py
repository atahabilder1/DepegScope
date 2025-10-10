"""Historical depeg event model."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum


class DepegCause(Enum):
    """Classification of depeg causes."""
    ALGORITHMIC_FAILURE = "algorithmic_failure"
    BANK_FAILURE = "bank_failure"
    COLLATERAL_CRISIS = "collateral_crisis"
    ORACLE_MANIPULATION = "oracle_manipulation"
    SMART_CONTRACT_EXPLOIT = "smart_contract_exploit"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    REGULATORY_ACTION = "regulatory_action"
    MARKET_PANIC = "market_panic"
    CONTAGION = "contagion"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, cause_str: str) -> "DepegCause":
        """Convert string to DepegCause."""
        cause_lower = cause_str.lower()
        if "algorithm" in cause_lower or "death spiral" in cause_lower:
            return cls.ALGORITHMIC_FAILURE
        elif "bank" in cause_lower or "svb" in cause_lower:
            return cls.BANK_FAILURE
        elif "collateral" in cause_lower:
            return cls.COLLATERAL_CRISIS
        elif "oracle" in cause_lower:
            return cls.ORACLE_MANIPULATION
        elif "exploit" in cause_lower or "hack" in cause_lower:
            return cls.SMART_CONTRACT_EXPLOIT
        elif "liquidity" in cause_lower:
            return cls.LIQUIDITY_CRISIS
        elif "regulat" in cause_lower:
            return cls.REGULATORY_ACTION
        elif "panic" in cause_lower:
            return cls.MARKET_PANIC
        elif "contag" in cause_lower or "cascade" in cause_lower:
            return cls.CONTAGION
        return cls.UNKNOWN


class DepegSeverity(Enum):
    """Severity classification of depeg events."""
    MINOR = "minor"         # < 5% deviation
    MODERATE = "moderate"   # 5-20% deviation
    SEVERE = "severe"       # 20-50% deviation
    CATASTROPHIC = "catastrophic"  # > 50% deviation

    @classmethod
    def from_price(cls, min_price: float) -> "DepegSeverity":
        """Determine severity from minimum price."""
        deviation = abs(1.0 - min_price)
        if deviation < 0.05:
            return cls.MINOR
        elif deviation < 0.20:
            return cls.MODERATE
        elif deviation < 0.50:
            return cls.SEVERE
        return cls.CATASTROPHIC


@dataclass
class CascadeEffect:
    """Represents a cascade effect from a depeg event."""

    affected_entity: str  # Protocol or stablecoin name
    entity_type: str  # "protocol" or "stablecoin"
    impact_description: str
    estimated_loss_usd: float = 0.0
    low_price: Optional[float] = None  # For stablecoins
    recovery_time_days: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affected_entity": self.affected_entity,
            "entity_type": self.entity_type,
            "impact_description": self.impact_description,
            "estimated_loss_usd": self.estimated_loss_usd,
            "low_price": self.low_price,
            "recovery_time_days": self.recovery_time_days
        }


@dataclass
class DepegEvent:
    """Represents a historical stablecoin depeg event."""

    event_id: str
    stablecoin: str
    date: datetime
    low_price: float
    cause: DepegCause

    # Event details
    description: str = ""
    trigger_event: str = ""
    duration_hours: float = 0.0
    recovery_date: Optional[datetime] = None

    # Impact assessment
    total_loss_usd: float = 0.0
    affected_protocols: List[str] = field(default_factory=list)
    cascade_effects: List[CascadeEffect] = field(default_factory=list)

    # For multi-stablecoin events
    related_stablecoins: List[str] = field(default_factory=list)
    is_cascade_trigger: bool = False

    # Price data
    price_history: Dict[str, float] = field(default_factory=dict)  # timestamp -> price

    # Lessons learned
    lessons: List[str] = field(default_factory=list)

    # Metadata
    source: str = ""
    confidence: float = 1.0

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.date, str):
            self.date = datetime.fromisoformat(self.date)
        if isinstance(self.cause, str):
            self.cause = DepegCause.from_string(self.cause)

    @property
    def severity(self) -> DepegSeverity:
        """Get severity classification."""
        return DepegSeverity.from_price(self.low_price)

    @property
    def max_deviation(self) -> float:
        """Maximum deviation from peg."""
        return abs(1.0 - self.low_price)

    @property
    def duration_days(self) -> float:
        """Duration in days."""
        return self.duration_hours / 24.0

    @property
    def recovered(self) -> bool:
        """Check if stablecoin recovered."""
        return self.recovery_date is not None

    def recovery_time_days(self) -> Optional[float]:
        """Calculate recovery time in days."""
        if self.recovery_date:
            delta = self.recovery_date - self.date
            return delta.total_seconds() / 86400
        return None

    def add_cascade_effect(
        self,
        entity: str,
        entity_type: str,
        description: str,
        loss: float = 0,
        low_price: Optional[float] = None
    ):
        """Add a cascade effect to this event."""
        effect = CascadeEffect(
            affected_entity=entity,
            entity_type=entity_type,
            impact_description=description,
            estimated_loss_usd=loss,
            low_price=low_price
        )
        self.cascade_effects.append(effect)

    def total_cascade_losses(self) -> float:
        """Calculate total losses from cascade effects."""
        return sum(e.estimated_loss_usd for e in self.cascade_effects)

    def affected_stablecoins(self) -> List[str]:
        """Get list of all stablecoins affected (including cascades)."""
        stables = [self.stablecoin] + self.related_stablecoins
        for effect in self.cascade_effects:
            if effect.entity_type == "stablecoin":
                stables.append(effect.affected_entity)
        return list(set(stables))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_id": self.event_id,
            "stablecoin": self.stablecoin,
            "date": self.date.isoformat(),
            "low_price": self.low_price,
            "max_deviation": self.max_deviation,
            "severity": self.severity.value,
            "cause": self.cause.value,
            "description": self.description,
            "trigger_event": self.trigger_event,
            "duration_hours": self.duration_hours,
            "recovery_date": self.recovery_date.isoformat() if self.recovery_date else None,
            "total_loss_usd": self.total_loss_usd,
            "affected_protocols": self.affected_protocols,
            "cascade_effects": [e.to_dict() for e in self.cascade_effects],
            "related_stablecoins": self.related_stablecoins,
            "lessons": self.lessons,
            "recovered": self.recovered
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DepegEvent":
        """Create DepegEvent from dictionary."""
        cascade_effects = [
            CascadeEffect(**e) for e in data.get("cascade_effects", [])
        ]

        recovery_date = None
        if data.get("recovery_date"):
            recovery_date = datetime.fromisoformat(data["recovery_date"])

        return cls(
            event_id=data.get("event_id", ""),
            stablecoin=data["stablecoin"],
            date=datetime.fromisoformat(data["date"]) if isinstance(data["date"], str) else data["date"],
            low_price=data["low_price"],
            cause=DepegCause.from_string(data.get("cause", "unknown")),
            description=data.get("description", ""),
            trigger_event=data.get("trigger_event", ""),
            duration_hours=data.get("duration_hours", 0),
            recovery_date=recovery_date,
            total_loss_usd=data.get("total_loss_usd", 0),
            affected_protocols=data.get("affected_protocols", []),
            cascade_effects=cascade_effects,
            related_stablecoins=data.get("related_stablecoins", []),
            lessons=data.get("lessons", [])
        )

    def __repr__(self) -> str:
        return (
            f"DepegEvent({self.stablecoin}, date={self.date.date()}, "
            f"low=${self.low_price:.4f}, severity={self.severity.value})"
        )


# Pre-defined historical events for validation
HISTORICAL_EVENTS = {
    "terra_ust": DepegEvent(
        event_id="terra_ust_2022",
        stablecoin="UST",
        date=datetime(2022, 5, 9),
        low_price=0.006,
        cause=DepegCause.ALGORITHMIC_FAILURE,
        description="Terra UST algorithmic stablecoin death spiral",
        trigger_event="Large UST redemptions triggered LUNA minting spiral",
        duration_hours=168,  # 7 days
        total_loss_usd=60_000_000_000,
        affected_protocols=["Anchor Protocol", "Mirror Protocol", "Lido (stLUNA)"],
        lessons=[
            "Algorithmic stablecoins are vulnerable to death spirals",
            "Over-reliance on single yield source (Anchor 20% APY) created fragility",
            "Reflexive mechanisms amplify downward pressure"
        ],
        is_cascade_trigger=True
    ),

    "usdc_svb": DepegEvent(
        event_id="usdc_svb_2023",
        stablecoin="USDC",
        date=datetime(2023, 3, 11),
        low_price=0.87,
        cause=DepegCause.BANK_FAILURE,
        description="USDC depeg due to SVB collapse with $3.3B reserves frozen",
        trigger_event="Silicon Valley Bank collapse froze Circle reserves",
        duration_hours=72,
        recovery_date=datetime(2023, 3, 14),
        total_loss_usd=0,  # Eventually recovered
        affected_protocols=["MakerDAO", "Frax Finance", "Curve"],
        related_stablecoins=["DAI", "FRAX"],
        lessons=[
            "Fiat-backed stablecoins have banking counterparty risk",
            "Collateral concentration creates contagion (DAI's 60% USDC exposure)",
            "Fast recovery possible with regulatory backstop"
        ],
        is_cascade_trigger=True
    ),

    "susd_2025": DepegEvent(
        event_id="susd_2025",
        stablecoin="sUSD",
        date=datetime(2025, 4, 15),
        low_price=0.68,
        cause=DepegCause.COLLATERAL_CRISIS,
        description="sUSD depeg following SIP-420 collateral changes and SNX decline",
        trigger_event="SIP-420 reduced collateralization requirements during SNX price decline",
        duration_hours=336,  # 14 days
        affected_protocols=["Synthetix", "Curve sUSD pool"],
        lessons=[
            "Collateral ratio changes during volatile periods are risky",
            "Single-asset collateral creates concentration risk"
        ]
    ),

    "nov_2025_cascade": DepegEvent(
        event_id="nov_2025_cascade",
        stablecoin="xUSD",
        date=datetime(2025, 11, 6),
        low_price=0.23,
        cause=DepegCause.CONTAGION,
        description="Cascade depeg of xUSD, deUSD, USDX following Stream platform loss",
        trigger_event="Stream platform $93M asset loss",
        duration_hours=120,
        total_loss_usd=150_000_000,
        related_stablecoins=["deUSD", "USDX"],
        lessons=[
            "Small stablecoins can cascade to each other",
            "Shared collateral creates hidden dependencies",
            "Cross-stablecoin backing amplifies contagion"
        ],
        is_cascade_trigger=True
    )
}


def get_historical_event(event_id: str) -> Optional[DepegEvent]:
    """Get a historical event by ID."""
    return HISTORICAL_EVENTS.get(event_id)


def get_all_historical_events() -> List[DepegEvent]:
    """Get all historical events."""
    return list(HISTORICAL_EVENTS.values())


def get_events_by_cause(cause: DepegCause) -> List[DepegEvent]:
    """Get events filtered by cause."""
    return [e for e in HISTORICAL_EVENTS.values() if e.cause == cause]


def get_cascade_events() -> List[DepegEvent]:
    """Get events that triggered cascades."""
    return [e for e in HISTORICAL_EVENTS.values() if e.is_cascade_trigger]
