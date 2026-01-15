# DepegScope - Project Instructions for Claude Code

## Project Overview

**DepegScope** is a stablecoin depeg contagion analysis framework that:
1. Maps DeFi protocol dependencies and stablecoin exposure
2. Simulates cascade failures when a stablecoin depegs
3. Provides early warning indicators for systemic risk
4. Validates models against historical depeg events

**Target:** Academic publication at Financial Cryptography, IMC, or CCS.

---

## Tech Stack

```
Language: Python 3.10+
Data: Dune Analytics, DeFiLlama API, The Graph, Etherscan
Analysis: pandas, networkx, numpy, scipy
Visualization: matplotlib, plotly, seaborn
Simulation: mesa (agent-based modeling)
Database: SQLite (local), PostgreSQL (optional)
```

---

## Project Structure

```
DepegScope/
├── README.md
├── CLAUDE.md                    # Instructions for Claude Code
├── requirements.txt
├── setup.py
├── .env.example                 # API keys template
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # Global settings
│   └── stablecoins.yaml         # Stablecoin definitions
│
├── data/
│   ├── raw/                     # Raw API responses
│   ├── processed/               # Cleaned datasets
│   └── historical/              # Historical depeg events
│
├── src/
│   ├── __init__.py
│   │
│   ├── collectors/              # Data collection modules
│   │   ├── __init__.py
│   │   ├── defillama.py         # DeFiLlama API
│   │   ├── dune.py              # Dune Analytics queries
│   │   ├── thegraph.py          # The Graph subgraphs
│   │   ├── etherscan.py         # On-chain data
│   │   └── price_feeds.py       # Price history
│   │
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── stablecoin.py        # Stablecoin class
│   │   ├── protocol.py          # Protocol class
│   │   ├── exposure.py          # Exposure relationships
│   │   └── depeg_event.py       # Historical events
│   │
│   ├── analysis/                # Core analysis
│   │   ├── __init__.py
│   │   ├── dependency_graph.py  # Build dependency networks
│   │   ├── contagion_model.py   # Cascade simulation
│   │   ├── risk_metrics.py      # Risk calculations
│   │   ├── early_warning.py     # Predictive indicators
│   │   └── historical.py        # Historical validation
│   │
│   ├── simulation/              # Agent-based simulation
│   │   ├── __init__.py
│   │   ├── agents.py            # Protocol agents
│   │   ├── environment.py       # DeFi environment
│   │   └── scenarios.py         # Depeg scenarios
│   │
│   └── visualization/           # Charts and dashboards
│       ├── __init__.py
│       ├── network_plots.py     # Dependency graphs
│       ├── cascade_viz.py       # Contagion spread
│       ├── risk_dashboard.py    # Risk metrics
│       └── historical_plots.py  # Historical analysis
│
├── notebooks/                   # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_dependency_mapping.ipynb
│   ├── 03_contagion_simulation.ipynb
│   ├── 04_historical_validation.ipynb
│   └── 05_early_warning_analysis.ipynb
│
├── scripts/                     # CLI scripts
│   ├── collect_data.py
│   ├── build_graph.py
│   ├── run_simulation.py
│   └── generate_report.py
│
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_models.py
│   ├── test_analysis.py
│   └── test_simulation.py
│
└── docs/                        # Documentation
    ├── API.md
    ├── METHODOLOGY.md
    └── RESULTS.md
```

---

## Implementation Steps

### STEP 1: Project Setup

Create the basic project structure with all necessary files.

```bash
# Initialize project
mkdir -p config data/{raw,processed,historical} src/{collectors,models,analysis,simulation,visualization} notebooks scripts tests docs

# Create __init__.py files
touch src/__init__.py src/collectors/__init__.py src/models/__init__.py src/analysis/__init__.py src/simulation/__init__.py src/visualization/__init__.py tests/__init__.py
```

**requirements.txt:**
```
# Data Collection
requests>=2.31.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
dune-client>=1.2.0

# Data Processing
pandas>=2.1.0
numpy>=1.24.0
pyyaml>=6.0.0

# Network Analysis
networkx>=3.2.0
python-louvain>=0.16

# Simulation
mesa>=2.1.0
scipy>=1.11.0

# Visualization
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.18.0

# Database
sqlalchemy>=2.0.0

# Web3
web3>=6.11.0

# Utilities
tqdm>=4.66.0
loguru>=0.7.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Notebooks
jupyter>=1.0.0
ipykernel>=6.26.0
```

---

### STEP 2: Configuration

**config/settings.py:**
```python
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

# API Keys
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
THEGRAPH_API_KEY = os.getenv("THEGRAPH_API_KEY")

# DeFiLlama (no key needed)
DEFILLAMA_BASE_URL = "https://api.llama.fi"

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
```

