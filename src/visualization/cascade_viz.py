"""Cascade and contagion visualization."""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class CascadeVisualizer:
    """Visualize cascade propagation and simulation results."""

    def __init__(self):
        """Initialize cascade visualizer."""
        self.colors = {
            "depegged": "#e74c3c",
            "distressed": "#e67e22",
            "healthy": "#2ecc71",
            "recovering": "#f1c40f"
        }

    def plot_simulation_timeline(
        self,
        simulation_history: pd.DataFrame,
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot simulation metrics over time.

        Args:
            simulation_history: DataFrame from simulation datacollector
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # Total TVL Lost
        ax1 = axes[0, 0]
        ax1.plot(simulation_history.index, simulation_history["Total_TVL_Lost"],
                 color="#e74c3c", linewidth=2)
        ax1.fill_between(simulation_history.index, 0, simulation_history["Total_TVL_Lost"],
                         alpha=0.3, color="#e74c3c")
        ax1.set_xlabel("Simulation Step")
        ax1.set_ylabel("TVL Lost ($)")
        ax1.set_title("Cumulative TVL Loss")
        ax1.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

        # Depegged Stablecoins
        ax2 = axes[0, 1]
        ax2.plot(simulation_history.index, simulation_history["Depegged_Stablecoins"],
                 color="#3498db", linewidth=2, marker="o", markersize=4)
        ax2.set_xlabel("Simulation Step")
        ax2.set_ylabel("Count")
        ax2.set_title("Depegged Stablecoins")
        ax2.set_ylim(bottom=0)

        # Distressed Protocols
        ax3 = axes[1, 0]
        ax3.plot(simulation_history.index, simulation_history["Distressed_Protocols"],
                 color="#e67e22", linewidth=2, marker="s", markersize=4)
        ax3.set_xlabel("Simulation Step")
        ax3.set_ylabel("Count")
        ax3.set_title("Distressed Protocols")
        ax3.set_ylim(bottom=0)

        # Average Stablecoin Price
        ax4 = axes[1, 1]
        ax4.plot(simulation_history.index, simulation_history["Average_Stablecoin_Price"],
                 color="#2ecc71", linewidth=2)
        ax4.axhline(y=1.0, color="#95a5a6", linestyle="--", label="Peg")
        ax4.axhline(y=0.98, color="#f1c40f", linestyle=":", label="Warning (2%)")
        ax4.set_xlabel("Simulation Step")
        ax4.set_ylabel("Price ($)")
        ax4.set_title("Average Stablecoin Price")
        ax4.legend()

        plt.suptitle("Contagion Simulation Timeline", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Timeline plot saved to {save_path}")

        return fig

    def plot_price_trajectories(
        self,
        stablecoin_states: List[Dict],
        figsize: Tuple[int, int] = (14, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot price trajectories for all stablecoins.

        Args:
            stablecoin_states: List of stablecoin state dicts with price_history
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        for state in stablecoin_states:
            symbol = state.get("symbol", "Unknown")
            prices = state.get("price_history", [1.0])

            color = "#e74c3c" if state.get("is_depegged", False) else "#2ecc71"
            alpha = 1.0 if state.get("is_depegged", False) else 0.6

            ax.plot(prices, label=symbol, color=color, alpha=alpha, linewidth=2)

        ax.axhline(y=1.0, color="#95a5a6", linestyle="--", linewidth=1)
        ax.axhline(y=0.98, color="#f1c40f", linestyle=":", alpha=0.7)
        ax.axhline(y=0.95, color="#e67e22", linestyle=":", alpha=0.7)

        ax.set_xlabel("Simulation Step")
        ax.set_ylabel("Price ($)")
        ax.set_title("Stablecoin Price Trajectories During Cascade")
        ax.legend(loc="lower left", ncol=3)
        ax.set_ylim(0, 1.1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_tvl_impact(
        self,
        protocol_states: List[Dict],
        top_n: int = 15,
        figsize: Tuple[int, int] = (12, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot TVL impact on protocols.

        Args:
            protocol_states: List of protocol state dicts
            top_n: Number of top affected protocols to show
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        # Sort by TVL lost
        sorted_protocols = sorted(
            protocol_states,
            key=lambda x: x.get("tvl_lost", 0),
            reverse=True
        )[:top_n]

        fig, ax = plt.subplots(figsize=figsize)

        names = [p.get("name", "Unknown") for p in sorted_protocols]
        initial_tvl = [p.get("initial_tvl", 0) for p in sorted_protocols]
        final_tvl = [p.get("tvl", 0) for p in sorted_protocols]
        tvl_lost = [p.get("tvl_lost", 0) for p in sorted_protocols]

        x = np.arange(len(names))
        width = 0.35

        bars1 = ax.bar(x - width / 2, initial_tvl, width, label="Initial TVL", color="#3498db", alpha=0.7)
        bars2 = ax.bar(x + width / 2, final_tvl, width, label="Final TVL", color="#2ecc71", alpha=0.7)

        # Add loss annotations
        for i, (init, final, loss) in enumerate(zip(initial_tvl, final_tvl, tvl_lost)):
            if loss > 0:
                loss_pct = (loss / init * 100) if init > 0 else 0
                ax.annotate(
                    f"-{loss_pct:.1f}%",
                    xy=(i, final),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color="#e74c3c"
                )

        ax.set_xlabel("Protocol")
        ax.set_ylabel("TVL ($)")
        ax.set_title("Protocol TVL Impact from Cascade")
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.legend()
        ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def plot_contagion_heatmap(
        self,
        contagion_matrix: pd.DataFrame,
        figsize: Tuple[int, int] = (12, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot heatmap of contagion effects.

        Args:
            contagion_matrix: Matrix of stablecoin -> protocol impact
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        import seaborn as sns

        fig, ax = plt.subplots(figsize=figsize)

        sns.heatmap(
            contagion_matrix,
            ax=ax,
            cmap="YlOrRd",
            annot=True,
            fmt=".2f",
            linewidths=0.5,
            cbar_kws={"label": "Impact Score"}
        )

        ax.set_xlabel("Protocol")
        ax.set_ylabel("Triggering Stablecoin")
        ax.set_title("Contagion Impact Matrix")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def create_interactive_cascade_animation(
        self,
        simulation_history: pd.DataFrame,
        stablecoin_states: List[Dict],
        save_path: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Create interactive Plotly animation of cascade.

        Args:
            simulation_history: Simulation history DataFrame
            stablecoin_states: Stablecoin state dicts
            save_path: Path to save HTML

        Returns:
            Plotly Figure or None
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for animation")
            return None

        # Create frames for animation
        frames = []
        steps = len(simulation_history)

        for step in range(steps):
            frame_data = []

            # Price trajectories up to this step
            for state in stablecoin_states:
                symbol = state.get("symbol", "Unknown")
                prices = state.get("price_history", [1.0])[:step + 1]

                frame_data.append(go.Scatter(
                    x=list(range(len(prices))),
                    y=prices,
                    mode="lines",
                    name=symbol
                ))

            frames.append(go.Frame(data=frame_data, name=str(step)))

        # Initial data
        initial_data = []
        for state in stablecoin_states:
            symbol = state.get("symbol", "Unknown")
            initial_data.append(go.Scatter(
                x=[0],
                y=[1.0],
                mode="lines",
                name=symbol
            ))

        # Create figure with animation
        fig = go.Figure(
            data=initial_data,
            layout=go.Layout(
                title="Cascade Animation",
                xaxis=dict(title="Step", range=[0, steps]),
                yaxis=dict(title="Price", range=[0, 1.1]),
                updatemenus=[
                    dict(
                        type="buttons",
                        showactive=False,
                        buttons=[
                            dict(label="Play",
                                 method="animate",
                                 args=[None, {"frame": {"duration": 100}}]),
                            dict(label="Pause",
                                 method="animate",
                                 args=[[None], {"mode": "immediate"}])
                        ]
                    )
                ]
            ),
            frames=frames
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"Animation saved to {save_path}")

        return fig

    def plot_monte_carlo_results(
        self,
        mc_results: Dict[str, Any],
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot Monte Carlo simulation results.

        Args:
            mc_results: Results from Monte Carlo simulation
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        all_results = mc_results.get("all_results", [])
        tvl_losses = [r["tvl_lost"] for r in all_results]
        depegged = [r["depegged"] for r in all_results]
        distressed = [r["distressed"] for r in all_results]

        # TVL Loss Distribution
        ax1 = axes[0, 0]
        ax1.hist(tvl_losses, bins=30, color="#e74c3c", alpha=0.7, edgecolor="black")
        ax1.axvline(np.mean(tvl_losses), color="#2c3e50", linestyle="--",
                    label=f"Mean: ${np.mean(tvl_losses):,.0f}")
        ax1.axvline(np.percentile(tvl_losses, 95), color="#e67e22", linestyle=":",
                    label=f"95th: ${np.percentile(tvl_losses, 95):,.0f}")
        ax1.set_xlabel("TVL Lost ($)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("TVL Loss Distribution")
        ax1.legend()

        # Depegged Count Distribution
        ax2 = axes[0, 1]
        unique, counts = np.unique(depegged, return_counts=True)
        ax2.bar(unique, counts, color="#3498db", alpha=0.7, edgecolor="black")
        ax2.set_xlabel("Number of Depegged Stablecoins")
        ax2.set_ylabel("Frequency")
        ax2.set_title("Depegged Stablecoins Distribution")

        # Distressed Count Distribution
        ax3 = axes[1, 0]
        unique, counts = np.unique(distressed, return_counts=True)
        ax3.bar(unique, counts, color="#e67e22", alpha=0.7, edgecolor="black")
        ax3.set_xlabel("Number of Distressed Protocols")
        ax3.set_ylabel("Frequency")
        ax3.set_title("Distressed Protocols Distribution")

        # Summary Statistics
        ax4 = axes[1, 1]
        ax4.axis("off")

        stats_text = f"""
        Monte Carlo Results Summary
        ===========================
        Scenario: {mc_results.get('scenario', 'Unknown')}
        Number of Runs: {mc_results.get('n_runs', 0)}

        TVL Loss Statistics:
          Mean: ${mc_results['tvl_loss']['mean']:,.0f}
          Std Dev: ${mc_results['tvl_loss']['std']:,.0f}
          95th Percentile: ${mc_results['tvl_loss']['percentile_95']:,.0f}
          99th Percentile: ${mc_results['tvl_loss']['percentile_99']:,.0f}
          Maximum: ${mc_results['tvl_loss']['max']:,.0f}

        Cascade Statistics:
          Avg Depegged: {mc_results['depegged_stablecoins']['mean']:.1f}
          Max Depegged: {mc_results['depegged_stablecoins']['max']}
          Avg Distressed: {mc_results['distressed_protocols']['mean']:.1f}
          Max Distressed: {mc_results['distressed_protocols']['max']}
        """

        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes,
                 fontsize=10, verticalalignment="top", fontfamily="monospace")

        plt.suptitle("Monte Carlo Simulation Analysis", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig
