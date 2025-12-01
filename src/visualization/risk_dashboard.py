"""Risk dashboard visualization."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class RiskDashboard:
    """Create risk assessment dashboards."""

    RISK_COLORS = {
        "LOW": "#2ecc71",
        "MEDIUM": "#f1c40f",
        "HIGH": "#e67e22",
        "CRITICAL": "#e74c3c"
    }

    def __init__(self):
        """Initialize risk dashboard."""
        pass

    def create_risk_summary_dashboard(
        self,
        stablecoin_risks: pd.DataFrame,
        protocol_risks: pd.DataFrame,
        ecosystem_risk: Dict[str, Any],
        figsize: Tuple[int, int] = (16, 12),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create comprehensive risk summary dashboard.

        Args:
            stablecoin_risks: DataFrame from RiskCalculator
            protocol_risks: Protocol risk DataFrame
            ecosystem_risk: Ecosystem-wide risk metrics
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig = plt.figure(figsize=figsize)

        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # 1. Stablecoin Risk Scores
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_risk_bars(ax1, stablecoin_risks, "symbol", "Stablecoin Risk Scores")

        # 2. Risk Level Distribution (Pie)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_risk_distribution(ax2, stablecoin_risks)

        # 3. Risk Component Breakdown
        ax3 = fig.add_subplot(gs[1, :2])
        self._plot_risk_components(ax3, stablecoin_risks)

        # 4. Ecosystem Risk Gauge
        ax4 = fig.add_subplot(gs[1, 2])
        self._plot_risk_gauge(ax4, ecosystem_risk.get("overall_ecosystem_risk", 0))

        # 5. Top Protocol Risks
        ax5 = fig.add_subplot(gs[2, :2])
        if len(protocol_risks) > 0:
            self._plot_risk_bars(ax5, protocol_risks.head(10), "protocol", "Top Protocol Risks")

        # 6. Risk Summary Text
        ax6 = fig.add_subplot(gs[2, 2])
        self._plot_risk_summary(ax6, ecosystem_risk)

        plt.suptitle("DepegScope Risk Dashboard", fontsize=16, fontweight="bold")

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Dashboard saved to {save_path}")

        return fig

    def _plot_risk_bars(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        name_col: str,
        title: str
    ):
        """Plot horizontal risk score bars."""
        df_sorted = df.sort_values("composite_score", ascending=True).tail(10)

        colors = [self.RISK_COLORS.get(level, "#95a5a6")
                  for level in df_sorted["risk_level"]]

        ax.barh(df_sorted[name_col], df_sorted["composite_score"],
                color=colors, edgecolor="white", linewidth=0.5)

        ax.set_xlabel("Composite Risk Score")
        ax.set_title(title)
        ax.set_xlim(0, 1)

        # Add risk level labels
        for i, (score, level) in enumerate(
            zip(df_sorted["composite_score"], df_sorted["risk_level"])
        ):
            ax.text(score + 0.02, i, level, va="center", fontsize=8)

    def _plot_risk_distribution(self, ax: plt.Axes, df: pd.DataFrame):
        """Plot risk level distribution pie chart."""
        risk_counts = df["risk_level"].value_counts()

        colors = [self.RISK_COLORS.get(level, "#95a5a6") for level in risk_counts.index]

        ax.pie(risk_counts.values, labels=risk_counts.index,
               colors=colors, autopct="%1.0f%%", startangle=90)
        ax.set_title("Risk Distribution")

    def _plot_risk_components(self, ax: plt.Axes, df: pd.DataFrame):
        """Plot stacked bar chart of risk components."""
        components = ["concentration_risk", "liquidity_risk", "contagion_risk",
                      "collateral_risk", "mechanism_risk"]

        available_components = [c for c in components if c in df.columns]

        df_top = df.head(10)
        x = np.arange(len(df_top))
        width = 0.15

        colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]

        for i, (comp, color) in enumerate(zip(available_components, colors)):
            ax.bar(x + i * width, df_top[comp], width, label=comp.replace("_", " ").title(),
                   color=color, alpha=0.8)

        ax.set_xlabel("Stablecoin")
        ax.set_ylabel("Risk Score")
        ax.set_title("Risk Component Breakdown")
        ax.set_xticks(x + width * len(available_components) / 2)
        ax.set_xticklabels(df_top["symbol"], rotation=45, ha="right")
        ax.legend(loc="upper right", fontsize=8)
        ax.set_ylim(0, 1)

    def _plot_risk_gauge(self, ax: plt.Axes, risk_score: float):
        """Plot risk gauge."""
        ax.set_aspect("equal")

        # Draw gauge background
        theta = np.linspace(0, np.pi, 100)
        for i, (start, end, color) in enumerate([
            (0, 0.25, "#2ecc71"),
            (0.25, 0.5, "#f1c40f"),
            (0.5, 0.75, "#e67e22"),
            (0.75, 1.0, "#e74c3c")
        ]):
            theta_start = np.pi * (1 - end)
            theta_end = np.pi * (1 - start)
            theta_segment = np.linspace(theta_start, theta_end, 25)

            ax.fill_between(
                np.cos(theta_segment), 0, np.sin(theta_segment),
                color=color, alpha=0.7
            )

        # Draw needle
        needle_angle = np.pi * (1 - risk_score)
        ax.arrow(0, 0, 0.8 * np.cos(needle_angle), 0.8 * np.sin(needle_angle),
                 head_width=0.05, head_length=0.03, fc="#2c3e50", ec="#2c3e50")

        # Add center circle
        circle = plt.Circle((0, 0), 0.1, color="#2c3e50")
        ax.add_patch(circle)

        # Add label
        ax.text(0, -0.3, f"Risk Score: {risk_score:.2f}",
                ha="center", fontsize=12, fontweight="bold")

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.5, 1.2)
        ax.axis("off")
        ax.set_title("Ecosystem Risk Level")

    def _plot_risk_summary(self, ax: plt.Axes, ecosystem_risk: Dict):
        """Plot risk summary text."""
        ax.axis("off")

        high_risk_stables = ecosystem_risk.get("high_risk_stablecoins", [])
        high_risk_protocols = ecosystem_risk.get("high_risk_protocols", [])

        summary_text = f"""
