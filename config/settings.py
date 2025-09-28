"""Global configuration settings for DepegScope."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
HISTORICAL_DATA_DIR = DATA_DIR / "historical"
CONFIG_DIR = ROOT_DIR / "config"

# API Keys
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
THEGRAPH_API_KEY = os.getenv("THEGRAPH_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")  # Optional, for pro features

# DeFiLlama (no key needed)
DEFILLAMA_BASE_URL = "https://api.llama.fi"
DEFILLAMA_STABLECOINS_URL = "https://stablecoins.llama.fi"
DEFILLAMA_YIELDS_URL = "https://yields.llama.fi"

# CoinGecko
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Stablecoin Configuration
MAJOR_STABLECOINS = [
    "USDT", "USDC", "DAI", "FRAX", "TUSD",
    "USDP", "GUSD", "LUSD", "sUSD", "USDe",
    "FDUSD", "GHO", "crvUSD", "PYUSD"
]

# Analysis Parameters
DEPEG_THRESHOLD = 0.02  # 2% deviation from peg
CONTAGION_THRESHOLD = 0.10  # 10% exposure triggers cascade
SIMULATION_STEPS = 100
DEFAULT_LOOKBACK_DAYS = 365

# Risk Thresholds
RISK_THRESHOLDS = {
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
    "critical": 1.0
}

# Early Warning Thresholds
EARLY_WARNING_THRESHOLDS = {
    "price_deviation": 0.005,      # 0.5% from peg
    "volume_spike": 2.0,           # 2x normal volume
    "pool_imbalance": 0.40,        # 40% imbalance in Curve pools
    "redemption_spike": 3.0,       # 3x normal redemptions
    "liquidity_drop": 0.20,        # 20% liquidity decrease
}

# Network Analysis Parameters
NETWORK_CONFIG = {
    "min_edge_weight": 1_000_000,  # $1M minimum exposure
    "max_cascade_depth": 10,
    "pagerank_damping": 0.85,
}

# Simulation Parameters
SIMULATION_CONFIG = {
    "max_steps": 100,
    "confidence_decay_rate": 0.1,
    "noise_std": 0.01,
    "algorithmic_death_spiral_factor": 0.9,
    "liquidation_threshold": 0.8,
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
