# DepegScope Methodology

## Overview

This document provides a detailed explanation of the methodology used in DepegScope for analyzing stablecoin depeg contagion in DeFi ecosystems.

---

## 1. Data Collection Methodology

### 1.1 Data Sources

| Source | Data Type | Update Frequency | API |
|--------|-----------|------------------|-----|
| DeFiLlama | Protocol TVL, stablecoin data | Real-time | REST |
| CoinGecko | Price history, market data | Minute-level | REST |
| Dune Analytics | On-chain metrics | Hourly | GraphQL |
| The Graph | Protocol-specific data | Block-level | GraphQL |
| Etherscan | Token supplies, transfers | Block-level | REST |

### 1.2 Stablecoin Data Collection

```
For each stablecoin S:
    1. Fetch basic info: symbol, name, type, contract address
    2. Fetch market data: market cap, circulating supply
    3. Fetch price history: daily OHLCV for N days
    4. Fetch backing/reserve composition (if available)
    5. Classify type: fiat-backed, crypto-backed, algorithmic
```

### 1.3 Protocol Data Collection

```
For each protocol P with TVL > threshold:
    1. Fetch basic info: name, category, chains
    2. Fetch TVL and TVL history
    3. Fetch token composition (stablecoin holdings)
    4. Calculate stablecoin exposure ratios
    5. Identify liquidity pools containing stablecoins
```

### 1.4 Exposure Matrix Construction

The exposure matrix E captures the relationship between protocols and stablecoins:

```
E[p][s] = USD value of stablecoin s held by protocol p
```

Construction process:
1. Query DeFiLlama for protocol token breakdowns
2. For DEXes: aggregate liquidity pool compositions
3. For lending: aggregate collateral and borrowing
4. For yield aggregators: trace underlying positions
5. Cross-validate with on-chain data where possible

---

## 2. Dependency Graph Model

### 2.1 Graph Definition

The dependency graph G = (V, E) where:
- V = V_s ∪ V_p (stablecoin nodes ∪ protocol nodes)
- E = {(p, s, w) : protocol p has exposure to stablecoin s with weight w}

### 2.2 Node Attributes

**Stablecoin Nodes:**
```python
{
    "type": "stablecoin",
    "symbol": str,
    "market_cap": float,
    "stablecoin_type": Enum,  # fiat, crypto, algorithmic
    "peg_currency": str,
    "is_algorithmic": bool
}
```

**Protocol Nodes:**
```python
{
    "type": "protocol",
    "name": str,
    "tvl": float,
    "category": Enum,  # dex, lending, yield, etc.
    "chains": List[str]
}
```

### 2.3 Edge Weights

Edge weight w(p, s) represents the strength of dependency:

```
w(p, s) = α * absolute_exposure + β * relative_exposure

where:
    absolute_exposure = E[p][s]  # USD value
    relative_exposure = E[p][s] / TVL[p]  # percentage of TVL
    α, β = weighting parameters (default: α=0.5, β=0.5)
```

### 2.4 Graph Construction Algorithm

```python
def build_dependency_graph(stablecoins, protocols, exposures):
    G = nx.DiGraph()

    # Add stablecoin nodes
    for s in stablecoins:
        G.add_node(s.symbol, **s.attributes)

    # Add protocol nodes
    for p in protocols:
        G.add_node(p.name, **p.attributes)

    # Add exposure edges
    for e in exposures:
        weight = calculate_edge_weight(e)
        G.add_edge(e.protocol, e.stablecoin, weight=weight, **e.attributes)

    return G
```

---

## 3. Risk Metrics

### 3.1 Centrality Metrics

**Degree Centrality:**
```
DC(v) = degree(v) / (|V| - 1)
```
Measures direct connections; high DC stablecoins are widely used.

**Betweenness Centrality:**
```
BC(v) = Σ (σ_st(v) / σ_st) for all s≠v≠t
```
Measures how often a node lies on shortest paths; identifies chokepoints.

**PageRank:**
```
PR(v) = (1-d)/|V| + d * Σ PR(u)/out_degree(u) for all u→v
```
Measures influence propagation; identifies systemically important nodes.

**Eigenvector Centrality:**
```
EC(v) = (1/λ) * Σ EC(u) for all u adjacent to v
```
Measures connection to other well-connected nodes.

### 3.2 Blast Radius

The blast radius quantifies the potential impact of a single stablecoin depeg:

```
BlastRadius(s) = Σ TVL[p] * Vulnerability[p][s] for all protocols p

where:
    Vulnerability[p][s] = min(1, E[p][s] / (TVL[p] * threshold))
```

**Interpretation:**
- Higher blast radius = more TVL at risk
- Vulnerability capped at 1.0 (complete failure)
- Threshold determines sensitivity (default: 0.1 = 10% TVL)

### 3.3 Contagion Index

The contagion index measures a stablecoin's potential to trigger cascades:

```
ContagionIndex(s) = w1*BC(s) + w2*PR(s) + w3*SecondOrderExposure(s)

where:
    SecondOrderExposure(s) = Σ exposure(p,s) * Σ exposure(p,s') for s'≠s
```

**Interpretation:**
- Combines network position with cascade potential
- Higher index = more likely to trigger chain reactions

### 3.4 Concentration Risk (HHI)

Protocol-level concentration using Herfindahl-Hirschman Index:

```
HHI(p) = Σ (E[p][s] / TotalExposure[p])² for all stablecoins s
```

**Interpretation:**
- HHI = 1.0: Single stablecoin exposure (maximum concentration)
- HHI → 0: Well-diversified across many stablecoins
- Threshold: HHI > 0.25 considered concentrated

### 3.5 Value at Risk (VaR)

Probabilistic loss estimation using Monte Carlo simulation:

```
VaR_α = Percentile(Losses, 1-α)
CVaR_α = E[Loss | Loss > VaR_α]
```

Where losses are simulated across scenarios with varying:
- Trigger stablecoin
- Initial severity
- Market conditions

---

## 4. Agent-Based Simulation Model

### 4.1 Agent Types

**StablecoinAgent:**
```
State: {price, peg, confidence, is_depegged}

Behavior:
    - Price follows confidence with noise
    - Confidence decays under selling pressure
    - Algorithmic coins have death spiral dynamics
    - Depeg triggers when price < (peg - threshold)
```

**ProtocolAgent:**
```
State: {tvl, stablecoin_holdings, is_distressed}

Behavior:
    - Monitor exposure to depegged stablecoins
    - Trigger liquidations when exposure > threshold
    - Reduce TVL proportionally to losses
    - Mark distressed when TVL loss > distress_threshold
```

**LiquidatorAgent:**
```
State: {capital, profit}

Behavior:
    - Monitor distressed protocols
    - Execute liquidations for profit
    - Apply market impact on stablecoin prices
```

**ArbitragerAgent:**
```
State: {capital}

Behavior:
    - Detect price deviations from peg
    - Execute arbitrage (stabilizing force)
    - Limited by capital and market depth
```

### 4.2 Environment Dynamics

Each simulation step:

```python
def step(self):
    # 1. Update stablecoin prices based on confidence
    for stablecoin in self.stablecoins:
        stablecoin.update_price()

    # 2. Protocols react to price changes
    for protocol in self.protocols:
        protocol.assess_exposure()
        protocol.trigger_liquidations()

    # 3. Liquidators execute opportunities
    for liquidator in self.liquidators:
        liquidator.find_and_execute()

    # 4. Arbitrageurs stabilize prices
    for arb in self.arbitrageurs:
        arb.arbitrage()

    # 5. Record metrics
    self.datacollector.collect(self)
```

### 4.3 Cascade Propagation

```
When stablecoin S depegs:
    1. Direct impact: Protocols with S exposure lose value
    2. Liquidations: Undercollateralized positions liquidated
    3. Confidence spillover: Related stablecoins lose confidence
    4. Second-order effects: Affected protocols may fail
    5. Feedback loop: Protocol failures reduce stablecoin backing
```

### 4.4 Stopping Conditions

Simulation terminates when:
- Maximum steps reached
- System reaches equilibrium (no state changes for N steps)
- All stablecoins stabilized (prices within threshold of peg)
- Catastrophic failure (>50% of TVL lost)

---

## 5. Historical Validation Methodology

### 5.1 Event Selection

Events selected based on:
1. Significant price deviation (>3% from peg)
2. Duration >1 hour
3. Documented impact on DeFi protocols
4. Sufficient data availability

### 5.2 Validation Process

```
For each historical event E:
    1. Reconstruct state at time T-1 (before event)
    2. Initialize simulation with historical state
    3. Trigger depeg with actual initial severity
    4. Run simulation
    5. Compare predicted vs. actual:
        - Protocols affected
        - TVL losses
        - Cascade timeline
        - Secondary depegs
```

### 5.3 Accuracy Metrics

**Protocol Prediction Accuracy:**
```
Accuracy = |PredictedAffected ∩ ActualAffected| / |ActualAffected|
```

**TVL Loss Error:**
```
MAPE = |PredictedLoss - ActualLoss| / ActualLoss * 100
```

**Timeline Correlation:**
```
Correlation(predicted_timeline, actual_timeline)
```

### 5.4 Cross-Validation

- Leave-one-out: Train on N-1 events, test on 1
- Parameter sensitivity: Vary key parameters ±20%
- Bootstrap: Resample simulation runs for confidence intervals

---

## 6. Early Warning System

### 6.1 Indicators

| Indicator | Calculation | Warning Threshold |
|-----------|-------------|-------------------|
| Price Deviation | \|price - peg\| / peg | > 0.5% |
| Volume Spike | volume / MA(volume, 7d) | > 3.0x |
| Pool Imbalance | max(ratio) / min(ratio) | > 1.5 |
| Redemption Rate | redemptions / supply | > 1% daily |
| Funding Rate | perp funding rate | < -0.1% |
| Social Sentiment | NLP sentiment score | < -0.5 |

### 6.2 Composite Score

```
WarningScore = Σ w_i * normalize(indicator_i) * severity_i

where:
    w_i = indicator weight (learned or manual)
    normalize = min-max normalization
    severity_i = how concerning the current value is
```

### 6.3 Alert Levels

| Score | Level | Action |
|-------|-------|--------|
| 0-0.3 | Normal | Monitor |
| 0.3-0.5 | Elevated | Increase monitoring frequency |
| 0.5-0.7 | High | Prepare contingency plans |
| 0.7-1.0 | Critical | Immediate action required |

---

## 7. Simulation Configuration

### 7.1 Default Parameters

```python
DEFAULT_CONFIG = {
    # Depeg thresholds
    "depeg_threshold": 0.02,        # 2% from peg
    "severe_depeg_threshold": 0.10,  # 10% from peg

    # Confidence dynamics
    "confidence_decay_rate": 0.1,    # Per step under pressure
    "confidence_recovery_rate": 0.05, # Per step when stable

    # Market dynamics
    "noise_std": 0.005,              # Price noise standard deviation
    "market_impact": 0.001,          # Impact per $1M traded

    # Algorithmic coins
    "death_spiral_factor": 0.9,      # Severity multiplier for algo coins

    # Simulation
    "max_steps": 100,
    "equilibrium_threshold": 5,      # Steps without change
}
```

### 7.2 Scenario Parameters

Predefined scenarios vary:
- Trigger stablecoin
- Initial severity (0.01 to 0.50)
- Market stress level (1.0 to 3.0)
- Recovery probability (0.0 to 1.0)

### 7.3 Monte Carlo Configuration

```python
MONTE_CARLO_CONFIG = {
    "n_runs": 1000,
    "seed_range": (0, 100000),
    "confidence_intervals": [0.90, 0.95, 0.99],
    "output_metrics": ["tvl_loss", "depegged_count", "steps_to_equilibrium"]
}
```

---

## 8. Reproducibility

### 8.1 Random Seeds

All stochastic components use seeded RNGs:
- Simulation: Mesa model seed
- Monte Carlo: Incrementing seeds from base
- Bootstrapping: Fixed seed for reproducibility

### 8.2 Data Versioning

- Raw data timestamped at collection
- Processed data includes provenance metadata
- Configuration files version controlled

### 8.3 Code Versioning

- Git commit hash recorded in output
- Dependency versions locked in requirements.txt
- Docker container for exact environment reproduction
