# Getting Started with DepegScope

A quick guide to setting up and running DepegScope for stablecoin depeg contagion analysis.

---

## Prerequisites

- Python 3.10 or higher
- Git
- 4GB+ RAM (for large simulations)
- Internet connection (for data collection)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DepegScope.git
cd DepegScope
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys (Optional)

Create a `.env` file for API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required for advanced features:
- `ETHERSCAN_API_KEY`: For on-chain data
- `DUNE_API_KEY`: For Dune Analytics queries
- `COINGECKO_API_KEY`: For higher rate limits

---

## Quick Start

### Option 1: Run Full Pipeline

```bash
# Collect data, build graph, run simulation, generate report
make all
```

Or manually:

```bash
# 1. Collect data from APIs
python scripts/collect_data.py

# 2. Build dependency graph
python scripts/build_graph.py

# 3. Run a simulation
python scripts/run_simulation.py --trigger USDC --severity 0.1

# 4. Generate report
python scripts/generate_report.py --generate-plots
```

### Option 2: Use Jupyter Notebooks

```bash
jupyter notebook notebooks/01_data_exploration.ipynb
```

---

## Basic Usage

### Collecting Data

```bash
# Collect all data with defaults (365 days history, top 100 protocols)
python scripts/collect_data.py

# Custom options
python scripts/collect_data.py \
    --days 90 \
    --top-protocols 50 \
    --min-pool-tvl 500000 \
    --output-dir data/custom
```

### Building the Dependency Graph

```bash
# Build graph with minimum TVL filter
python scripts/build_graph.py --min-tvl 1000000

# Export for visualization
python scripts/build_graph.py --export-graph
```

### Running Simulations

```bash
# Single simulation with custom trigger
python scripts/run_simulation.py --trigger USDT --severity 0.15

# Use predefined scenario
python scripts/run_simulation.py --scenario usdc_svb

# Monte Carlo simulation
python scripts/run_simulation.py --trigger USDC --monte-carlo 1000 --output results.json
```

### Generating Reports

```bash
# Generate all report formats with plots
python scripts/generate_report.py --format all --generate-plots

# JSON only
python scripts/generate_report.py --format json
```

---

## Understanding the Output

### Directory Structure After Running

```
DepegScope/
├── data/
│   ├── raw/                    # Raw API responses
│   │   ├── stablecoins.json
│   │   ├── protocols.json
│   │   └── ...
│   └── processed/              # Cleaned data
│       ├── stablecoins_processed.json
│       ├── centrality_metrics.csv
│       └── graph_visualization.json
├── reports/
│   ├── risk_report_*.json      # Analysis results
│   └── plots/                  # Visualizations
│       ├── risk_dashboard_*.png
│       └── network_*.html
└── logs/                       # Execution logs
```

### Key Output Files

| File | Description |
|------|-------------|
| `centrality_metrics.csv` | Network centrality for each entity |
| `graph_visualization.json` | D3.js-compatible graph data |
| `risk_report_*.json` | Comprehensive risk analysis |
| `risk_dashboard_*.png` | Visual risk summary |
| `network_interactive_*.html` | Interactive network explorer |

---

## Common Tasks

### Analyze a Specific Stablecoin

```python
from src.analysis.dependency_graph import DependencyGraph
from src.analysis.risk_metrics import RiskCalculator

# Load graph
graph = DependencyGraph()
graph.load_from_file("data/processed/graph_visualization.json")

# Get exposure for USDC
exposure = graph.get_stablecoin_exposure("USDC")
print(f"USDC total exposure: ${exposure:,.0f}")

# Calculate blast radius
blast_radius = graph.calculate_blast_radius("USDC")
print(f"USDC blast radius: ${blast_radius:,.0f}")
```

### Run Custom Scenario

```python
from src.simulation.environment import DeFiEnvironment
from src.simulation.scenarios import DepegScenario

scenario = DepegScenario(
    name="custom_scenario",
    description="Custom USDT severe depeg",
    trigger_stablecoin="USDT",
    initial_severity=0.20,  # 20% depeg
    market_stress=2.0       # High stress
)

env = DeFiEnvironment(stablecoins, protocols)
env.trigger_depeg(scenario.trigger_stablecoin, scenario.initial_severity)
results = env.run_simulation()

print(f"TVL Lost: ${results['total_tvl_lost']:,.0f}")
```

### Monitor Early Warning Indicators

```python
from src.analysis.early_warning import EarlyWarningSystem

ews = EarlyWarningSystem()

# Check current indicators for USDC
alerts = ews.check_stablecoin("USDC")
for alert in alerts:
    print(f"{alert.indicator}: {alert.level} - {alert.message}")
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEPEGSCOPE_DATA_DIR` | Data directory | `./data` |
| `DEPEGSCOPE_LOG_LEVEL` | Logging level | `INFO` |
| `ETHERSCAN_API_KEY` | Etherscan API key | None |
| `COINGECKO_API_KEY` | CoinGecko API key | None |
| `DUNE_API_KEY` | Dune Analytics key | None |

### Configuration Files

- `config/settings.py`: Global settings and paths
- `config/stablecoins.yaml`: Stablecoin definitions and historical events

---

## Troubleshooting

### Common Issues

**1. "No stablecoin data found"**
```
Solution: Run data collection first
$ python scripts/collect_data.py
```

**2. "Rate limit exceeded"**
```
Solution: Add API key or wait before retrying
- Add COINGECKO_API_KEY to .env for higher limits
- Use --skip-prices flag for faster collection
```

**3. "ImportError: No module named 'mesa'"**
```
Solution: Ensure virtual environment is activated and dependencies installed
$ source venv/bin/activate
$ pip install -r requirements.txt
```

**4. "Graph too large to visualize"**
```
Solution: Increase minimum TVL filter
$ python scripts/build_graph.py --min-tvl 10000000
```

### Getting Help

- Check the logs in `logs/` directory
- Enable verbose mode: `--verbose` or `-v`
- Open an issue on GitHub

---

## Next Steps

1. **Explore the data**: Open `notebooks/01_data_exploration.ipynb`
2. **Run validation**: Compare against historical events
3. **Customize scenarios**: Create your own depeg scenarios
4. **Generate visualizations**: Create publication-ready figures
5. **Read the methodology**: See `docs/METHODOLOGY.md`

---

## Project Structure

```
DepegScope/
├── config/             # Configuration files
├── data/               # Data storage
├── docs/               # Documentation
├── notebooks/          # Jupyter notebooks
├── reports/            # Generated reports
├── scripts/            # CLI scripts
├── src/                # Source code
│   ├── analysis/       # Risk analysis modules
│   ├── collectors/     # Data collection
│   ├── models/         # Data models
│   ├── simulation/     # Agent-based simulation
│   └── visualization/  # Plotting and dashboards
├── tests/              # Unit tests
├── requirements.txt    # Python dependencies
└── README.md           # Project overview
```