**config/stablecoins.yaml:**
```yaml
stablecoins:
  USDT:
    name: "Tether"
    type: "fiat-backed"
    chain: "multi-chain"
    contract_ethereum: "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    market_cap_rank: 1
    
  USDC:
    name: "USD Coin"
    type: "fiat-backed"
    chain: "multi-chain"
    contract_ethereum: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    market_cap_rank: 2
    
  DAI:
    name: "Dai"
    type: "crypto-backed"
    chain: "ethereum"
    contract_ethereum: "0x6B175474E89094C44Da98b954EescdeCB5f6f"
    collateral: ["USDC", "ETH", "WBTC", "stETH"]
    market_cap_rank: 3
    
  USDe:
    name: "Ethena USDe"
    type: "algorithmic"
    chain: "ethereum"
    contract_ethereum: "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3"
    mechanism: "delta-neutral"
    market_cap_rank: 4
    
  FRAX:
    name: "Frax"
    type: "hybrid"
    chain: "multi-chain"
    contract_ethereum: "0x853d955aCEf822Db058eb8505911ED77F175b99e"
    collateral: ["USDC", "FXS"]
    market_cap_rank: 5

  sUSD:
    name: "Synthetix USD"
    type: "crypto-backed"
    chain: "ethereum"
    contract_ethereum: "0x57Ab1ec28D129707052df4dF418D58a2D46d5f51"
    collateral: ["SNX"]
    
  LUSD:
    name: "Liquity USD"
    type: "crypto-backed"
    chain: "ethereum"
    contract_ethereum: "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0"
    collateral: ["ETH"]
    
  GHO:
    name: "GHO"
    type: "crypto-backed"
    chain: "ethereum"
    contract_ethereum: "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f"
    collateral: ["aTokens"]
    issuer: "Aave"

historical_depegs:
  terra_ust:
    date: "2022-05-09"
    stablecoin: "UST"
    low_price: 0.006
    total_loss_usd: 60000000000
    
  usdc_svb:
    date: "2023-03-11"
    stablecoin: "USDC"
    low_price: 0.87
    recovery_days: 3
    cause: "SVB collapse, $3.3B reserves frozen"
    
  susd_2025:
    date: "2025-04-15"
    stablecoin: "sUSD"
    low_price: 0.68
    cause: "SIP-420 collateral change"
    
  nov_2025_cascade:
    date: "2025-11-06"
    stablecoins: ["xUSD", "deUSD", "USDX"]
    trigger: "xUSD"
    low_prices:
      xUSD: 0.23
      deUSD: 0.02
      USDX: 0.30
    cause: "Stream platform $93M asset loss"
```

---

### STEP 3: Data Collection Modules

**src/collectors/defillama.py:**
```python
"""DeFiLlama API collector for TVL and protocol data."""

import requests
from typing import Dict, List, Optional
from loguru import logger
from config.settings import DEFILLAMA_BASE_URL

class DeFiLlamaCollector:
    """Collect data from DeFiLlama API."""
    
    def __init__(self):
        self.base_url = DEFILLAMA_BASE_URL
        self.session = requests.Session()
    
    def get_all_protocols(self) -> List[Dict]:
        """Fetch all protocols with TVL data."""
        url = f"{self.base_url}/protocols"
        response = self.session.get(url)
        response.raise_for_status()
        logger.info(f"Fetched {len(response.json())} protocols")
        return response.json()
    
    def get_protocol_tvl(self, protocol_slug: str) -> Dict:
        """Get detailed TVL breakdown for a protocol."""
        url = f"{self.base_url}/protocol/{protocol_slug}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_stablecoins(self) -> List[Dict]:
        """Fetch all stablecoins data."""
        url = f"{self.base_url}/stablecoins"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("peggedAssets", [])
    
    def get_stablecoin_charts(self, stablecoin_id: int) -> Dict:
        """Get historical data for a stablecoin."""
        url = f"{self.base_url}/stablecoin/{stablecoin_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_stablecoin_prices(self) -> Dict:
        """Get current prices for all stablecoins."""
        url = f"{self.base_url}/stablecoinprices"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_pools(self) -> List[Dict]:
        """Fetch all liquidity pools."""
        url = f"{self.base_url}/pools"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def get_protocol_treasury(self, protocol_slug: str) -> Dict:
        """Get treasury holdings for a protocol."""
        url = f"{self.base_url}/treasury/{protocol_slug}"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        return {}

    def get_stablecoin_pools(self) -> List[Dict]:
        """Filter pools containing stablecoins."""
        pools = self.get_pools()
        stablecoin_symbols = {"USDT", "USDC", "DAI", "FRAX", "TUSD", "LUSD", "sUSD", "USDe", "GHO", "crvUSD"}
        
        stablecoin_pools = []
        for pool in pools:
            symbols = set(pool.get("symbol", "").upper().split("-"))
            if symbols & stablecoin_symbols:
                stablecoin_pools.append(pool)
        
        logger.info(f"Found {len(stablecoin_pools)} stablecoin pools")
        return stablecoin_pools
```

**src/collectors/price_feeds.py:**
```python
"""Price feed collector for stablecoin prices."""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

class PriceFeedCollector:
    """Collect historical and real-time stablecoin prices."""
    
    def __init__(self):
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
    
    def get_price_history(
        self, 
        coin_id: str, 
        days: int = 365,
        vs_currency: str = "usd"
    ) -> pd.DataFrame:
        """Get historical price data."""
        url = f"{self.coingecko_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily"
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        
        return df
    
    def detect_depeg_events(
        self, 
        prices: pd.DataFrame, 
        threshold: float = 0.02
    ) -> List[Dict]:
        """Detect depeg events from price history."""
        depeg_events = []
        
        prices["deviation"] = abs(prices["price"] - 1.0)
        prices["is_depegged"] = prices["deviation"] > threshold
        
        # Find contiguous depeg periods
        prices["depeg_group"] = (prices["is_depegged"] != prices["is_depegged"].shift()).cumsum()
        
        for group_id, group in prices[prices["is_depegged"]].groupby("depeg_group"):
            event = {
                "start_date": group.index.min(),
                "end_date": group.index.max(),
                "duration_hours": (group.index.max() - group.index.min()).total_seconds() / 3600,
                "min_price": group["price"].min(),
                "max_deviation": group["deviation"].max(),
            }
            depeg_events.append(event)
        
        return depeg_events
    
    def get_current_prices(self, coin_ids: List[str]) -> Dict[str, float]:
        """Get current prices for multiple coins."""
        url = f"{self.coingecko_url}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd"
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return {coin: data["usd"] for coin, data in response.json().items()}

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
}
```