Risk Summary
============

Overall Ecosystem Risk:
  Score: {ecosystem_risk.get('overall_ecosystem_risk', 0):.2f}

Stablecoin Risk:
  Average: {ecosystem_risk.get('avg_stablecoin_risk', 0):.2f}
  Maximum: {ecosystem_risk.get('max_stablecoin_risk', 0):.2f}
  Weighted: {ecosystem_risk.get('weighted_stablecoin_risk', 0):.2f}

Protocol Risk:
  Average: {ecosystem_risk.get('avg_protocol_risk', 0):.2f}
  Maximum: {ecosystem_risk.get('max_protocol_risk', 0):.2f}

High Risk Entities:
  Stablecoins: {len(high_risk_stables)}
  Protocols: {len(high_risk_protocols)}
        """

        ax.text(0.05, 0.95, summary_text, transform=ax.transAxes,
                fontsize=9, verticalalignment="top", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    def create_interactive_dashboard(
        self,
        stablecoin_risks: pd.DataFrame,
        protocol_risks: pd.DataFrame,
        ecosystem_risk: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Create interactive Plotly dashboard.

        Args:
            stablecoin_risks: Stablecoin risk DataFrame
            protocol_risks: Protocol risk DataFrame
            ecosystem_risk: Ecosystem risk metrics
            save_path: Path to save HTML

        Returns:
            Plotly Figure or None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for interactive dashboard")
            return None

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Stablecoin Risk Scores",
                "Risk Distribution",
                "Risk Components",
                "Top Protocol Risks"
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )

        # Stablecoin Risk Bars
        fig.add_trace(
            go.Bar(
                x=stablecoin_risks["symbol"],
                y=stablecoin_risks["composite_score"],
                marker_color=[self.RISK_COLORS.get(l, "#95a5a6")
                              for l in stablecoin_risks["risk_level"]],
                name="Risk Score"
            ),
            row=1, col=1
        )

        # Risk Distribution Pie
        risk_counts = stablecoin_risks["risk_level"].value_counts()
        fig.add_trace(
            go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                marker_colors=[self.RISK_COLORS.get(l, "#95a5a6")
                               for l in risk_counts.index]
            ),
            row=1, col=2
        )

        # Risk Components
        for col in ["concentration_risk", "contagion_risk", "mechanism_risk"]:
            if col in stablecoin_risks.columns:
                fig.add_trace(
                    go.Bar(
                        x=stablecoin_risks["symbol"],
                        y=stablecoin_risks[col],
                        name=col.replace("_", " ").title()
                    ),
                    row=2, col=1
                )

        # Protocol Risks
        if len(protocol_risks) > 0:
            top_protocols = protocol_risks.head(10)
            fig.add_trace(
                go.Bar(
                    x=top_protocols["protocol"],
                    y=top_protocols["composite_score"],
                    marker_color=[self.RISK_COLORS.get(l, "#95a5a6")
                                  for l in top_protocols["risk_level"]],
                    name="Protocol Risk"
                ),
                row=2, col=2
            )

        fig.update_layout(
            title_text="DepegScope Interactive Risk Dashboard",
            height=800,
            showlegend=True
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"Interactive dashboard saved to {save_path}")

        return fig

    def create_early_warning_dashboard(
        self,
        warning_data: Dict[str, Any],
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create early warning system dashboard.

        Args:
            warning_data: Warning check results
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        signals = warning_data.get("signals", [])

        # Signal status overview
        ax1 = axes[0, 0]
        indicators = [s["indicator"] for s in signals]
        values = [s["value"] for s in signals]
        thresholds = [s["threshold"] for s in signals]
        colors = [self.RISK_COLORS.get(s["severity"], "#95a5a6") for s in signals]

        x = np.arange(len(indicators))
        width = 0.35

        ax1.bar(x - width / 2, values, width, label="Current Value", color=colors, alpha=0.8)
        ax1.bar(x + width / 2, thresholds, width, label="Threshold",
                color="#95a5a6", alpha=0.5, hatch="//")

        ax1.set_xticks(x)
        ax1.set_xticklabels([i.replace("_", "\n") for i in indicators], fontsize=8)
        ax1.set_ylabel("Value")
        ax1.set_title("Early Warning Indicators")
        ax1.legend()

        # Severity summary
        ax2 = axes[0, 1]
        severity_counts = {}
        for s in signals:
            sev = s["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        if severity_counts:
            ax2.pie(
                severity_counts.values(),
                labels=severity_counts.keys(),
                colors=[self.RISK_COLORS.get(s, "#95a5a6") for s in severity_counts.keys()],
                autopct="%1.0f%%",
                startangle=90
            )
        ax2.set_title("Severity Distribution")

        # Warning status
        ax3 = axes[1, 0]
        ax3.axis("off")

        status_text = f"""
