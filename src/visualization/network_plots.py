"""Network visualization for dependency graphs."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class NetworkVisualizer:
    """Visualize stablecoin-protocol dependency networks."""

    # Color schemes
    COLORS = {
        "stablecoin": {
            "fiat-backed": "#2ecc71",      # Green
            "crypto-backed": "#3498db",     # Blue
            "algorithmic": "#e74c3c",       # Red
            "hybrid": "#9b59b6",            # Purple
            "unknown": "#95a5a6"            # Gray
        },
        "protocol": {
            "lending": "#1abc9c",
            "dex": "#f39c12",
            "yield": "#e67e22",
            "bridge": "#9b59b6",
            "cdp": "#3498db",
            "other": "#95a5a6"
        },
        "risk": {
            "LOW": "#2ecc71",
            "MEDIUM": "#f1c40f",
            "HIGH": "#e67e22",
            "CRITICAL": "#e74c3c"
        }
    }

    def __init__(self, dependency_graph):
        """
        Initialize network visualizer.

        Args:
            dependency_graph: DependencyGraph instance
        """
        self.graph = dependency_graph

    def plot_dependency_network(
        self,
        figsize: Tuple[int, int] = (16, 12),
        layout: str = "spring",
        node_size_factor: float = 1.0,
        edge_width_factor: float = 1.0,
        show_labels: bool = True,
        highlight_nodes: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create static matplotlib visualization of dependency network.

        Args:
            figsize: Figure size
            layout: Layout algorithm ('spring', 'circular', 'kamada_kawai')
            node_size_factor: Multiplier for node sizes
            edge_width_factor: Multiplier for edge widths
            show_labels: Whether to show node labels
            highlight_nodes: Nodes to highlight
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        G = self.graph.graph

        # Calculate layout
        if layout == "spring":
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G, seed=42)

        # Prepare node attributes
        node_colors = []
        node_sizes = []
        node_types = []

        for node in G.nodes():
            node_data = G.nodes[node]
            node_type = node_data.get("node_type", "unknown")
            node_types.append(node_type)

            if node_type == "stablecoin":
                coin_type = node_data.get("coin_type", "unknown")
                color = self.COLORS["stablecoin"].get(coin_type, "#95a5a6")
                size = np.sqrt(node_data.get("market_cap", 1e9)) / 1e4 * node_size_factor
            else:
                category = node_data.get("category", "other")
                color = self.COLORS["protocol"].get(category, "#95a5a6")
                size = np.sqrt(node_data.get("tvl", 1e8)) / 1e3 * node_size_factor

            # Highlight nodes
            if highlight_nodes and node in highlight_nodes:
                color = "#e74c3c"
                size *= 1.5

            node_colors.append(color)
            node_sizes.append(max(size, 100))

        # Prepare edge attributes
        edge_widths = []
        edge_colors = []
        for u, v, data in G.edges(data=True):
            weight = data.get("weight", 1)
            width = np.log10(max(weight, 1)) / 2 * edge_width_factor
            edge_widths.append(max(width, 0.5))

            risk = data.get("risk_score", 0)
            if risk > 0.75:
                edge_colors.append("#e74c3c")
            elif risk > 0.5:
                edge_colors.append("#e67e22")
            elif risk > 0.25:
                edge_colors.append("#f1c40f")
            else:
                edge_colors.append("#95a5a6")

        # Draw edges
        nx.draw_networkx_edges(
            G, pos, ax=ax,
            width=edge_widths,
            edge_color=edge_colors,
            alpha=0.6,
            arrows=True,
            arrowsize=10,
            connectionstyle="arc3,rad=0.1"
        )

        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9
        )

        # Draw labels
        if show_labels:
            nx.draw_networkx_labels(
                G, pos, ax=ax,
                font_size=8,
                font_weight="bold"
            )

        # Create legend
        legend_elements = [
            mpatches.Patch(color="#2ecc71", label="Fiat-backed"),
            mpatches.Patch(color="#3498db", label="Crypto-backed"),
            mpatches.Patch(color="#e74c3c", label="Algorithmic"),
            mpatches.Patch(color="#9b59b6", label="Hybrid/Bridge"),
            mpatches.Patch(color="#f39c12", label="DEX"),
            mpatches.Patch(color="#1abc9c", label="Lending"),
        ]
        ax.legend(handles=legend_elements, loc="upper left", fontsize=8)

        ax.set_title("Stablecoin-Protocol Dependency Network", fontsize=14, fontweight="bold")
        ax.axis("off")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Network plot saved to {save_path}")

        return fig

    def plot_cascade_visualization(
        self,
        cascade_path: Dict[int, List[str]],
        figsize: Tuple[int, int] = (14, 10),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Visualize cascade propagation path.

        Args:
            cascade_path: Dict mapping depth to affected nodes
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Create hierarchical layout
        pos = {}
        max_width = max(len(nodes) for nodes in cascade_path.values()) if cascade_path else 1

        for depth, nodes in cascade_path.items():
            y = -depth
            for i, node in enumerate(nodes):
                x = (i - len(nodes) / 2) * 2
                pos[node] = (x, y)

        # Build subgraph with cascade edges
        cascade_nodes = set()
        for nodes in cascade_path.values():
            cascade_nodes.update(nodes)

        subgraph = self.graph.graph.subgraph(cascade_nodes).copy()

        # Color by depth
        depth_colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(cascade_path)))
        node_colors = []
        for node in subgraph.nodes():
            for depth, nodes in cascade_path.items():
                if node in nodes:
                    node_colors.append(depth_colors[depth])
                    break

        # Draw
        nx.draw_networkx_nodes(
            subgraph, pos, ax=ax,
            node_color=node_colors,
            node_size=1000,
            alpha=0.9
        )

        nx.draw_networkx_edges(
            subgraph, pos, ax=ax,
            edge_color="#e74c3c",
            width=2,
            alpha=0.7,
            arrows=True,
            arrowsize=15
        )

        nx.draw_networkx_labels(
            subgraph, pos, ax=ax,
            font_size=9,
            font_weight="bold"
        )

        # Add depth labels
        for depth in cascade_path:
            ax.text(
                -max_width - 1, -depth,
                f"Depth {depth}",
                fontsize=10,
                fontweight="bold",
                va="center"
            )

        ax.set_title("Cascade Propagation Path", fontsize=14, fontweight="bold")
        ax.axis("off")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig

    def create_interactive_network(
        self,
        save_path: Optional[str] = None
    ) -> Optional[go.Figure]:
        """
        Create interactive Plotly network visualization.

        Args:
            save_path: Path to save HTML file

        Returns:
            Plotly Figure or None if Plotly unavailable
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for interactive visualization")
            return None

        G = self.graph.graph
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Create edge traces
        edge_x = []
        edge_y = []
        edge_colors = []

        for u, v, data in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines"
        )

        # Create node traces
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = G.nodes[node]
            node_type = node_data.get("node_type", "unknown")

            if node_type == "stablecoin":
                coin_type = node_data.get("coin_type", "unknown")
                mcap = node_data.get("market_cap", 0)
                text = f"{node}<br>Type: {coin_type}<br>MCap: ${mcap:,.0f}"
                color = self.COLORS["stablecoin"].get(coin_type, "#95a5a6")
                size = np.sqrt(mcap) / 1e4 + 10
            else:
                category = node_data.get("category", "other")
                tvl = node_data.get("tvl", 0)
                text = f"{node}<br>Category: {category}<br>TVL: ${tvl:,.0f}"
                color = self.COLORS["protocol"].get(category, "#95a5a6")
                size = np.sqrt(tvl) / 1e3 + 10

            node_text.append(text)
            node_colors.append(color)
            node_sizes.append(min(size, 50))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=[n for n in G.nodes()],
            textposition="top center",
            hovertext=node_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line_width=2,
                line_color="white"
            )
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Interactive Stablecoin-Protocol Dependency Network",
                showlegend=False,
                hovermode="closest",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="white"
            )
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"Interactive network saved to {save_path}")

        return fig

    def plot_centrality_comparison(
        self,
        top_n: int = 15,
        figsize: Tuple[int, int] = (14, 8),
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot comparison of centrality metrics.

        Args:
            top_n: Number of top nodes to show
            figsize: Figure size
            save_path: Path to save figure

        Returns:
            matplotlib Figure
        """
        centrality = self.graph.calculate_centrality_metrics()

        # Filter to stablecoins
        stablecoin_centrality = centrality[centrality["type"] == "stablecoin"].head(top_n)

        fig, axes = plt.subplots(1, 3, figsize=figsize)

        metrics = ["pagerank", "betweenness", "out_degree_weighted"]
        titles = ["PageRank (Importance)", "Betweenness (Bridge Role)", "Out-Degree (Dependents)"]

        for ax, metric, title in zip(axes, metrics, titles):
            data = stablecoin_centrality.sort_values(metric, ascending=True)

            colors = [self.COLORS["stablecoin"].get(
                self.graph.stablecoins.get(n, {}).stablecoin_type.value if n in self.graph.stablecoins else "unknown",
                "#95a5a6"
            ) for n in data["node"]]

            ax.barh(data["node"], data[metric], color=colors)
            ax.set_xlabel(metric.replace("_", " ").title())
            ax.set_title(title)

        plt.suptitle("Stablecoin Centrality Metrics", fontsize=14, fontweight="bold")
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        return fig