---

### STEP 4: Data Models

**src/models/stablecoin.py:**
```python
"""Stablecoin data model."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class StablecoinType(Enum):
    FIAT_BACKED = "fiat-backed"
    CRYPTO_BACKED = "crypto-backed"
    ALGORITHMIC = "algorithmic"
    HYBRID = "hybrid"

@dataclass
class Stablecoin:
    """Represents a stablecoin and its properties."""
    
    symbol: str
    name: str
    type: StablecoinType
    contract_address: str
    chain: str = "ethereum"
    market_cap: float = 0.0
    current_price: float = 1.0
    collateral: List[str] = field(default_factory=list)
    
    # Exposure tracking
    protocol_exposures: Dict[str, float] = field(default_factory=dict)
    pool_exposures: Dict[str, float] = field(default_factory=dict)
    
    # Risk metrics
    concentration_risk: float = 0.0
    collateral_ratio: float = 1.0
    liquidity_depth: float = 0.0
    
    def total_exposure(self) -> float:
        """Calculate total exposure across all protocols."""
        return sum(self.protocol_exposures.values())
    
    def is_depegged(self, threshold: float = 0.02) -> bool:
        """Check if stablecoin is currently depegged."""
        return abs(self.current_price - 1.0) > threshold
    
    def depeg_severity(self) -> float:
        """Calculate severity of current depeg."""
        return abs(self.current_price - 1.0)
    
    def top_exposures(self, n: int = 10) -> List[tuple]:
        """Get top N protocol exposures."""
        sorted_exposures = sorted(
            self.protocol_exposures.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_exposures[:n]
```

**src/models/protocol.py:**
```python
"""DeFi Protocol data model."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Protocol:
    """Represents a DeFi protocol and its stablecoin exposure."""
    
    name: str
    slug: str
    category: str  # lending, dex, yield, bridge, etc.
    chain: str = "ethereum"
    tvl: float = 0.0
    
    # Stablecoin holdings
    stablecoin_holdings: Dict[str, float] = field(default_factory=dict)
    
    # Dependencies
    collateral_from: List[str] = field(default_factory=list)  # Stablecoins used as collateral
    borrows_from: List[str] = field(default_factory=list)     # Protocols borrowed from
    lends_to: List[str] = field(default_factory=list)         # Protocols lent to
    
    # Risk metrics
    stablecoin_concentration: float = 0.0  # % of TVL in stablecoins
    largest_stablecoin_exposure: str = ""
    
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
    
    def would_cascade(self, depegged_stablecoin: str, threshold: float = 0.10) -> bool:
        """Check if this protocol would be affected by a stablecoin depeg."""
        exposure_ratio = self.exposure_to(depegged_stablecoin) / max(self.tvl, 1)
        return exposure_ratio >= threshold
```

**src/models/exposure.py:**
```python
"""Exposure relationship model."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ExposureType(Enum):
    COLLATERAL = "collateral"       # Stablecoin used as collateral
    LIQUIDITY = "liquidity"         # Stablecoin in liquidity pool
    TREASURY = "treasury"           # Held in protocol treasury
    BORROWED = "borrowed"           # Borrowed stablecoin
    BACKING = "backing"             # Backs another stablecoin

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
    
    def risk_score(self) -> float:
        """Calculate risk score for this exposure."""
        base_score = self.percentage_of_tvl
        
        # Higher risk for collateral exposures
        if self.exposure_type == ExposureType.COLLATERAL:
            base_score *= 1.5
        
        # Higher risk for backing relationships (stablecoin depends on stablecoin)
        if self.exposure_type == ExposureType.BACKING:
            base_score *= 2.0
        
        return min(base_score, 1.0)
```

---

### STEP 5: Dependency Graph Analysis

