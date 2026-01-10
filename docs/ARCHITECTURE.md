# DepegScope System Architecture

## High-Level Architecture

```
                                    DepegScope Architecture
    ┌─────────────────────────────────────────────────────────────────────────────┐
    │                                                                             │
    │  ┌─────────────────────────────────────────────────────────────────────┐   │
    │  │                        DATA COLLECTION LAYER                         │   │
    │  │                                                                      │   │
    │  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
    │  │   │  DeFiLlama   │  │  CoinGecko   │  │    Dune      │             │   │
    │  │   │  Collector   │  │  Collector   │  │  Collector   │             │   │
    │  │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │   │
    │  │          │                 │                 │                      │   │
    │  │   ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐             │   │
    │  │   │  The Graph   │  │  Etherscan   │  │   Custom     │             │   │
    │  │   │  Collector   │  │  Collector   │  │   Sources    │             │   │
    │  │   └──────────────┘  └──────────────┘  └──────────────┘             │   │
    │  └──────────────────────────────┬──────────────────────────────────────┘   │
    │                                 │                                           │
    │                                 ▼                                           │
    │  ┌─────────────────────────────────────────────────────────────────────┐   │
    │  │                          DATA MODELS LAYER                           │   │
    │  │                                                                      │   │
    │  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │   │
    │  │   │ Stablecoin  │  │  Protocol   │  │  Exposure   │  │  DepegEvent│ │   │
    │  │   │   Model     │  │   Model     │  │   Model     │  │   Model   │ │   │
    │  │   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │   │
    │  └──────────────────────────────┬──────────────────────────────────────┘   │
    │                                 │                                           │
    │                                 ▼                                           │
    │  ┌─────────────────────────────────────────────────────────────────────┐   │
    │  │                         ANALYSIS LAYER                               │   │
    │  │                                                                      │   │
    │  │   ┌───────────────────────────────────────────────────────────────┐ │   │
    │  │   │                    Dependency Graph                            │ │   │
    │  │   │                      (NetworkX)                                │ │   │
    │  │   └────────────────────────────┬──────────────────────────────────┘ │   │
    │  │                                │                                     │   │
    │  │   ┌────────────────┐  ┌────────┴───────┐  ┌─────────────────────┐  │   │
    │  │   │ Risk Metrics   │  │   Contagion    │  │   Early Warning     │  │   │
    │  │   │  Calculator    │  │   Analyzer     │  │      System         │  │   │
    │  │   └────────────────┘  └────────────────┘  └─────────────────────┘  │   │
    │  │                                                                      │   │
    │  │   ┌─────────────────────────────────────────────────────────────┐   │   │
    │  │   │              Historical Validator                            │   │   │
    │  │   └─────────────────────────────────────────────────────────────┘   │   │
    │  └──────────────────────────────┬──────────────────────────────────────┘   │
    │                                 │                                           │
    │                                 ▼                                           │
    │  ┌─────────────────────────────────────────────────────────────────────┐   │
    │  │                       SIMULATION LAYER                               │   │
    │  │                                                                      │   │
    │  │   ┌─────────────────────────────────────────────────────────────┐   │   │
    │  │   │                    DeFi Environment                          │   │   │
    │  │   │                      (Mesa ABM)                              │   │   │
    │  │   └────────────────────────────┬────────────────────────────────┘   │   │
    │  │                                │                                     │   │
    │  │   ┌────────────┐  ┌────────────┴────────────┐  ┌────────────────┐  │   │
    │  │   │ Stablecoin │  │    Protocol Agent       │  │  Market Agents │  │   │
    │  │   │   Agent    │  │                         │  │ (Liquidators,  │  │   │
    │  │   │            │  │                         │  │  Arbitrageurs) │  │   │
    │  │   └────────────┘  └─────────────────────────┘  └────────────────┘  │   │
    │  │                                                                      │   │
    │  │   ┌─────────────────────────────────────────────────────────────┐   │   │
    │  │   │              Scenario Runner (Monte Carlo)                   │   │   │
    │  │   └─────────────────────────────────────────────────────────────┘   │   │
    │  └──────────────────────────────┬──────────────────────────────────────┘   │
    │                                 │                                           │
    │                                 ▼                                           │
    │  ┌─────────────────────────────────────────────────────────────────────┐   │
    │  │                      VISUALIZATION LAYER                             │   │
    │  │                                                                      │   │
    │  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │   │
    │  │   │   Network    │  │   Cascade    │  │      Risk Dashboard      │ │   │
    │  │   │  Visualizer  │  │  Visualizer  │  │                          │ │   │
    │  │   └──────────────┘  └──────────────┘  └──────────────────────────┘ │   │
    │  │                                                                      │   │
    │  │   ┌─────────────────────────────────────────────────────────────┐   │   │
    │  │   │              Historical Plotter                              │   │   │
    │  │   └─────────────────────────────────────────────────────────────┘   │   │
    │  └─────────────────────────────────────────────────────────────────────┘   │
    │                                                                             │
    └─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Data Collection Layer

The data collection layer interfaces with external APIs and data sources to gather information about stablecoins, protocols, and their relationships.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  DeFiLlama API ──────────►  ┌──────────────────┐                │
│  - Protocols                │                  │                │
│  - TVL data                 │   DeFiLlama      │                │
│  - Stablecoins              │   Collector      │───┐            │
│  - Pool composition         │                  │   │            │
│                             └──────────────────┘   │            │
│                                                    │            │
│  CoinGecko API ──────────►  ┌──────────────────┐   │            │
│  - Price history            │                  │   │            │
│  - Market cap               │   Price Feed     │───┤            │
│  - Volume data              │   Collector      │   │            │
│                             └──────────────────┘   │            │
│                                                    ▼            │
│  Dune Analytics ──────────►  ┌──────────────────┐  ┌─────────┐ │
│  - On-chain metrics         │                  │  │         │ │
│  - Transfer flows           │   Dune           │──►│  Raw    │ │
│  - Custom queries           │   Collector      │  │  Data   │ │
│                             └──────────────────┘  │  Store  │ │
│                                                    │         │ │
│  The Graph ──────────────►  ┌──────────────────┐  └────┬────┘ │
│  - Uniswap pools            │                  │       │      │
│  - Aave markets             │   TheGraph       │───────┘      │
│  - Curve data               │   Collector      │              │
│                             └──────────────────┘              │
│                                                                │
│  Etherscan ──────────────►  ┌──────────────────┐              │
│  - Token supplies           │                  │              │
│  - Contract data            │   Etherscan      │──────────────┘
│  - Transfer history         │   Collector      │
│                             └──────────────────┘
│                                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Data Models Layer

Clean, typed data structures that represent the domain entities.

```
┌─────────────────────────────────────────────────────────────────┐
│                       Data Models Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Stablecoin                                                   ││
│  │ ├── symbol: str                                              ││
│  │ ├── name: str                                                ││
│  │ ├── type: StablecoinType (fiat/crypto/algo/hybrid)          ││
│  │ ├── market_cap: float                                        ││
│  │ ├── contract_address: str                                    ││
│  │ ├── backing_assets: List[str]                                ││
│  │ └── exposures: Dict[str, float]                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Protocol                                                     ││
│  │ ├── name: str                                                ││
│  │ ├── slug: str                                                ││
│  │ ├── category: ProtocolCategory (dex/lending/yield/...)      ││
│  │ ├── tvl: float                                               ││
│  │ ├── chains: List[str]                                        ││
│  │ └── stablecoin_holdings: Dict[str, float]                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Exposure                                                     ││
│  │ ├── protocol_name: str                                       ││
│  │ ├── stablecoin_symbol: str                                   ││
│  │ ├── exposure_type: ExposureType (collateral/liquidity/...)  ││
│  │ ├── amount_usd: float                                        ││
│  │ └── percentage_of_tvl: float                                 ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ DepegEvent                                                   ││
│  │ ├── stablecoin: str                                          ││
│  │ ├── start_date: datetime                                     ││
│  │ ├── end_date: datetime                                       ││
│  │ ├── max_deviation: float                                     ││
│  │ ├── cascade_effects: List[str]                               ││
│  │ └── tvl_impact: float                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Analysis Layer

Network analysis and risk quantification using the dependency graph.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Analysis Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Dependency Graph                          ││
│  │                      (NetworkX)                              ││
│  │                                                              ││
│  │     Stablecoin Nodes ◄──────► Protocol Nodes                ││
│  │          (USDC)                  (Aave)                      ││
│  │          (USDT)    Weighted      (Curve)                     ││
│  │          (DAI)      Edges        (Uniswap)                   ││
│  │                                                              ││
│  │  Methods:                                                    ││
│  │  - build_from_data()                                         ││
│  │  - calculate_centrality_metrics()                            ││
│  │  - calculate_blast_radius()                                  ││
│  │  - find_systemic_chokepoints()                               ││
│  │  - simulate_cascade()                                        ││
│  └──────────────────────────┬──────────────────────────────────┘│
│                             │                                    │
│          ┌──────────────────┼──────────────────┐                │
│          ▼                  ▼                  ▼                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Risk Metrics  │  │ Contagion    │  │   Early Warning      │  │
│  │ Calculator   │  │  Analyzer    │  │      System          │  │
│  │              │  │              │  │                      │  │
│  │- HHI         │  │- Static      │  │- Price deviation     │  │
│  │- VaR/CVaR    │  │- Dynamic     │  │- Volume spikes       │  │
│  │- Contagion   │  │- Multi-      │  │- Pool imbalance      │  │
│  │  Index       │  │  trigger     │  │- Redemption rate     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Historical Validator                            ││
│  │                                                              ││
│  │  - Validate against UST collapse                             ││
│  │  - Validate against USDC/SVB                                 ││
│  │  - Cross-validation methodology                              ││
│  │  - Accuracy metrics calculation                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Simulation Layer

