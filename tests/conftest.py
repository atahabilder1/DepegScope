"""Shared pytest fixtures for DepegScope tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.stablecoin import Stablecoin, StablecoinType
from src.models.protocol import Protocol, ProtocolCategory
from src.models.exposure import Exposure, ExposureType
from src.analysis.dependency_graph import DependencyGraph


@pytest.fixture
def sample_stablecoins():
    """Create sample stablecoins for testing."""
    return [
        Stablecoin(
            symbol="USDC",
            name="USD Coin",
            stablecoin_type=StablecoinType.FIAT_BACKED,
            contract_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            market_cap=25_000_000_000,
            peg_currency="USD",
            peg_value=1.0
        ),
        Stablecoin(
            symbol="USDT",
            name="Tether",
            stablecoin_type=StablecoinType.FIAT_BACKED,
            contract_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            market_cap=83_000_000_000,
            peg_currency="USD",
            peg_value=1.0
        ),
        Stablecoin(
            symbol="DAI",
            name="Dai",
            stablecoin_type=StablecoinType.CRYPTO_BACKED,
            contract_address="0x6b175474e89094c44da98b954eedeac495271d0f",
            market_cap=5_000_000_000,
            peg_currency="USD",
            peg_value=1.0
        ),
        Stablecoin(
            symbol="UST",
            name="TerraUSD",
            stablecoin_type=StablecoinType.ALGORITHMIC,
            contract_address="terra1...",
            market_cap=0,  # Collapsed
            peg_currency="USD",
            peg_value=1.0
        ),
    ]


@pytest.fixture
def sample_protocols():
    """Create sample protocols for testing."""
    return [
        Protocol(
            name="Aave",
            slug="aave",
            category=ProtocolCategory.LENDING,
            tvl=10_000_000_000,
            chains=["ethereum", "polygon", "avalanche"],
            stablecoin_holdings={
                "USDC": 3_000_000_000,
                "USDT": 2_000_000_000,
                "DAI": 1_500_000_000
            }
        ),
        Protocol(
            name="Curve",
            slug="curve",
            category=ProtocolCategory.DEX,
            tvl=5_000_000_000,
            chains=["ethereum"],
            stablecoin_holdings={
                "USDC": 1_500_000_000,
                "USDT": 1_500_000_000,
                "DAI": 1_000_000_000
            }
        ),
        Protocol(
            name="Compound",
            slug="compound",
            category=ProtocolCategory.LENDING,
            tvl=3_000_000_000,
            chains=["ethereum"],
            stablecoin_holdings={
                "USDC": 2_000_000_000,
                "DAI": 500_000_000
            }
        ),
        Protocol(
            name="Uniswap",
            slug="uniswap",
            category=ProtocolCategory.DEX,
            tvl=4_000_000_000,
            chains=["ethereum", "arbitrum", "optimism"],
            stablecoin_holdings={
                "USDC": 1_000_000_000,
                "USDT": 800_000_000
            }
        ),
    ]


@pytest.fixture
def sample_exposures(sample_protocols):
    """Create sample exposures from protocols."""
    exposures = []
    for protocol in sample_protocols:
        for stablecoin, amount in protocol.stablecoin_holdings.items():
            exposures.append(
                Exposure(
                    protocol_name=protocol.slug,
                    stablecoin_symbol=stablecoin,
                    exposure_type=ExposureType.LIQUIDITY,
                    amount_usd=amount,
                    percentage_of_tvl=amount / protocol.tvl if protocol.tvl > 0 else 0,
                    source="test"
                )
            )
    return exposures


@pytest.fixture
def sample_graph(sample_stablecoins, sample_protocols, sample_exposures):
    """Create a sample dependency graph."""
    graph = DependencyGraph()
    graph.build_from_data(sample_stablecoins, sample_protocols, sample_exposures)
    return graph


@pytest.fixture
def simulation_stablecoins():
    """Stablecoin data in simulation format."""
    return [
        {
            "symbol": "USDC",
            "market_cap": 25_000_000_000,
            "is_algorithmic": False,
            "stablecoin_type": "fiat_backed"
        },
        {
            "symbol": "USDT",
            "market_cap": 83_000_000_000,
            "is_algorithmic": False,
            "stablecoin_type": "fiat_backed"
        },
        {
            "symbol": "DAI",
            "market_cap": 5_000_000_000,
            "is_algorithmic": False,
            "stablecoin_type": "crypto_backed"
        },
    ]


@pytest.fixture
def simulation_protocols():
    """Protocol data in simulation format."""
    return [
        {
            "name": "aave",
            "tvl": 10_000_000_000,
            "exposures": {"USDC": 3_000_000_000, "USDT": 2_000_000_000},
            "category": "lending"
        },
        {
            "name": "curve",
            "tvl": 5_000_000_000,
            "exposures": {"USDC": 1_500_000_000, "DAI": 1_000_000_000},
            "category": "dex"
        },
        {
            "name": "compound",
            "tvl": 3_000_000_000,
            "exposures": {"USDC": 2_000_000_000},
            "category": "lending"
        },
    ]


@pytest.fixture
def default_simulation_config():
    """Default simulation configuration."""
    return {
        "depeg_threshold": 0.02,
        "max_steps": 50,
        "confidence_decay_rate": 0.1,
        "noise_std": 0.01,
        "algorithmic_death_spiral_factor": 0.9,
    }