**src/analysis/dependency_graph.py:**
```python
"""Build and analyze stablecoin dependency graphs."""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Optional
from loguru import logger

from src.models.stablecoin import Stablecoin
from src.models.protocol import Protocol
from src.models.exposure import Exposure, ExposureType

class DependencyGraph:
    """Build and analyze stablecoin-protocol dependency networks."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.stablecoins: Dict[str, Stablecoin] = {}
        self.protocols: Dict[str, Protocol] = {}
        self.exposures: List[Exposure] = []
    
    def add_stablecoin(self, stablecoin: Stablecoin):
        """Add a stablecoin node."""
        self.stablecoins[stablecoin.symbol] = stablecoin
        self.graph.add_node(
            stablecoin.symbol,
            node_type="stablecoin",
            market_cap=stablecoin.market_cap,
            coin_type=stablecoin.type.value
        )
    
    def add_protocol(self, protocol: Protocol):
        """Add a protocol node."""
        self.protocols[protocol.slug] = protocol
        self.graph.add_node(
            protocol.slug,
            node_type="protocol",
            tvl=protocol.tvl,
            category=protocol.category
        )
    
    def add_exposure(self, exposure: Exposure):
        """Add an exposure edge between protocol and stablecoin."""
        self.exposures.append(exposure)
        
        # Direction: stablecoin -> protocol (protocol depends on stablecoin)
        self.graph.add_edge(
            exposure.stablecoin_symbol,
            exposure.protocol_name,
            weight=exposure.amount_usd,
            exposure_type=exposure.exposure_type.value,
            risk_score=exposure.risk_score()
        )
    
    def add_stablecoin_dependency(
        self, 
        dependent: str, 
        backing: str, 
        amount: float
    ):
        """Add dependency between stablecoins (e.g., DAI backed by USDC)."""
        self.graph.add_edge(
            backing,
            dependent,
            weight=amount,
            exposure_type="backing",
            risk_score=1.0  # High risk for stablecoin-stablecoin dependencies
        )
    
    def get_downstream_protocols(self, stablecoin: str) -> List[str]:
        """Get all protocols that would be affected by a stablecoin depeg."""
        if stablecoin not in self.graph:
            return []
        return list(self.graph.successors(stablecoin))
    
    def get_cascade_path(
        self, 
        source_stablecoin: str, 
        max_depth: int = 5
    ) -> Dict[int, List[str]]:
        """Calculate cascade propagation paths from a depegging stablecoin."""
        cascade = {0: [source_stablecoin]}
        visited = {source_stablecoin}
        
        for depth in range(1, max_depth + 1):
            cascade[depth] = []
            for node in cascade[depth - 1]:
                for successor in self.graph.successors(node):
                    if successor not in visited:
                        cascade[depth].append(successor)
                        visited.add(successor)
            
            if not cascade[depth]:
                break
        
        return {k: v for k, v in cascade.items() if v}
    
    def calculate_blast_radius(self, stablecoin: str) -> Dict:
        """Calculate the 'blast radius' of a stablecoin depeg."""
        cascade = self.get_cascade_path(stablecoin)
        
        total_tvl_at_risk = 0.0
        protocols_affected = []
        stablecoins_affected = []
        
        for depth, nodes in cascade.items():
            for node in nodes:
                if node in self.protocols:
                    protocol = self.protocols[node]
                    total_tvl_at_risk += protocol.tvl
                    protocols_affected.append(node)
                elif node in self.stablecoins:
                    stablecoins_affected.append(node)
        
        return {
            "source": stablecoin,
            "total_tvl_at_risk": total_tvl_at_risk,
            "protocols_affected": len(protocols_affected),
            "stablecoins_affected": len(stablecoins_affected),
            "cascade_depth": len(cascade),
            "cascade_path": cascade
        }
    
    def find_systemic_chokepoints(self) -> List[Tuple[str, float]]:
        """Identify stablecoins that are systemic chokepoints."""
        chokepoints = []
        
        for stablecoin in self.stablecoins:
            blast = self.calculate_blast_radius(stablecoin)
            score = (
                blast["total_tvl_at_risk"] * 
                (1 + blast["stablecoins_affected"] * 0.5)  # Extra weight for stablecoin contagion
            )
            chokepoints.append((stablecoin, score))
        
        return sorted(chokepoints, key=lambda x: x[1], reverse=True)
    
    def calculate_centrality_metrics(self) -> pd.DataFrame:
        """Calculate network centrality metrics for all nodes."""
        metrics = []
        
        # Calculate various centrality measures
        degree_cent = nx.degree_centrality(self.graph)
        in_degree = dict(self.graph.in_degree(weight="weight"))
        out_degree = dict(self.graph.out_degree(weight="weight"))
        
        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
        except:
            pagerank = {n: 0 for n in self.graph.nodes()}
        
        try:
            betweenness = nx.betweenness_centrality(self.graph, weight="weight")
        except:
            betweenness = {n: 0 for n in self.graph.nodes()}
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            metrics.append({
                "node": node,
                "type": node_data.get("node_type", "unknown"),
                "degree_centrality": degree_cent.get(node, 0),
                "in_degree_weighted": in_degree.get(node, 0),
                "out_degree_weighted": out_degree.get(node, 0),
                "pagerank": pagerank.get(node, 0),
                "betweenness": betweenness.get(node, 0)
            })
        
        return pd.DataFrame(metrics).sort_values("pagerank", ascending=False)
    
    def export_for_visualization(self) -> Dict:
        """Export graph data for visualization."""
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node,
                **data
            })
        
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **data
            })
        
        return {"nodes": nodes, "edges": edges}
```

---

### STEP 6: Contagion Simulation

**src/simulation/contagion_model.py:**
```python
"""Agent-based contagion simulation model."""

from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
import numpy as np
from typing import Dict, List, Optional
from loguru import logger

class StablecoinAgent(Agent):
    """Agent representing a stablecoin."""
    
    def __init__(self, unique_id: str, model: "ContagionModel", **kwargs):
        super().__init__(unique_id, model)
        self.symbol = unique_id
        self.price = 1.0
        self.market_cap = kwargs.get("market_cap", 1e9)
        self.collateral = kwargs.get("collateral", [])
        self.collateral_ratio = kwargs.get("collateral_ratio", 1.0)
        self.is_algorithmic = kwargs.get("is_algorithmic", False)
        
        # State
        self.is_depegged = False
        self.depeg_severity = 0.0
        self.confidence = 1.0
    
    def step(self):
        """Execute one step of the simulation."""
        # Check if collateral has depegged
        collateral_health = self._calculate_collateral_health()
        
        # Confidence drops if collateral is unhealthy
        if collateral_health < 0.9:
            self.confidence *= (0.5 + 0.5 * collateral_health)
        
        # Price follows confidence with some noise
        noise = np.random.normal(0, 0.01)
        self.price = max(0.01, self.confidence + noise)
        
        # Update depeg status
        self.depeg_severity = abs(1.0 - self.price)
        self.is_depegged = self.depeg_severity > 0.02
        
        # Algorithmic stablecoins are more sensitive
        if self.is_algorithmic and self.is_depegged:
            self.price *= 0.9  # Death spiral acceleration
    
    def _calculate_collateral_health(self) -> float:
        """Calculate health of collateral backing."""
        if not self.collateral:
            return 1.0
        
        health_sum = 0
        for collateral_symbol in self.collateral:
            collateral_agent = self.model.get_agent(collateral_symbol)
            if collateral_agent:
                health_sum += collateral_agent.price
            else:
                health_sum += 1.0
        
        return health_sum / len(self.collateral)
    
    def trigger_depeg(self, severity: float = 0.1):
        """Externally trigger a depeg event."""
        self.confidence = 1.0 - severity
        self.price = self.confidence


class ProtocolAgent(Agent):
    """Agent representing a DeFi protocol."""
    
    def __init__(self, unique_id: str, model: "ContagionModel", **kwargs):
        super().__init__(unique_id, model)
        self.name = unique_id
        self.tvl = kwargs.get("tvl", 1e8)
        self.stablecoin_exposures: Dict[str, float] = kwargs.get("exposures", {})
        self.liquidation_threshold = kwargs.get("liquidation_threshold", 0.8)
        
        # State
        self.is_distressed = False
        self.tvl_lost = 0.0
    
    def step(self):
        """Execute one step of the simulation."""
        total_exposure_loss = 0
        
        for stablecoin, exposure in self.stablecoin_exposures.items():
            agent = self.model.get_agent(stablecoin)
            if agent and agent.is_depegged:
                # Loss proportional to depeg severity and exposure
                loss = exposure * agent.depeg_severity
                total_exposure_loss += loss
        
        # Protocol becomes distressed if losses exceed threshold
        if self.tvl > 0:
            loss_ratio = total_exposure_loss / self.tvl
            self.is_distressed = loss_ratio > (1 - self.liquidation_threshold)
            self.tvl_lost = total_exposure_loss
            self.tvl = max(0, self.tvl - total_exposure_loss)


class ContagionModel(Model):
    """Main contagion simulation model."""
    
    def __init__(
        self,
        stablecoins: List[Dict],
        protocols: List[Dict],
        initial_depeg: Optional[Dict] = None
    ):
        super().__init__()
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.step_count = 0
        
        # Create stablecoin agents
        for sc in stablecoins:
            agent = StablecoinAgent(sc["symbol"], self, **sc)
            self.schedule.add(agent)
        
        # Create protocol agents
        for proto in protocols:
            agent = ProtocolAgent(proto["name"], self, **proto)
            self.schedule.add(agent)
        
        # Apply initial depeg if specified
        if initial_depeg:
            self._trigger_initial_depeg(initial_depeg)
        
        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "Total_TVL_Lost": self._total_tvl_lost,
                "Depegged_Stablecoins": self._count_depegged,
                "Distressed_Protocols": self._count_distressed,
                "Average_Stablecoin_Price": self._avg_stablecoin_price,
            },
            agent_reporters={
                "Price": lambda a: getattr(a, "price", None),
                "TVL": lambda a: getattr(a, "tvl", None),
                "Is_Depegged": lambda a: getattr(a, "is_depegged", None),
                "Is_Distressed": lambda a: getattr(a, "is_distressed", None),
            }
        )
    
    def get_agent(self, unique_id: str) -> Optional[Agent]:
        """Get agent by unique ID."""
        for agent in self.schedule.agents:
            if agent.unique_id == unique_id:
                return agent
        return None
    
    def _trigger_initial_depeg(self, depeg_config: Dict):
        """Trigger initial depeg event."""
        agent = self.get_agent(depeg_config["stablecoin"])
        if agent:
            agent.trigger_depeg(depeg_config.get("severity", 0.1))
            logger.info(f"Triggered depeg for {depeg_config['stablecoin']}")
    
    def step(self):
        """Execute one step of the model."""
        self.datacollector.collect(self)
        self.schedule.step()
        self.step_count += 1
        
        # Check for cascade completion
        if self._count_depegged() == 0 and self.step_count > 5:
            self.running = False
    
    def run_simulation(self, max_steps: int = 100) -> Dict:
        """Run full simulation and return results."""
        for _ in range(max_steps):
            if not self.running:
                break
            self.step()
        
        return {
            "steps": self.step_count,
            "total_tvl_lost": self._total_tvl_lost(),
            "depegged_stablecoins": self._count_depegged(),
            "distressed_protocols": self._count_distressed(),
            "history": self.datacollector.get_model_vars_dataframe()
        }
    
    def _total_tvl_lost(self) -> float:
        return sum(
            a.tvl_lost for a in self.schedule.agents 
            if isinstance(a, ProtocolAgent)
        )
    
    def _count_depegged(self) -> int:
        return sum(
            1 for a in self.schedule.agents 
            if isinstance(a, StablecoinAgent) and a.is_depegged
        )
    
    def _count_distressed(self) -> int:
        return sum(
            1 for a in self.schedule.agents 
            if isinstance(a, ProtocolAgent) and a.is_distressed
        )
    
    def _avg_stablecoin_price(self) -> float:
        prices = [
            a.price for a in self.schedule.agents 
            if isinstance(a, StablecoinAgent)
        ]
        return np.mean(prices) if prices else 1.0
```

