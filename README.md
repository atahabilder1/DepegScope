# DepegScope

**Stablecoin Depeg Contagion Analysis Framework**

DepegScope is a comprehensive framework for analyzing systemic risk and contagion dynamics in DeFi ecosystems, with a focus on stablecoin depeg events.

## Overview

The explosive growth of decentralized finance (DeFi) has created a complex web of dependencies between protocols and stablecoins. When stablecoins lose their peg, cascading failures can propagate through interconnected protocols, causing widespread losses.

DepegScope provides:

- **Dependency Graph Analysis**: Map protocol-stablecoin relationships and identify systemic chokepoints
- **Agent-Based Simulation**: Model cascade dynamics with realistic market behaviors
- **Risk Metrics**: Quantify blast radius, contagion index, and Value at Risk (VaR)
- **Early Warning System**: Monitor indicators that precede depeg events
- **Historical Validation**: Validate models against real events (Terra/UST, USDC/SVB)

## Key Features

- Network analysis of stablecoin-protocol dependencies
- Monte Carlo simulations for risk quantification
- Centrality and systemic risk metrics
- Interactive visualizations and dashboards
- Predefined scenarios for common depeg events
- Comprehensive CLI tools for automation

## Installation

### Prerequisites

- Python 3.10 or higher
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/DepegScope.git
cd DepegScope

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

## Quick Start

### 1. Collect Data

```bash
python scripts/collect_data.py --days 365 --top-protocols 100
```

### 2. Build Dependency Graph

```bash
python scripts/build_graph.py --min-tvl 1000000 --export-graph
```

### 3. Run Simulation

```bash
# Single simulation
python scripts/run_simulation.py --trigger USDC --severity 0.1

# Monte Carlo
python scripts/run_simulation.py --scenario usdc_svb --monte-carlo 1000
```

### 4. Generate Report

```bash
python scripts/generate_report.py --format all --generate-plots
```

## Project Structure

```
DepegScope/
├── config/             # Configuration files
│   ├── settings.py     # Global settings
│   └── stablecoins.yaml
├── src/
│   ├── collectors/     # Data collection from APIs
│   ├── models/         # Data models
│   ├── analysis/       # Risk analysis modules
│   ├── simulation/     # Agent-based simulation
│   └── visualization/  # Plotting and dashboards
├── scripts/            # CLI scripts
├── notebooks/          # Jupyter notebooks
├── tests/              # Test suite
├── docs/               # Documentation
├── data/               # Data storage
└── reports/            # Generated reports
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Methodology](docs/METHODOLOGY.md)
- [API Reference](docs/API.md)
- [Paper Structure](docs/PAPER_STRUCTURE.md)
- [Submission Venues](docs/SUBMISSION_VENUES.md)

## Usage Examples

### Python API

```python
from src.analysis.dependency_graph import DependencyGraph
from src.analysis.risk_metrics import RiskCalculator
from src.simulation.environment import DeFiEnvironment

# Build dependency graph
graph = DependencyGraph()
graph.build_from_data(stablecoins, protocols, exposures)

# Calculate risk metrics
calc = RiskCalculator(graph)
risk = calc.calculate_stablecoin_risk("USDC")
print(f"USDC Risk Score: {risk.overall_score:.2f}")

# Run simulation
env = DeFiEnvironment(stablecoins, protocols)
env.trigger_depeg("USDC", severity=0.10)
results = env.run_simulation()
print(f"TVL Lost: ${results['total_tvl_lost']:,.0f}")
```

### Jupyter Notebooks

```bash
jupyter notebook notebooks/01_data_exploration.ipynb
```

## Key Metrics

| Metric | Description |
|--------|-------------|
| Blast Radius | TVL at risk from a single depeg event |
| Contagion Index | Measure of cascade propagation potential |
| HHI Concentration | Protocol diversification measure |
| VaR (95%) | Value at Risk at 95% confidence |

## Historical Validation

The model has been validated against:

- **Terra/UST Collapse** (May 2022): $60B+ impact
- **USDC/SVB Crisis** (March 2023): ~12% depeg, recovered
- **2025 Cascade Events**: Multiple secondary depegs

## Research Applications

This framework supports academic research in:

- DeFi systemic risk analysis
- Stablecoin stability mechanisms
- Network effects in financial systems
- Agent-based modeling of market dynamics

### Target Venues

- Financial Cryptography (FC)
- Internet Measurement Conference (IMC)
- ACM CCS
- AFT (Advances in Financial Technologies)

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Data sources:
- [DeFiLlama](https://defillama.com/) - Protocol and stablecoin data
- [CoinGecko](https://www.coingecko.com/) - Price history
- [Dune Analytics](https://dune.com/) - On-chain metrics

## Citation

If you use DepegScope in your research, please cite:

```bibtex
@software{depegscope2024,
  title = {DepegScope: Stablecoin Depeg Contagion Analysis Framework},
  year = {2024},
  url = {https://github.com/yourusername/DepegScope}
}
```
