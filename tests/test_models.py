"""Tests for data models."""

import pytest
from datetime import datetime

from src.models.stablecoin import Stablecoin, StablecoinType
from src.models.protocol import Protocol, ProtocolCategory
from src.models.exposure import Exposure, ExposureType
from src.models.depeg_event import DepegEvent, HISTORICAL_EVENTS


class TestStablecoin:
    """Tests for Stablecoin model."""

    def test_stablecoin_creation(self):
        """Test basic stablecoin creation."""
        stablecoin = Stablecoin(
            symbol="USDC",
            name="USD Coin",
            stablecoin_type=StablecoinType.FIAT_BACKED,
            market_cap=25_000_000_000
        )

        assert stablecoin.symbol == "USDC"
        assert stablecoin.name == "USD Coin"
        assert stablecoin.stablecoin_type == StablecoinType.FIAT_BACKED
        assert stablecoin.market_cap == 25_000_000_000

    def test_is_algorithmic_property(self):
        """Test is_algorithmic property for different types."""
        fiat = Stablecoin(
            symbol="USDC",
            name="USD Coin",
            stablecoin_type=StablecoinType.FIAT_BACKED
        )
        assert fiat.is_algorithmic is False

        algo = Stablecoin(
            symbol="UST",
            name="TerraUSD",
            stablecoin_type=StablecoinType.ALGORITHMIC
        )
        assert algo.is_algorithmic is True

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = Stablecoin(
            symbol="USDC",
            name="USD Coin",
            stablecoin_type=StablecoinType.FIAT_BACKED,
            market_cap=25_000_000_000,
            peg_currency="USD",
            peg_value=1.0
        )

        data = original.to_dict()
        restored = Stablecoin.from_dict(data)

        assert restored.symbol == original.symbol
        assert restored.name == original.name
        assert restored.market_cap == original.market_cap

    def test_add_exposure(self):
        """Test adding protocol exposure."""
        stablecoin = Stablecoin(symbol="USDC", name="USD Coin")
        stablecoin.add_exposure("aave", 1_000_000_000)
        stablecoin.add_exposure("curve", 500_000_000)

        assert stablecoin.total_exposure == 1_500_000_000

    def test_stablecoin_type_enum(self):
        """Test all stablecoin types exist."""
        assert StablecoinType.FIAT_BACKED.value == "fiat_backed"
        assert StablecoinType.CRYPTO_BACKED.value == "crypto_backed"
        assert StablecoinType.ALGORITHMIC.value == "algorithmic"
        assert StablecoinType.HYBRID.value == "hybrid"
        assert StablecoinType.UNKNOWN.value == "unknown"


class TestProtocol:
    """Tests for Protocol model."""

    def test_protocol_creation(self):
        """Test basic protocol creation."""
        protocol = Protocol(
            name="Aave",
            slug="aave",
            category=ProtocolCategory.LENDING,
            tvl=10_000_000_000
        )

        assert protocol.name == "Aave"
        assert protocol.slug == "aave"
        assert protocol.category == ProtocolCategory.LENDING
        assert protocol.tvl == 10_000_000_000

    def test_stablecoin_exposure_calculation(self):
        """Test stablecoin exposure properties."""
        protocol = Protocol(
            name="Aave",
            slug="aave",
            category=ProtocolCategory.LENDING,
            tvl=10_000_000_000,
            stablecoin_holdings={"USDC": 3_000_000_000, "DAI": 2_000_000_000}
        )

        assert protocol.total_stablecoin_exposure == 5_000_000_000
        assert protocol.stablecoin_ratio == 0.5
        assert protocol.dominant_stablecoin == "USDC"

    def test_get_exposure_to(self):
        """Test getting exposure to specific stablecoin."""
        protocol = Protocol(
            name="Aave",
            stablecoin_holdings={"USDC": 3_000_000_000, "DAI": 2_000_000_000}
        )

        assert protocol.get_exposure_to("USDC") == 3_000_000_000
        assert protocol.get_exposure_to("DAI") == 2_000_000_000
        assert protocol.get_exposure_to("USDT") == 0

    def test_calculate_risk_from_depeg(self):
        """Test depeg risk calculation."""
        protocol = Protocol(
            name="Aave",
            tvl=10_000_000_000,
            stablecoin_holdings={"USDC": 5_000_000_000}
        )

        # 50% exposure, 10% depeg = 5% TVL loss
        risk = protocol.calculate_risk_from_depeg("USDC", severity=0.10)
        assert risk == 500_000_000  # 10% of 5B exposure

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = Protocol(
            name="Aave",
            slug="aave",
            category=ProtocolCategory.LENDING,
            tvl=10_000_000_000,
            chains=["ethereum", "polygon"]
        )

        data = original.to_dict()
        restored = Protocol.from_dict(data)

        assert restored.name == original.name
        assert restored.slug == original.slug
        assert restored.tvl == original.tvl


class TestExposure:
    """Tests for Exposure model."""

    def test_exposure_creation(self):
        """Test basic exposure creation."""
        exposure = Exposure(
            protocol_name="aave",
            stablecoin_symbol="USDC",
            exposure_type=ExposureType.COLLATERAL,
            amount_usd=3_000_000_000,
            percentage_of_tvl=0.30
        )

        assert exposure.protocol_name == "aave"
        assert exposure.stablecoin_symbol == "USDC"
        assert exposure.exposure_type == ExposureType.COLLATERAL
        assert exposure.amount_usd == 3_000_000_000
        assert exposure.percentage_of_tvl == 0.30

    def test_exposure_types(self):
        """Test all exposure types exist."""
        assert ExposureType.COLLATERAL.value == "collateral"
        assert ExposureType.LIQUIDITY.value == "liquidity"
        assert ExposureType.BACKING.value == "backing"
        assert ExposureType.LENDING.value == "lending"
        assert ExposureType.BORROWING.value == "borrowing"

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        original = Exposure(
            protocol_name="aave",
            stablecoin_symbol="USDC",
            exposure_type=ExposureType.COLLATERAL,
            amount_usd=3_000_000_000,
            percentage_of_tvl=0.30,
            chain="ethereum",
            source="defillama"
        )

        data = original.to_dict()
        restored = Exposure.from_dict(data)

        assert restored.protocol_name == original.protocol_name
        assert restored.stablecoin_symbol == original.stablecoin_symbol
        assert restored.amount_usd == original.amount_usd


class TestDepegEvent:
    """Tests for DepegEvent model."""

    def test_depeg_event_creation(self):
        """Test basic depeg event creation."""
        event = DepegEvent(
            stablecoin="UST",
            start_date=datetime(2022, 5, 9),
            end_date=datetime(2022, 5, 13),
            min_price=0.01,
            max_deviation=0.99,
            trigger="Algorithm failure",
            recovery=False
        )

        assert event.stablecoin == "UST"
        assert event.min_price == 0.01
        assert event.max_deviation == 0.99
        assert event.recovery is False

    def test_historical_events_exist(self):
        """Test that predefined historical events are available."""
        assert "ust_collapse" in HISTORICAL_EVENTS
        assert "usdc_svb" in HISTORICAL_EVENTS

        ust = HISTORICAL_EVENTS["ust_collapse"]
        assert ust.stablecoin == "UST"
        assert ust.tvl_impact > 0

    def test_event_duration(self):
        """Test event duration calculation."""
        event = DepegEvent(
            stablecoin="TEST",
            start_date=datetime(2022, 1, 1),
            end_date=datetime(2022, 1, 3),
            min_price=0.95,
            max_deviation=0.05
        )

        duration = (event.end_date - event.start_date).days
        assert duration == 2