---

### STEP 7: Risk Metrics

**src/analysis/risk_metrics.py:**
```python
"""Risk metrics and scoring for stablecoins and protocols."""

import numpy as np
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass

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
    
    # Computed
    @property
    def composite_score(self) -> float:
        """Weighted composite risk score."""
        weights = {
            "concentration": 0.25,
            "liquidity": 0.25,
            "contagion": 0.30,
            "collateral": 0.20
        }
        return (
            weights["concentration"] * self.concentration_risk +
            weights["liquidity"] * self.liquidity_risk +
            weights["contagion"] * self.contagion_risk +
            weights["collateral"] * self.collateral_risk
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


class RiskCalculator:
    """Calculate various risk metrics."""
    
    def __init__(self, dependency_graph):
        self.graph = dependency_graph
    
    def calculate_concentration_risk(self, exposures: Dict[str, float]) -> float:
        """Calculate Herfindahl-Hirschman Index for exposure concentration."""
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
        return normalized
    
    def calculate_liquidity_risk(
        self, 
        market_cap: float, 
        daily_volume: float,
        pool_depth: float
    ) -> float:
        """Calculate liquidity risk based on market metrics."""
        # Volume ratio (higher is better)
        volume_ratio = daily_volume / max(market_cap, 1)
        volume_score = 1 - min(volume_ratio * 10, 1)  # Cap at 10% daily volume
        
        # Pool depth ratio
        depth_ratio = pool_depth / max(market_cap, 1)
        depth_score = 1 - min(depth_ratio * 5, 1)  # Cap at 20% depth
        
        return (volume_score + depth_score) / 2
    
    def calculate_contagion_risk(self, stablecoin: str) -> float:
        """Calculate contagion risk based on dependency graph."""
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
    
    def calculate_collateral_risk(self, collateral_composition: Dict[str, float]) -> float:
        """Calculate collateral risk for crypto-backed stablecoins."""
        if not collateral_composition:
            return 0.0  # No collateral = fiat-backed, lower risk
        
        risk_weights = {
            "USDC": 0.1,    # Low risk
            "USDT": 0.2,    # Medium-low
            "ETH": 0.4,     # Volatile
            "WBTC": 0.4,    # Volatile
            "stETH": 0.5,   # Liquid staking derivative
            "other": 0.6,   # Unknown = higher risk
        }
        
        total = sum(collateral_composition.values())
        if total == 0:
            return 0.5
        
        weighted_risk = 0
        for asset, amount in collateral_composition.items():
            weight = risk_weights.get(asset, risk_weights["other"])
            weighted_risk += (amount / total) * weight
        
        return weighted_risk
    
    def generate_risk_report(self) -> pd.DataFrame:
        """Generate comprehensive risk report for all stablecoins."""
        reports = []
        
        for symbol, stablecoin in self.graph.stablecoins.items():
            score = RiskScore(
                entity_name=symbol,
                entity_type="stablecoin",
                concentration_risk=self.calculate_concentration_risk(
                    stablecoin.protocol_exposures
                ),
                contagion_risk=self.calculate_contagion_risk(symbol),
                collateral_risk=self.calculate_collateral_risk(
                    {c: 1 for c in stablecoin.collateral}  # Simplified
                )
            )
            
            reports.append({
                "symbol": symbol,
                "type": stablecoin.type.value,
                "market_cap": stablecoin.market_cap,
                "concentration_risk": score.concentration_risk,
                "contagion_risk": score.contagion_risk,
                "collateral_risk": score.collateral_risk,
                "composite_score": score.composite_score,
                "risk_level": score.risk_level
            })
        
        return pd.DataFrame(reports).sort_values("composite_score", ascending=False)
```

---

### STEP 8: Early Warning System

