# DepegScope API Documentation

Complete API reference for all DepegScope modules.

---

## Table of Contents

1. [Data Models](#1-data-models)
2. [Data Collectors](#2-data-collectors)
3. [Analysis Modules](#3-analysis-modules)
4. [Simulation Framework](#4-simulation-framework)
5. [Visualization](#5-visualization)

---

## 1. Data Models

### 1.1 Stablecoin

```python
from src.models.stablecoin import Stablecoin, StablecoinType

# Create a stablecoin
stablecoin = Stablecoin(
    symbol="USDC",
    name="USD Coin",
    stablecoin_type=StablecoinType.FIAT_BACKED,
    contract_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    chain="ethereum",
    peg_currency="USD",
    peg_value=1.0,
    market_cap=25_000_000_000,
    circulating_supply=25_000_000_000,
    backing_assets=["USD", "US Treasuries"],
    issuer="Circle"
)

# Properties
stablecoin.is_algorithmic  # False
stablecoin.total_exposure  # Sum of protocol exposures

# Methods
stablecoin.add_exposure(protocol, amount)
stablecoin.to_dict()
Stablecoin.from_dict(data)
```

**StablecoinType Enum:**
```python
class StablecoinType(Enum):
    FIAT_BACKED = "fiat_backed"
    CRYPTO_BACKED = "crypto_backed"
    ALGORITHMIC = "algorithmic"
    COMMODITY_BACKED = "commodity_backed"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"
```

### 1.2 Protocol

```python
from src.models.protocol import Protocol, ProtocolCategory

protocol = Protocol(
    name="Aave",
    slug="aave",
    category=ProtocolCategory.LENDING,
    tvl=10_000_000_000,
    chains=["ethereum", "polygon", "avalanche"],
    stablecoin_holdings={"USDC": 3_000_000_000, "DAI": 2_000_000_000}
)

# Properties
protocol.total_stablecoin_exposure  # Sum of stablecoin holdings
protocol.stablecoin_ratio          # Stablecoin TVL / Total TVL
protocol.dominant_stablecoin       # Largest stablecoin exposure

# Methods
protocol.get_exposure_to(stablecoin_symbol)
protocol.calculate_risk_from_depeg(stablecoin, severity)
protocol.to_dict()
Protocol.from_dict(data)
Protocol.from_defillama(api_response)
```

**ProtocolCategory Enum:**
```python
class ProtocolCategory(Enum):
    DEX = "dex"
    LENDING = "lending"
    CDP = "cdp"
    YIELD = "yield"
    BRIDGE = "bridge"
    DERIVATIVES = "derivatives"
    LIQUID_STAKING = "liquid_staking"
    OTHER = "other"
```

### 1.3 Exposure

```python
from src.models.exposure import Exposure, ExposureType

exposure = Exposure(
    protocol_name="aave",
    stablecoin_symbol="USDC",
    exposure_type=ExposureType.COLLATERAL,
    amount_usd=3_000_000_000,
    percentage_of_tvl=0.30,
    chain="ethereum",
    source="defillama"
)

# Methods
exposure.to_dict()
Exposure.from_dict(data)
```

### 1.4 DepegEvent

```python
from src.models.depeg_event import DepegEvent, HISTORICAL_EVENTS

event = DepegEvent(
    stablecoin="UST",
    start_date=datetime(2022, 5, 9),
    end_date=datetime(2022, 5, 13),
    min_price=0.01,
    max_deviation=0.99,
    trigger="Bank run and algorithmic failure",
    cascade_effects=["LUNA collapse", "3AC bankruptcy"],
    tvl_impact=60_000_000_000,
    recovery=False
)

# Access predefined events
ust_event = HISTORICAL_EVENTS["ust_collapse"]
usdc_event = HISTORICAL_EVENTS["usdc_svb"]
```

---

## 2. Data Collectors

### 2.1 DeFiLlamaCollector

```python
from src.collectors.defillama import DeFiLlamaCollector

collector = DeFiLlamaCollector()

# Get all stablecoins
stablecoins = collector.get_stablecoins()

# Get all protocols
protocols = collector.get_all_protocols()

# Get top protocols by TVL
top_100 = collector.get_top_protocols_by_tvl(limit=100)

# Get protocol details
aave = collector.get_protocol_details("aave")

# Get stablecoin pools
pools = collector.get_stablecoin_pools(min_tvl=100_000)

# Build exposure matrix
slugs = ["aave", "compound", "curve"]
matrix = collector.build_exposure_matrix(slugs)
# Returns: {"aave": {"USDC": 3e9, "DAI": 2e9}, ...}
```

### 2.2 PriceFeedCollector

```python
from src.collectors.price_feeds import PriceFeedCollector, COINGECKO_IDS

collector = PriceFeedCollector()

# Get price history
df = collector.get_price_history("usd-coin", days=365)
# Returns DataFrame with: price, market_cap, volume

# Detect depeg events
events = collector.detect_depeg_events(df, threshold=0.02)
# Returns list of (start_date, end_date, min_price)

# Get current price
price = collector.get_current_price("tether")

# Available coin IDs
print(COINGECKO_IDS)  # {"USDC": "usd-coin", "USDT": "tether", ...}
```

### 2.3 DuneCollector

```python
from src.collectors.dune import DuneCollector

collector = DuneCollector(api_key="your_api_key")

# Run custom query
results = collector.run_query(query_id=123456)

# Get stablecoin transfers
transfers = collector.get_stablecoin_transfers(
    token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    days=30
)
```

### 2.4 TheGraphCollector

```python
from src.collectors.thegraph import TheGraphCollector

collector = TheGraphCollector()

# Query Uniswap V3 pools
pools = collector.get_uniswap_v3_pools(stablecoin="USDC", min_tvl=1_000_000)

# Query Aave markets
markets = collector.get_aave_markets()

# Query Curve pools
curve_pools = collector.get_curve_pools()
```

---

## 3. Analysis Modules

### 3.1 DependencyGraph

```python
from src.analysis.dependency_graph import DependencyGraph

graph = DependencyGraph()

# Build from data
graph.build_from_data(stablecoins, protocols, exposures)

# Add entities manually
graph.add_stablecoin(stablecoin)
graph.add_protocol(protocol)
graph.add_exposure(protocol_name, stablecoin_symbol, amount, exposure_type)

# Query methods
exposure = graph.get_stablecoin_exposure("USDC")
protocols = graph.get_protocols_exposed_to("USDC")
stablecoins = graph.get_protocol_stablecoin_exposure("aave")

# Network analysis
centrality_df = graph.calculate_centrality_metrics()
# Columns: entity, type, degree, betweenness, pagerank, eigenvector

# Cascade analysis
blast_radius = graph.calculate_blast_radius("USDC", severity=0.1)
cascade_path = graph.simulate_cascade("USDC", severity=0.1)
# Returns: [(step, affected_entities, cumulative_impact), ...]

# Systemic risk
chokepoints = graph.find_systemic_chokepoints()
# Returns: [(stablecoin, risk_score), ...] sorted by risk

# Graph statistics
summary = graph.summary()
# Returns: {nodes, edges, stablecoins, protocols, total_exposure_usd}

# Export
viz_data = graph.export_for_visualization()
# Returns: {nodes: [...], edges: [...]} for D3.js
```

### 3.2 RiskCalculator

```python
from src.analysis.risk_metrics import RiskCalculator, RiskScore

calc = RiskCalculator(dependency_graph)

# Stablecoin risk
risk = calc.calculate_stablecoin_risk("USDC")
# Returns RiskScore dataclass

# Protocol risk
risk = calc.calculate_protocol_risk("aave")

# Concentration risk (HHI)
hhi = calc.calculate_concentration_risk("aave")
# Returns 0-1 (1 = single stablecoin, 0 = perfectly diversified)

# Value at Risk
var_metrics = calc.calculate_var(confidence=0.95, n_simulations=1000)
# Returns: {var, cvar, expected_loss, max_loss}

# Generate reports
stablecoin_report = calc.generate_risk_report()
protocol_report = calc.generate_protocol_risk_report()
# Returns DataFrames with risk metrics

# Ecosystem risk
ecosystem = calc.calculate_ecosystem_risk()
# Returns: {overall_ecosystem_risk, high_risk_stablecoins, high_risk_protocols, ...}
```

**RiskScore Dataclass:**
```python
@dataclass
class RiskScore:
    entity_name: str
    entity_type: str  # "stablecoin" or "protocol"
    overall_score: float  # 0-1
    concentration_risk: float
    contagion_risk: float
    market_risk: float
    liquidity_risk: float
    factors: Dict[str, float]
    timestamp: datetime
```

### 3.3 ContagionAnalyzer

```python
from src.analysis.contagion_model import ContagionAnalyzer

analyzer = ContagionAnalyzer(dependency_graph)

# Static analysis
static = analyzer.analyze_static_contagion("USDC", severity=0.1)
# Returns: {direct_impact, indirect_impact, total_tvl_at_risk, affected_protocols}

# Dynamic simulation
dynamic = analyzer.analyze_dynamic_contagion(
    trigger="USDC",
    severity=0.1,
    max_steps=100,
    seed=42
)
# Returns: {steps, timeline, final_state, metrics}

# Multi-trigger scenario
multi = analyzer.analyze_multi_trigger(
    triggers=[("USDC", 0.1), ("USDT", 0.05)],
    simultaneous=True
)

# Get cascade paths
paths = analyzer.get_cascade_paths("USDC", max_depth=5)
# Returns list of propagation paths
```

### 3.4 EarlyWarningSystem

```python
from src.analysis.early_warning import EarlyWarningSystem, AlertLevel

ews = EarlyWarningSystem()

# Check single stablecoin
alerts = ews.check_stablecoin(
    symbol="USDC",
    current_price=0.995,
    volume_24h=5_000_000_000,
    avg_volume_7d=2_000_000_000
)

# Check all stablecoins
all_alerts = ews.check_all(stablecoin_data)

# Get composite warning score
score = ews.calculate_composite_score("USDC", indicators)
# Returns 0-1 (higher = more concerning)

# Historical analysis
historical = ews.analyze_historical_warnings(price_history)
# Returns detected warning periods
```

**AlertLevel Enum:**
```python
class AlertLevel(Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
```

### 3.5 HistoricalValidator

```python
from src.analysis.historical import HistoricalValidator

validator = HistoricalValidator(dependency_graph, contagion_analyzer)

# Validate against historical event
results = validator.validate_event(
    event=HISTORICAL_EVENTS["usdc_svb"],
    historical_data=price_history
)
# Returns: {accuracy, predicted_affected, actual_affected, mape, correlation}

# Cross-validation
cv_results = validator.cross_validate(events_list, k_folds=5)

# Backtest
backtest = validator.backtest(
    start_date=datetime(2022, 1, 1),
    end_date=datetime(2023, 12, 31),
    events=all_events
)
```

---

## 4. Simulation Framework

### 4.1 DeFiEnvironment

```python
from src.simulation.environment import DeFiEnvironment

config = {
    "depeg_threshold": 0.02,
    "max_steps": 100,
    "confidence_decay_rate": 0.1,
    "noise_std": 0.01,
    "algorithmic_death_spiral_factor": 0.9,
}

env = DeFiEnvironment(
    stablecoins=stablecoin_list,
    protocols=protocol_list,
    config=config,
    seed=42
)

# Trigger depeg
env.trigger_depeg("USDC", severity=0.1)

# Run simulation
results = env.run_simulation()
# Returns: {steps, total_tvl_lost, depegged_stablecoins, distressed_protocols,
#           contagion_index, price_history, tvl_history}

# Step-by-step execution
while not env.is_equilibrium():
    env.step()
    state = env.get_current_state()

# Get simulation data
price_df = env.datacollector.get_agent_vars_dataframe()
model_df = env.datacollector.get_model_vars_dataframe()
```

### 4.2 Agents

```python
from src.simulation.agents import (
    StablecoinAgent, ProtocolAgent,
    LiquidatorAgent, ArbitragerAgent
)

# Stablecoin agent
stablecoin_agent = StablecoinAgent(
    unique_id=1,
    model=env,
    symbol="USDC",
    initial_price=1.0,
    market_cap=25e9,
    is_algorithmic=False
)

# Access state
stablecoin_agent.price
stablecoin_agent.confidence
stablecoin_agent.is_depegged

# Protocol agent
protocol_agent = ProtocolAgent(
    unique_id=2,
    model=env,
    name="aave",
    tvl=10e9,
    stablecoin_exposures={"USDC": 3e9, "DAI": 2e9}
)

# Access state
protocol_agent.current_tvl
protocol_agent.is_distressed
protocol_agent.calculate_loss(stablecoin_prices)
```

### 4.3 Scenarios

```python
from src.simulation.scenarios import (
    DepegScenario, ScenarioRunner,
    PREDEFINED_SCENARIOS, get_scenario, list_scenarios
)

# List available scenarios
scenarios = list_scenarios()

# Get predefined scenario
scenario = get_scenario("usdc_svb")

# Create custom scenario
custom = DepegScenario(
    name="custom_severe",
    description="Severe USDT depeg under market stress",
    trigger_stablecoin="USDT",
    initial_severity=0.20,
    market_stress=2.0,
    secondary_triggers=[("USDC", 0.05)],
    config_overrides={"confidence_decay_rate": 0.2}
)

# Run with ScenarioRunner
runner = ScenarioRunner(stablecoins, protocols)

# Single run
results = runner.run_scenario(scenario, seed=42)

# Monte Carlo
mc_results = runner.run_monte_carlo(scenario, n_runs=1000, seed_start=0)
# Returns: {tvl_loss: {mean, std, percentile_95, percentile_99},
#           depegged_stablecoins: {...}, distressed_protocols: {...}}

# Compare scenarios
comparison = runner.compare_scenarios([scenario1, scenario2, scenario3])
```

---

## 5. Visualization

### 5.1 NetworkVisualizer

```python
from src.visualization.network_plots import NetworkVisualizer

viz = NetworkVisualizer(dependency_graph)

# Static network plot
fig = viz.plot_dependency_network(
    layout="spring",
    node_size_by="market_cap",
    edge_width_by="exposure",
    highlight=["USDC", "aave"],
    save_path="network.png"
)

# Interactive Plotly network
fig = viz.create_interactive_network(
    save_path="network_interactive.html"
)

# Heatmap of exposures
fig = viz.plot_exposure_heatmap(
    protocols=top_20_protocols,
    stablecoins=top_10_stablecoins,
    save_path="heatmap.png"
)
```

### 5.2 CascadeVisualizer

```python
from src.visualization.cascade_viz import CascadeVisualizer

viz = CascadeVisualizer()

# Timeline of cascade
fig = viz.plot_cascade_timeline(
    simulation_results,
    save_path="cascade_timeline.png"
)

# Animated cascade (for presentations)
anim = viz.create_cascade_animation(
    simulation_results,
    save_path="cascade.gif"
)

# Sankey diagram of flows
fig = viz.plot_contagion_sankey(
    cascade_paths,
    save_path="sankey.png"
)
```

### 5.3 RiskDashboard

```python
from src.visualization.risk_dashboard import RiskDashboard

dashboard = RiskDashboard()

# Full dashboard
fig = dashboard.create_risk_summary_dashboard(
    stablecoin_risks=risk_df,
    protocol_risks=protocol_risk_df,
    ecosystem_risk=ecosystem_metrics,
    save_path="dashboard.png"
)

# Individual components
fig = dashboard.plot_risk_gauge(risk_score, title="Ecosystem Risk")
fig = dashboard.plot_risk_breakdown(risk_factors)
fig = dashboard.plot_var_distribution(var_simulations)
```

### 5.4 HistoricalPlotter

```python
from src.visualization.historical_plots import HistoricalPlotter

plotter = HistoricalPlotter()

# Price history with events
fig = plotter.plot_price_history(
    price_df,
    events=[ust_event, usdc_event],
    save_path="price_history.png"
)

# Validation comparison
fig = plotter.plot_validation_comparison(
    predicted=predicted_affected,
    actual=actual_affected,
    save_path="validation.png"
)

# Multi-event comparison
fig = plotter.plot_event_comparison(
    events=[ust_event, usdc_event],
    metrics=["tvl_impact", "duration", "severity"],
    save_path="event_comparison.png"
)
```

---

## Error Handling

All modules raise specific exceptions:

```python
from src.exceptions import (
    DataCollectionError,
    InvalidStablecoinError,
    SimulationError,
    GraphConstructionError
)

try:
    data = collector.get_stablecoins()
except DataCollectionError as e:
    logger.error(f"Failed to collect data: {e}")
```

---

## Logging

All modules use loguru for logging:

```python
from loguru import logger

# Configure logging level
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Logs are automatically generated with context
# [2024-01-15 10:30:45] INFO | Building dependency graph...
# [2024-01-15 10:30:46] DEBUG | Added 24 stablecoin nodes
```
