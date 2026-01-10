# DepegScope: Academic Paper Structure

## Suggested Title Options

1. **"DepegScope: Quantifying Systemic Risk from Stablecoin Depeg Contagion in DeFi"**
2. **"Cascading Failures in Decentralized Finance: A Network Analysis of Stablecoin Dependencies"**
3. **"Measuring the Blast Radius: An Agent-Based Model for Stablecoin Depeg Propagation"**
4. **"Systemic Risk in DeFi: Network Topology and Contagion Dynamics of Stablecoin Depegs"**

---

## Paper Structure (8-12 pages for conference, 20+ for journal)

### Abstract (150-250 words)

**Structure:**
1. **Problem Statement** (1-2 sentences): The interconnected nature of DeFi creates systemic risk when stablecoins depeg
2. **Gap/Motivation** (1 sentence): Existing research lacks quantitative frameworks for measuring contagion dynamics
3. **Contribution** (2-3 sentences): Present DepegScope - a framework combining network analysis and agent-based modeling
4. **Method Summary** (1 sentence): Analyze dependency graphs, simulate cascades, validate against historical events
5. **Key Results** (2-3 sentences): Quantified findings (e.g., "USDT depeg would affect 73% of top-100 protocols")
6. **Implications** (1 sentence): Implications for risk management and DeFi design

**Example:**
> The explosive growth of decentralized finance (DeFi) has created a complex web of dependencies between protocols and stablecoins, raising concerns about systemic risk when stablecoins lose their peg. We present DepegScope, a comprehensive framework for quantifying stablecoin depeg contagion in DeFi ecosystems. Our approach combines dependency graph analysis to map protocol-stablecoin relationships with agent-based simulations to model cascade dynamics. We validate our model against three historical depeg events: Terra/UST (May 2022), USDC/SVB (March 2023), and the 2025 cascade events, achieving 87% accuracy in predicting affected protocols. Our analysis reveals that the top 5 stablecoins by market cap represent critical chokepoints, with USDT alone creating potential cascade paths affecting $47B in protocol TVL. These findings provide actionable insights for protocol risk management and highlight the need for diversification in DeFi architecture.

---

### 1. Introduction (1-1.5 pages)

**1.1 Opening Hook**
- Start with a concrete example (UST collapse: $60B lost in days)
- Establish the scale and importance of the problem

**1.2 Problem Context**
- Define stablecoins and their role in DeFi
- Explain what "depeg" means and its consequences
- Describe the interconnected nature of DeFi protocols

**1.3 Research Gap**
- Current literature focuses on individual stablecoin stability
- Lack of systemic analysis of cross-protocol contagion
- No validated simulation frameworks for depeg cascades

**1.4 Contributions** (Bulleted list)
1. A novel dependency graph model capturing stablecoin-protocol relationships
2. An agent-based simulation framework for cascade propagation
3. Risk metrics including "blast radius" and "contagion index"
4. Validation against 3+ historical depeg events
5. Open-source implementation for reproducibility

**1.5 Paper Organization**
- Brief roadmap of remaining sections

---

### 2. Background and Related Work (1.5-2 pages)

**2.1 Stablecoins in DeFi**
- Types: fiat-backed, crypto-backed, algorithmic
- Market overview and growth trajectory
- Role in DeFi primitives (lending, DEXes, yield farming)

**2.2 Historical Depeg Events**
- Terra/UST collapse (May 2022)
- USDC SVB crisis (March 2023)
- USDT concerns and short-term deviations
- Table summarizing events, causes, and impacts

**2.3 Related Work**
- **Systemic Risk in Traditional Finance**: Cite banking contagion literature (Allen & Gale, etc.)
- **DeFi Security Research**: Smart contract vulnerabilities, oracle manipulation
- **Stablecoin Analysis**: Individual stability mechanisms, reserve analysis
- **Network Analysis in Finance**: Interbank networks, counterparty risk
- **Agent-Based Financial Modeling**: Market simulations, flash crash models

**2.4 Gap Analysis**
- Why existing approaches are insufficient for DeFi contagion
- Unique challenges: composability, transparency, speed of propagation

---

### 3. System Model and Threat Model (1-1.5 pages)

**3.1 DeFi Ecosystem Model**
- Formal definition of protocols, stablecoins, and exposures
- Mathematical notation (G = (V, E) for dependency graph)
- Types of exposure relationships:
  - Collateral dependencies
  - Liquidity pool composition
  - Reserve backing
  - Oracle price feeds

**3.2 Threat Model**
- Depeg trigger scenarios:
  - Reserve insolvency
  - Bank run / confidence crisis
  - Algorithmic mechanism failure
  - External market shock
- Attacker capabilities (if applicable)
- Trust assumptions

**3.3 Cascade Propagation Model**
- How depeg spreads through dependencies
- Confidence decay mechanisms
- Liquidation cascades
- Feedback loops (death spirals)

---

### 4. DepegScope Framework (2-3 pages)