Early Warning Status
====================

Stablecoin: {warning_data.get('stablecoin', 'N/A')}
Timestamp: {warning_data.get('timestamp', 'N/A')}

Total Warnings: {warning_data.get('total_warnings', 0)}
Overall Severity: {warning_data.get('overall_severity', 'N/A')}

Warning Indicators:
{chr(10).join('  - ' + i for i in warning_data.get('warning_indicators', []))}

Recommendation:
{warning_data.get('recommendation', 'N/A')}
        """

        ax3.text(0.05, 0.95, status_text, transform=ax3.transAxes,
                 fontsize=10, verticalalignment="top", fontfamily="monospace",
                 bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

        # Signal details
        ax4 = axes[1, 1]
        ax4.axis("off")

        detail_text = "Signal Details\n" + "=" * 40 + "\n\n"
        for s in signals:
            status = "⚠️" if s["warning"] else "✓"
            detail_text += f"{status} {s['indicator']}: {s['value']:.4f}\n"
            detail_text += f"   Threshold: {s['threshold']:.4f}\n"
            detail_text += f"   Severity: {s['severity']}\n\n"

        ax4.text(0.05, 0.95, detail_text, transform=ax4.transAxes,
                 fontsize=9, verticalalignment="top", fontfamily="monospace")

        plt.suptitle("Early Warning System Dashboard", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig
