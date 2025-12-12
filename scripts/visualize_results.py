#!/usr/bin/env python3
"""Visualize and analyze DepegScope results."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    # Find latest report
    reports_dir = Path('reports')
    report_files = list(reports_dir.glob('risk_report_*.json'))
    if not report_files:
        print("No report files found. Run generate_report.py first.")
        return

    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
    print(f"Loading: {latest_report}")

    with open(latest_report) as f:
        report = json.load(f)

    centrality = pd.read_csv('data/processed/centrality_metrics.csv')

    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('DepegScope Analysis Results', fontsize=16, fontweight='bold')

    # 1. Top Protocols by Exposure
    ax1 = axes[0, 0]
    top_protocols = centrality[centrality['type'] == 'protocol'].nlargest(10, 'in_degree_weighted')
    colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top_protocols)))
    ax1.barh(top_protocols['node'], top_protocols['in_degree_weighted'] / 1e6, color=colors)
    ax1.set_xlabel('Stablecoin Exposure ($ Millions)')
    ax1.set_title('Top 10 Protocols by Stablecoin Exposure')
    ax1.invert_yaxis()

    # 2. Risk Distribution
    ax2 = axes[0, 1]
    risks = pd.DataFrame(report['stablecoin_risks'])
    risk_counts = risks['risk_level'].value_counts()
    colors_pie = {'LOW': '#2ecc71', 'MEDIUM': '#f39c12', 'HIGH': '#e74c3c', 'CRITICAL': '#8e44ad'}
    pie_colors = [colors_pie.get(level, '#95a5a6') for level in risk_counts.index]
    ax2.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%', colors=pie_colors)
    ax2.set_title('Stablecoin Risk Distribution')

    # 3. Risk Components
    ax3 = axes[1, 0]
    top_risky = risks.nlargest(10, 'composite_score')[['symbol', 'liquidity_risk', 'mechanism_risk']]
    x = range(len(top_risky))
    width = 0.35
    ax3.bar([i - width/2 for i in x], top_risky['liquidity_risk'], width, label='Liquidity Risk', color='#3498db')
    ax3.bar([i + width/2 for i in x], top_risky['mechanism_risk'], width, label='Mechanism Risk', color='#e74c3c')
    ax3.set_xticks(x)
    ax3.set_xticklabels(top_risky['symbol'], rotation=45, ha='right')
    ax3.set_title('Risk Components by Stablecoin')
    ax3.set_ylabel('Risk Score')
    ax3.legend()

    # 4. Summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    summary = report['summary']
    text = f"""
    ECOSYSTEM SUMMARY
    ─────────────────────────────
    Stablecoins:        {summary['total_stablecoins']}
    Protocols:          {summary['total_protocols']}
    Exposures:          {summary['total_exposures']}

    Ecosystem Risk:     {summary['ecosystem_risk_score']:.3f}
    VaR (95%):          ${summary['var_95']:,.0f}
    CVaR (95%):         ${summary['cvar_95']:,.0f}
    """
    ax4.text(0.1, 0.7, text, transform=ax4.transAxes, fontsize=12,
             fontfamily='monospace', verticalalignment='top')

    plt.tight_layout()
    output_path = reports_dir / 'analysis_dashboard.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nDashboard saved to: {output_path}")

    # Print text analysis
    print("\n" + "="*60)
    print("DEPEGSCOPE ANALYSIS RESULTS")
    print("="*60)
    print(f"""
DATA SUMMARY
  • {summary['total_stablecoins']} stablecoins analyzed
  • {summary['total_protocols']} DeFi protocols mapped
  • {summary['total_exposures']} exposure relationships

TOP PROTOCOLS BY EXPOSURE""")
    for _, row in top_protocols.head(5).iterrows():
        print(f"  • {row['node']}: ${row['in_degree_weighted']/1e6:.1f}M")

    print(f"""
RISK DISTRIBUTION""")
    for level, count in risk_counts.items():
        print(f"  • {level}: {count} stablecoins")

    print(f"""
ECOSYSTEM METRICS
  • Risk Score: {summary['ecosystem_risk_score']:.3f}
  • VaR (95%): ${summary['var_95']:,.0f}
  • CVaR (95%): ${summary['cvar_95']:,.0f}

NOTES
  • Limited exposure data due to API rate limiting
  • Re-run with CoinGecko API key for complete analysis
""")

if __name__ == "__main__":
    main()