**4.1 Architecture Overview**
- Diagram of system components
- Data flow from collection to visualization

**4.2 Data Collection Pipeline**
- Data sources: DeFiLlama, CoinGecko, on-chain data
- Collection methodology and frequency
- Data validation and cleaning

**4.3 Dependency Graph Construction**
- Node types: stablecoins, protocols
- Edge types: exposure relationships with weights
- Graph construction algorithm
- Handling missing data and estimation

**4.4 Risk Metrics**
- **Centrality Metrics**: Degree, betweenness, PageRank
- **Blast Radius**: Potential cascade impact from single depeg
- **Contagion Index**: Measure of systemic interconnectedness
- **Concentration Risk (HHI)**: Protocol diversification measure
- **Value at Risk (VaR)**: Probabilistic loss estimation

**4.5 Agent-Based Simulation**
- Agent types and behaviors:
  - Stablecoin agents (price, confidence dynamics)
  - Protocol agents (exposure reactions, liquidations)
  - Market agents (arbitrageurs, liquidators)
- Environment model and step function
- Configurable parameters and scenarios

---

### 5. Methodology (1-1.5 pages)

**5.1 Data Collection**
- Time period: [specify dates]
- Sources and APIs used
- Dataset statistics: # stablecoins, # protocols, # exposures

**5.2 Experimental Setup**
- Hardware/software environment
- Simulation parameters and ranges
- Monte Carlo configuration (# runs, seeds)

**5.3 Validation Approach**
- Historical events used for validation
- Metrics for accuracy measurement
- Cross-validation methodology

**5.4 Ethical Considerations**
- Use of public blockchain data only
- Responsible disclosure of vulnerabilities found

---

### 6. Evaluation (2-3 pages)

**6.1 Dependency Graph Analysis**
- Graph statistics: density, clustering, diameter
- Centrality distribution analysis
- Key chokepoints identified
- Visualization of network topology

**6.2 Historical Validation**
- **Case Study 1: Terra/UST (May 2022)**
  - Simulation vs. actual affected protocols
  - Timeline comparison
  - Accuracy metrics

- **Case Study 2: USDC/SVB (March 2023)**
  - [Similar structure]

- **Case Study 3: 2025 Events**
  - [Similar structure]

**6.3 Scenario Analysis**
- Hypothetical depeg scenarios
- Monte Carlo simulation results
- Sensitivity analysis on key parameters

**6.4 Early Warning System Evaluation**
- Indicator performance on historical data
- Lead time analysis
- False positive/negative rates

**Table: Summary of Results**
| Metric | UST Event | SVB Event | 2025 Events |
|--------|-----------|-----------|-------------|
| Prediction Accuracy | X% | Y% | Z% |
| Protocols Affected | N | M | P |
| TVL Impact | $XB | $YB | $ZB |
| Lead Time | Xh | Yh | Zh |

---

### 7. Discussion (1-1.5 pages)

**7.1 Key Findings**
- Most significant discoveries
- Counterintuitive results
- Quantified risk concentrations

**7.2 Implications**
- For protocol developers: diversification recommendations
- For investors: risk assessment guidelines
- For regulators: systemic risk monitoring

**7.3 Limitations**
- Data availability and accuracy
- Model assumptions and simplifications
- Simulation fidelity vs. real-world complexity

**7.4 Future Work**
- Real-time monitoring system
- Cross-chain analysis
- Integration with governance mechanisms
- Machine learning for prediction

---

### 8. Conclusion (0.5 pages)

- Restate the problem and contribution
- Summarize key quantified findings
- Emphasize practical implications
- Call to action for the community

---

### References

- Aim for 30-50 references
- Include foundational DeFi papers, systemic risk literature, and recent empirical studies
- Follow venue-specific citation format

---

### Appendix (if space allows)

**A. Mathematical Proofs/Derivations**
- Formal definitions of risk metrics
- Convergence properties of simulation

**B. Additional Results**
- Extended tables and figures
- Sensitivity analysis details

**C. Implementation Details**
- Algorithm pseudocode
- Configuration parameters

---

## Key Figures to Include

1. **System Architecture Diagram** - Overview of DepegScope components
2. **Dependency Network Visualization** - Interactive or static graph
3. **Cascade Timeline** - How depeg spreads over time
4. **Historical Validation Plots** - Predicted vs. actual
5. **Risk Distribution Heatmap** - Protocol exposure concentrations
6. **Monte Carlo Results** - Loss distributions
7. **Early Warning Indicators** - Time series with events marked

---

## Writing Tips for Academic Publication

1. **Be Quantitative**: Every claim should have numbers backing it up
2. **Define Terms**: DeFi terminology may be unfamiliar to reviewers
3. **Reproducibility**: Emphasize open-source code and data availability
4. **Novelty**: Clearly articulate what's new vs. existing work
5. **Limitations**: Proactively address weaknesses
6. **Practical Impact**: Show real-world applicability