**src/analysis/early_warning.py:**
```python
"""Early warning indicators for stablecoin depegs."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from loguru import logger

class EarlyWarningSystem:
    """Detect early warning signals for stablecoin depegs."""
    
    def __init__(self):
        self.indicators = {}
        self.thresholds = {
            "price_deviation": 0.005,      # 0.5% from peg
            "volume_spike": 2.0,           # 2x normal volume
            "pool_imbalance": 0.40,        # 40% imbalance in Curve pools
            "redemption_spike": 3.0,       # 3x normal redemptions
            "liquidity_drop": 0.20,        # 20% liquidity decrease
        }
    
    def check_price_deviation(self, prices: pd.Series) -> Dict:
        """Check for sustained price deviation from peg."""
        current_price = prices.iloc[-1]
        deviation = abs(current_price - 1.0)
        
        # Check trend
        if len(prices) >= 24:
            trend = prices.iloc[-24:].mean() - prices.iloc[-48:-24].mean()
        else:
            trend = 0
        
        warning = deviation > self.thresholds["price_deviation"]
        
        return {
            "indicator": "price_deviation",
            "value": deviation,
            "threshold": self.thresholds["price_deviation"],
            "trend": trend,
            "warning": warning,
            "severity": "HIGH" if deviation > 0.02 else "MEDIUM" if warning else "LOW"
        }
    
    def check_volume_spike(
        self, 
        current_volume: float, 
        historical_avg: float
    ) -> Dict:
        """Check for abnormal trading volume."""
        if historical_avg == 0:
            ratio = 0
        else:
            ratio = current_volume / historical_avg
        
        warning = ratio > self.thresholds["volume_spike"]
        
        return {
            "indicator": "volume_spike",
            "value": ratio,
            "threshold": self.thresholds["volume_spike"],
            "warning": warning,
            "severity": "HIGH" if ratio > 5 else "MEDIUM" if warning else "LOW"
        }
    
    def check_curve_pool_imbalance(self, pool_composition: Dict[str, float]) -> Dict:
        """Check Curve pool imbalance (major depeg indicator)."""
        total = sum(pool_composition.values())
        if total == 0:
            return {"indicator": "pool_imbalance", "warning": False, "severity": "LOW"}
        
        shares = [v / total for v in pool_composition.values()]
        expected_share = 1 / len(shares)
        
        max_deviation = max(abs(s - expected_share) for s in shares)
        
        warning = max_deviation > self.thresholds["pool_imbalance"]
        
        return {
            "indicator": "pool_imbalance",
            "value": max_deviation,
            "threshold": self.thresholds["pool_imbalance"],
            "warning": warning,
            "severity": "CRITICAL" if max_deviation > 0.6 else "HIGH" if warning else "LOW"
        }
    
    def check_liquidity_drop(
        self, 
        current_liquidity: float, 
        previous_liquidity: float
    ) -> Dict:
        """Check for sudden liquidity withdrawals."""
        if previous_liquidity == 0:
            change = 0
        else:
            change = (previous_liquidity - current_liquidity) / previous_liquidity
        
        warning = change > self.thresholds["liquidity_drop"]
        
        return {
            "indicator": "liquidity_drop",
            "value": change,
            "threshold": self.thresholds["liquidity_drop"],
            "warning": warning,
            "severity": "HIGH" if change > 0.4 else "MEDIUM" if warning else "LOW"
        }
    
    def aggregate_warnings(self, checks: List[Dict]) -> Dict:
        """Aggregate multiple warning checks into overall risk assessment."""
        warnings = [c for c in checks if c.get("warning", False)]
        
        severity_scores = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        max_severity = max(
            (severity_scores.get(c.get("severity", "LOW"), 0) for c in checks),
            default=0
        )
        
        severity_labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_warnings": len(warnings),
            "warning_indicators": [w["indicator"] for w in warnings],
            "overall_severity": severity_labels[max_severity],
            "recommendation": self._get_recommendation(len(warnings), max_severity),
            "details": checks
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
    ) -> Dict:
        """Run all early warning checks for a stablecoin."""
        checks = [
            self.check_price_deviation(price_history),
            self.check_volume_spike(current_volume, avg_volume),
            self.check_curve_pool_imbalance(pool_composition),
            self.check_liquidity_drop(current_liquidity, previous_liquidity),
        ]
        
        result = self.aggregate_warnings(checks)
        result["stablecoin"] = stablecoin
        
        return result
```

---

### STEP 9: Main Scripts

**scripts/collect_data.py:**
```python
#!/usr/bin/env python3
"""Collect all data needed for DepegScope analysis."""

import argparse
import json
from pathlib import Path
from loguru import logger

from src.collectors.defillama import DeFiLlamaCollector
from src.collectors.price_feeds import PriceFeedCollector, COINGECKO_IDS
from config.settings import RAW_DATA_DIR, MAJOR_STABLECOINS

def main():
    parser = argparse.ArgumentParser(description="Collect DepegScope data")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    args = parser.parse_args()
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize collectors
    llama = DeFiLlamaCollector()
    price_collector = PriceFeedCollector()
    
    # 1. Collect stablecoin data
    logger.info("Collecting stablecoin data...")
    stablecoins = llama.get_stablecoins()
    with open(args.output_dir / "stablecoins.json", "w") as f:
        json.dump(stablecoins, f, indent=2)
    logger.info(f"Saved {len(stablecoins)} stablecoins")
    
    # 2. Collect protocol data
    logger.info("Collecting protocol data...")
    protocols = llama.get_all_protocols()
    with open(args.output_dir / "protocols.json", "w") as f:
        json.dump(protocols, f, indent=2)
    logger.info(f"Saved {len(protocols)} protocols")
    
    # 3. Collect stablecoin pools
    logger.info("Collecting stablecoin pools...")
    pools = llama.get_stablecoin_pools()
    with open(args.output_dir / "stablecoin_pools.json", "w") as f:
        json.dump(pools, f, indent=2)
    logger.info(f"Saved {len(pools)} stablecoin pools")
    
    # 4. Collect price history
    logger.info("Collecting price history...")
    price_history = {}
    for symbol in MAJOR_STABLECOINS:
        coin_id = COINGECKO_IDS.get(symbol)
        if coin_id:
            try:
                df = price_collector.get_price_history(coin_id, days=365)
                price_history[symbol] = df.to_dict()
                logger.info(f"  Collected {symbol} price history")
            except Exception as e:
                logger.warning(f"  Failed to collect {symbol}: {e}")
    
    with open(args.output_dir / "price_history.json", "w") as f:
        json.dump(price_history, f, indent=2, default=str)
    
    logger.info("Data collection complete!")

if __name__ == "__main__":
    main()
```

**scripts/run_simulation.py:**
```python
#!/usr/bin/env python3
"""Run contagion simulation scenarios."""

import argparse
import json
from pathlib import Path
from loguru import logger

from src.simulation.contagion_model import ContagionModel
from config.settings import PROCESSED_DATA_DIR

def load_simulation_data(data_dir: Path):
    """Load processed data for simulation."""
    with open(data_dir / "stablecoins_processed.json") as f:
        stablecoins = json.load(f)
    with open(data_dir / "protocols_processed.json") as f:
        protocols = json.load(f)
    return stablecoins, protocols

def run_scenario(
    stablecoins: list,
    protocols: list,
    trigger_stablecoin: str,
    severity: float = 0.1
):
    """Run a single depeg scenario."""
    model = ContagionModel(
        stablecoins=stablecoins,
        protocols=protocols,
        initial_depeg={
            "stablecoin": trigger_stablecoin,
            "severity": severity
        }
    )
    
    results = model.run_simulation(max_steps=100)
    return results

def main():
    parser = argparse.ArgumentParser(description="Run DepegScope simulation")
    parser.add_argument("--trigger", type=str, required=True, help="Stablecoin to trigger depeg")
    parser.add_argument("--severity", type=float, default=0.1, help="Initial depeg severity")
    parser.add_argument("--data-dir", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data_dir}")
    stablecoins, protocols = load_simulation_data(args.data_dir)
    
    logger.info(f"Running simulation: {args.trigger} depeg at {args.severity*100}% severity")
    results = run_scenario(
        stablecoins=stablecoins,
        protocols=protocols,
        trigger_stablecoin=args.trigger,
        severity=args.severity
    )
    
    logger.info(f"Simulation complete:")
    logger.info(f"  Steps: {results['steps']}")
    logger.info(f"  Total TVL Lost: ${results['total_tvl_lost']:,.0f}")
    logger.info(f"  Depegged Stablecoins: {results['depegged_stablecoins']}")
    logger.info(f"  Distressed Protocols: {results['distressed_protocols']}")
    
    if args.output:
        results["history"] = results["history"].to_dict()
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
```

---

### STEP 10: README.md

```markdown
# DepegScope

Stablecoin depeg contagion analysis framework. Maps DeFi protocol dependencies, simulates cascade failures, and provides early warning indicators for systemic risk.

## Features

- **Dependency Mapping**: Build comprehensive graphs of stablecoin ↔ protocol relationships
- **Contagion Simulation**: Agent-based modeling of depeg cascade propagation
- **Risk Metrics**: Quantitative scoring for concentration, liquidity, and contagion risk
- **Early Warning System**: Real-time indicators for potential depegs
- **Historical Validation**: Validated against Terra/UST, USDC/SVB, and 2025 cascade events

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/DepegScope.git
cd DepegScope
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
```

## Quick Start

```bash
# 1. Collect data
python scripts/collect_data.py

# 2. Build dependency graph
python scripts/build_graph.py

# 3. Run simulation
python scripts/run_simulation.py --trigger USDC --severity 0.1

# 4. Generate risk report
python scripts/generate_report.py
```

## Project Structure

```
DepegScope/
├── src/
│   ├── collectors/      # Data collection (DeFiLlama, Dune, etc.)
│   ├── models/          # Data models (Stablecoin, Protocol, Exposure)
│   ├── analysis/        # Core analysis (graphs, risk metrics, warnings)
│   ├── simulation/      # Agent-based contagion modeling
│   └── visualization/   # Charts and dashboards
├── notebooks/           # Jupyter analysis notebooks
├── scripts/             # CLI tools
└── data/                # Raw and processed data
```

## Research

This framework supports academic research on DeFi systemic risk. Target venues:
- Financial Cryptography (FC)
- Internet Measurement Conference (IMC)
- ACM CCS

## License

MIT

## Citation

If you use DepegScope in your research, please cite:
```bibtex
@software{depegscope2025,
  title={DepegScope: Stablecoin Depeg Contagion Analysis Framework},
  author={Your Name},
  year={2025},
  url={https://github.com/YOUR_USERNAME/DepegScope}
}
```
```

---

## Execution Order for Claude Code

Tell Claude Code to execute in this order:

1. **"Set up project structure"** - Create all directories and files
2. **"Implement config and settings"** - `config/settings.py`, `config/stablecoins.yaml`
3. **"Implement data collectors"** - `src/collectors/*.py`
4. **"Implement data models"** - `src/models/*.py`
5. **"Implement dependency graph"** - `src/analysis/dependency_graph.py`
6. **"Implement contagion simulation"** - `src/simulation/contagion_model.py`
7. **"Implement risk metrics"** - `src/analysis/risk_metrics.py`
8. **"Implement early warning system"** - `src/analysis/early_warning.py`
9. **"Create CLI scripts"** - `scripts/*.py`
10. **"Create notebooks"** - Jupyter notebooks for exploration
11. **"Add tests"** - Unit tests in `tests/`
12. **"Run data collection and test"** - Verify everything works

---

## Key Commands for Claude Code

```
# Initialize project
"Create the full DepegScope project structure with all directories and __init__.py files"

# Implement modules
"Implement the DeFiLlama collector in src/collectors/defillama.py"
"Implement the dependency graph analysis in src/analysis/dependency_graph.py"
"Implement the contagion simulation model using Mesa"

# Run and test
"Run the data collection script and save results"
"Test the simulation with USDC as trigger"
"Generate a risk report for all major stablecoins"
```

Good luck building DepegScope! 🚀