Agent-based modeling using the Mesa framework.

```
┌─────────────────────────────────────────────────────────────────┐
│                       Simulation Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   DeFi Environment                           ││
│  │                    (Mesa Model)                              ││
│  │                                                              ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │                    Scheduler                           │  ││
│  │  │              (RandomActivation)                        │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  │                           │                                  ││
│  │            ┌──────────────┼──────────────┐                  ││
│  │            ▼              ▼              ▼                  ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    ││
│  │  │  Stablecoin  │ │   Protocol   │ │   Market Agents  │    ││
│  │  │    Agents    │ │    Agents    │ │                  │    ││
│  │  │              │ │              │ │ - Liquidators    │    ││
│  │  │ - Price      │ │ - TVL        │ │ - Arbitrageurs   │    ││
│  │  │ - Confidence │ │ - Exposure   │ │                  │    ││
│  │  │ - Depeg state│ │ - Distress   │ │                  │    ││
│  │  └──────────────┘ └──────────────┘ └──────────────────┘    ││
│  │                                                              ││
│  │  ┌───────────────────────────────────────────────────────┐  ││
│  │  │                  Data Collector                        │  ││
│  │  │           (Records state each step)                    │  ││
│  │  └───────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Scenario Runner                            ││
│  │                                                              ││
│  │  Predefined Scenarios:                                       ││
│  │  - USDC SVB crisis                                           ││
│  │  - UST collapse                                              ││
│  │  - Custom scenarios                                          ││
│  │                                                              ││
│  │  Execution Modes:                                            ││
│  │  - Single run                                                ││
│  │  - Monte Carlo (N simulations)                               ││
│  │  - Sensitivity analysis                                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Visualization Layer

Publication-quality figures and interactive dashboards.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Visualization Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Network          │  │  Cascade         │                     │
│  │ Visualizer       │  │  Visualizer      │                     │
│  │                  │  │                  │                     │
│  │ - Matplotlib     │  │ - Timeline       │                     │
│  │ - Plotly         │  │ - Animation      │                     │
│  │ - Interactive    │  │ - Sankey         │                     │
│  │ - Heatmaps       │  │   diagrams       │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Risk Dashboard   │  │  Historical      │                     │
│  │                  │  │  Plotter         │                     │
│  │ - Gauges         │  │                  │                     │
│  │ - Risk summaries │  │ - Price history  │                     │
│  │ - VaR charts     │  │ - Validation     │                     │
│  │ - Comparisons    │  │   plots          │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  Output Formats:                                                 │
│  - PNG (300 DPI for publication)                                │
│  - PDF (vector graphics)                                        │
│  - HTML (interactive)                                           │
│  - GIF (animations)                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow                                       │
│                                                                             │
│  External APIs                                                              │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │    Raw      │ -> │  Processed  │ -> │  Dependency │ -> │  Analysis   │ │
│  │    Data     │    │    Data     │    │    Graph    │    │   Results   │ │
│  │   (JSON)    │    │   (JSON)    │    │  (NetworkX) │    │   (CSV/DF)  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│                                               │                             │
│                                               ▼                             │
│                                        ┌─────────────┐                      │
│                                        │ Simulation  │                      │
│                                        │   Engine    │                      │
│                                        │   (Mesa)    │                      │
│                                        └──────┬──────┘                      │
│                                               │                             │
│                                               ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   Reports   │ <- │  Risk       │ <- │ Simulation  │                     │
│  │   (JSON/    │    │  Metrics    │    │  Results    │                     │
│  │    HTML)    │    │   (DF)      │    │   (Dict)    │                     │
│  └─────────────┘    └─────────────┘    └─────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
DepegScope/
├── config/                 # Configuration
│   ├── settings.py        # Global settings
│   └── stablecoins.yaml   # Stablecoin definitions
│
├── src/                   # Source code
│   ├── collectors/        # Data collection
│   │   ├── defillama.py
│   │   ├── price_feeds.py
│   │   ├── dune.py
│   │   ├── thegraph.py
│   │   └── etherscan.py
│   │
│   ├── models/            # Data models
│   │   ├── stablecoin.py
│   │   ├── protocol.py
│   │   ├── exposure.py
│   │   └── depeg_event.py
│   │
│   ├── analysis/          # Analysis modules
│   │   ├── dependency_graph.py
│   │   ├── risk_metrics.py
│   │   ├── contagion_model.py
│   │   ├── early_warning.py
│   │   └── historical.py
│   │
│   ├── simulation/        # Agent-based simulation
│   │   ├── agents.py
│   │   ├── environment.py
│   │   └── scenarios.py
│   │
│   └── visualization/     # Plotting and dashboards
│       ├── network_plots.py
│       ├── cascade_viz.py
│       ├── risk_dashboard.py
│       └── historical_plots.py
│
├── scripts/               # CLI entry points
│   ├── collect_data.py
│   ├── build_graph.py
│   ├── run_simulation.py
│   └── generate_report.py
│
├── notebooks/             # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_network_analysis.ipynb
│   ├── 03_simulation_scenarios.ipynb
│   └── 04_historical_validation.ipynb
│
├── tests/                 # Test suite
│   ├── test_collectors.py
│   ├── test_models.py
│   ├── test_analysis.py
│   └── test_simulation.py
│
├── data/                  # Data storage
│   ├── raw/              # Raw API responses
│   └── processed/        # Cleaned data
│
├── reports/               # Generated reports
│   └── plots/            # Visualization outputs
│
└── docs/                  # Documentation
    ├── PAPER_STRUCTURE.md
    ├── SUBMISSION_VENUES.md
    ├── METHODOLOGY.md
    └── API.md
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.10+ | Core implementation |
| Data Processing | Pandas, NumPy | Data manipulation |
| Network Analysis | NetworkX | Graph algorithms |
| Simulation | Mesa | Agent-based modeling |
| Visualization | Matplotlib, Plotly | Static and interactive plots |
| API Clients | Requests, aiohttp | Data collection |
| Configuration | python-dotenv, PyYAML | Settings management |
| Logging | Loguru | Structured logging |
| Testing | Pytest | Test framework |
