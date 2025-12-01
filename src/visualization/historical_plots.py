"""Historical event analysis visualization."""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger


class HistoricalPlotter:
    """Visualize historical depeg events and validation results."""

    def __init__(self):
        """Initialize historical plotter."""
        self.event_colors = {
            "terra_ust": "#e74c3c",
            "usdc_svb": "#3498db",
            "susd_2025": "#9b59b6",
            "nov_2025_cascade": "#e67e22"
        }

    def plot_historical_event(
        self,
        event_data: Dict[str, Any],
        price_history: Optional[pd.DataFrame] = None,
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot detailed visualization of a historical depeg event.

        Args:
            event_data: DepegEvent data as dict
            price_history: Optional price history DataFrame
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        event_date = datetime.fromisoformat(event_data["date"]) if isinstance(
            event_data["date"], str) else event_data["date"]

        # 1. Price trajectory (if available)
        ax1 = axes[0, 0]
        if price_history is not None and len(price_history) > 0:
            ax1.plot(price_history.index, price_history["price"],
                     color="#3498db", linewidth=2)
            ax1.axhline(y=1.0, color="#95a5a6", linestyle="--", label="Peg")
            ax1.axhline(y=event_data["low_price"], color="#e74c3c",
                        linestyle=":", label=f"Low: ${event_data['low_price']:.4f}")
            ax1.axvline(x=event_date, color="#e67e22", linestyle="-.",
                        label="Event Date")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price ($)")
            ax1.set_title(f"{event_data['stablecoin']} Price During Event")
            ax1.legend()
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        else:
            ax1.text(0.5, 0.5, "Price history not available",
                     ha="center", va="center", fontsize=12)
            ax1.set_title(f"{event_data['stablecoin']} Price (No Data)")

        # 2. Severity gauge
        ax2 = axes[0, 1]
        self._plot_severity_gauge(ax2, event_data["max_deviation"],
                                  event_data.get("severity", "unknown"))

        # 3. Affected entities
        ax3 = axes[1, 0]
        affected = event_data.get("affected_protocols", [])
        cascade = event_data.get("cascade_effects", [])

        entities = affected + [c.get("affected_entity", "Unknown") for c in cascade]
        entity_types = ["Protocol"] * len(affected) + [
            c.get("entity_type", "unknown").title() for c in cascade
        ]

        if entities:
            colors = ["#3498db" if t == "Protocol" else "#e67e22" for t in entity_types]
            y_pos = np.arange(len(entities))
            ax3.barh(y_pos, [1] * len(entities), color=colors, alpha=0.7)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(entities)
            ax3.set_title("Affected Entities")
            ax3.legend([
                plt.Rectangle((0, 0), 1, 1, color="#3498db"),
                plt.Rectangle((0, 0), 1, 1, color="#e67e22")
            ], ["Protocol", "Stablecoin"])
        else:
            ax3.text(0.5, 0.5, "No affected entities recorded",
                     ha="center", va="center")

        # 4. Event details
        ax4 = axes[1, 1]
        ax4.axis("off")

        details_text = f"""
Historical Depeg Event Analysis
===============================

Event: {event_data.get('event_id', 'Unknown')}
Stablecoin: {event_data['stablecoin']}
Date: {event_date.strftime('%Y-%m-%d')}

Impact:
  Low Price: ${event_data['low_price']:.4f}
  Max Deviation: {event_data['max_deviation']*100:.1f}%
  Severity: {event_data.get('severity', 'Unknown')}
  Duration: {event_data.get('duration_hours', 0):.0f} hours
  Total Loss: ${event_data.get('total_loss_usd', 0):,.0f}

Cause: {event_data.get('cause', 'Unknown')}

Lessons Learned:
{chr(10).join('  • ' + l for l in event_data.get('lessons', ['None recorded']))}
        """

        ax4.text(0.02, 0.98, details_text, transform=ax4.transAxes,
                 fontsize=9, verticalalignment="top", fontfamily="monospace",
                 bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

        plt.suptitle(f"Historical Event: {event_data.get('event_id', 'Unknown')}",
                     fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def _plot_severity_gauge(
        self,
        ax: plt.Axes,
        deviation: float,
        severity: str
    ):
        """Plot severity gauge."""
        ax.set_aspect("equal")

        # Gauge segments
        segments = [
            (0, 0.05, "#2ecc71", "Minor"),
            (0.05, 0.20, "#f1c40f", "Moderate"),
            (0.20, 0.50, "#e67e22", "Severe"),
            (0.50, 1.0, "#e74c3c", "Catastrophic")
        ]

        for start, end, color, label in segments:
            theta_start = np.pi * (1 - end)
            theta_end = np.pi * (1 - start)
            theta = np.linspace(theta_start, theta_end, 50)

            ax.fill_between(np.cos(theta), 0, np.sin(theta),
                            color=color, alpha=0.7)

        # Needle
        clamped_dev = min(deviation, 1.0)
        needle_angle = np.pi * (1 - clamped_dev)
        ax.arrow(0, 0, 0.7 * np.cos(needle_angle), 0.7 * np.sin(needle_angle),
                 head_width=0.05, head_length=0.03, fc="#2c3e50", ec="#2c3e50")

        # Center
        circle = plt.Circle((0, 0), 0.08, color="#2c3e50")
        ax.add_patch(circle)

        ax.text(0, -0.25, f"Deviation: {deviation*100:.1f}%",
                ha="center", fontsize=11, fontweight="bold")
        ax.text(0, -0.4, f"Severity: {severity}",
                ha="center", fontsize=10)

        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-0.5, 1.1)
        ax.axis("off")
        ax.set_title("Depeg Severity")

    def plot_event_comparison(
        self,
        events: List[Dict],
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Compare multiple historical events.

        Args:
            events: List of event data dicts
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # Extract data
        names = [e.get("event_id", "Unknown") for e in events]
        stables = [e.get("stablecoin", "?") for e in events]
        deviations = [e.get("max_deviation", 0) for e in events]
        losses = [e.get("total_loss_usd", 0) for e in events]
        durations = [e.get("duration_hours", 0) for e in events]
        affected = [len(e.get("affected_protocols", [])) for e in events]

        x = np.arange(len(events))
        colors = [self.event_colors.get(n, "#3498db") for n in names]

        # 1. Deviation comparison
        ax1 = axes[0, 0]
        ax1.bar(x, [d * 100 for d in deviations], color=colors, alpha=0.8)
        ax1.set_xticks(x)
        ax1.set_xticklabels(stables, rotation=45, ha="right")
        ax1.set_ylabel("Max Deviation (%)")
        ax1.set_title("Depeg Severity Comparison")
        ax1.axhline(y=2, color="#f1c40f", linestyle="--", alpha=0.7, label="2% threshold")
        ax1.legend()

        # 2. Total losses
        ax2 = axes[0, 1]
        ax2.bar(x, [l / 1e9 for l in losses], color=colors, alpha=0.8)
        ax2.set_xticks(x)
        ax2.set_xticklabels(stables, rotation=45, ha="right")
        ax2.set_ylabel("Total Loss ($ Billion)")
        ax2.set_title("Financial Impact Comparison")

        # 3. Duration
        ax3 = axes[1, 0]
        ax3.bar(x, [d / 24 for d in durations], color=colors, alpha=0.8)
        ax3.set_xticks(x)
        ax3.set_xticklabels(stables, rotation=45, ha="right")
        ax3.set_ylabel("Duration (Days)")
        ax3.set_title("Event Duration Comparison")

        # 4. Affected protocols
        ax4 = axes[1, 1]
        ax4.bar(x, affected, color=colors, alpha=0.8)
        ax4.set_xticks(x)
        ax4.set_xticklabels(stables, rotation=45, ha="right")
        ax4.set_ylabel("Number of Protocols")
        ax4.set_title("Affected Protocols Comparison")

        plt.suptitle("Historical Depeg Event Comparison", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_validation_results(
        self,
        validation_df: pd.DataFrame,
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot model validation results.

        Args:
            validation_df: DataFrame from HistoricalValidator
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # 1. Actual vs Predicted TVL Loss
        ax1 = axes[0, 0]
        ax1.scatter(validation_df["actual_tvl_loss"],
                    validation_df["predicted_tvl_loss"],
                    c="#3498db", s=100, alpha=0.7)

        # Add perfect prediction line
        max_val = max(validation_df["actual_tvl_loss"].max(),
                      validation_df["predicted_tvl_loss"].max())
        ax1.plot([0, max_val], [0, max_val], "r--", label="Perfect Prediction")

        # Label points
        for i, row in validation_df.iterrows():
            ax1.annotate(row["stablecoin"],
                         (row["actual_tvl_loss"], row["predicted_tvl_loss"]),
                         fontsize=8)

        ax1.set_xlabel("Actual TVL Loss ($)")
        ax1.set_ylabel("Predicted TVL Loss ($)")
        ax1.set_title("TVL Loss: Actual vs Predicted")
        ax1.legend()

        # 2. Error distribution
        ax2 = axes[0, 1]
        errors = ["tvl_loss_error", "protocol_count_error", "cascade_error"]
        error_labels = ["TVL Loss", "Protocol Count", "Cascade"]

        available_errors = [e for e in errors if e in validation_df.columns]
        error_data = [validation_df[e].dropna().values for e in available_errors]

        if error_data:
            bp = ax2.boxplot(error_data, labels=[error_labels[errors.index(e)]
                                                  for e in available_errors])
            ax2.axhline(y=0.5, color="#e67e22", linestyle="--",
                        label="50% Error Threshold")
            ax2.set_ylabel("Relative Error")
            ax2.set_title("Prediction Error Distribution")
            ax2.legend()

        # 3. Accuracy by event
        ax3 = axes[1, 0]
        if "overall_accuracy" in validation_df.columns:
            events = validation_df["event_id"]
            accuracies = validation_df["overall_accuracy"]

            colors = ["#2ecc71" if a > 0.7 else "#f1c40f" if a > 0.5
                      else "#e74c3c" for a in accuracies]

            ax3.barh(events, accuracies, color=colors, alpha=0.8)
            ax3.axvline(x=0.7, color="#2ecc71", linestyle="--", label="Good (70%)")
            ax3.axvline(x=0.5, color="#f1c40f", linestyle="--", label="Acceptable (50%)")
            ax3.set_xlabel("Accuracy")
            ax3.set_title("Model Accuracy by Event")
            ax3.legend()
            ax3.set_xlim(0, 1)

        # 4. Summary statistics
        ax4 = axes[1, 1]
        ax4.axis("off")

        if "overall_accuracy" in validation_df.columns:
            summary_text = f"""
Model Validation Summary
========================

Events Validated: {len(validation_df)}

Overall Accuracy:
  Mean: {validation_df['overall_accuracy'].mean():.1%}
  Min: {validation_df['overall_accuracy'].min():.1%}
  Max: {validation_df['overall_accuracy'].max():.1%}

Error Analysis:
  TVL Loss Error: {validation_df['tvl_loss_error'].mean():.1%} (avg)
  Protocol Error: {validation_df['protocol_count_error'].mean():.1%} (avg)
  Cascade Error: {validation_df['cascade_error'].mean():.1%} (avg)

Best Predicted Event:
  {validation_df.loc[validation_df['overall_accuracy'].idxmax(), 'event_id']}
  ({validation_df['overall_accuracy'].max():.1%} accuracy)

Worst Predicted Event:
  {validation_df.loc[validation_df['overall_accuracy'].idxmin(), 'event_id']}
  ({validation_df['overall_accuracy'].min():.1%} accuracy)
            """
        else:
            summary_text = "Validation data not available"

        ax4.text(0.02, 0.98, summary_text, transform=ax4.transAxes,
                 fontsize=9, verticalalignment="top", fontfamily="monospace",
                 bbox=dict(boxstyle="round", facecolor="lightcyan", alpha=0.8))

        plt.suptitle("Model Validation Results", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_timeline_of_events(
        self,
        events: List[Dict],
        figsize: Tuple[int, int] = (16, 6),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot timeline of historical depeg events.

        Args:
            events: List of event data dicts
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Sort events by date
        sorted_events = sorted(events,
                               key=lambda x: datetime.fromisoformat(x["date"])
                               if isinstance(x["date"], str) else x["date"])

        dates = [datetime.fromisoformat(e["date"]) if isinstance(e["date"], str)
                 else e["date"] for e in sorted_events]
        stables = [e["stablecoin"] for e in sorted_events]
        deviations = [e.get("max_deviation", 0) for e in sorted_events]
        losses = [e.get("total_loss_usd", 0) for e in sorted_events]

        # Create timeline
        ax.scatter(dates, [0] * len(dates), s=[max(l / 1e8, 100) for l in losses],
                   c=[d for d in deviations], cmap="Reds", alpha=0.7, edgecolors="black")

        # Add labels
        for i, (date, stable, dev, loss) in enumerate(zip(dates, stables, deviations, losses)):
            y_offset = 0.15 if i % 2 == 0 else -0.15
            ax.annotate(
                f"{stable}\n{dev*100:.0f}%\n${loss/1e9:.1f}B",
                (date, 0),
                xytext=(0, 40 if y_offset > 0 else -40),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                arrowprops=dict(arrowstyle="-", color="gray", alpha=0.5)
            )

        ax.axhline(y=0, color="#2c3e50", linewidth=2)
        ax.set_ylim(-0.5, 0.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.set_xlabel("Date")
        ax.set_title("Timeline of Historical Depeg Events")

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap="Reds",
                                    norm=plt.Normalize(0, max(deviations)))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation="horizontal", pad=0.15)
        cbar.set_label("Max Deviation from Peg")

        ax.get_yaxis().set_visible(False)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig
