"""Build and analyze stablecoin dependency graphs."""

import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Set
from loguru import logger
from collections import defaultdict

from src.models.stablecoin import Stablecoin
from src.models.protocol import Protocol
from src.models.exposure import Exposure, ExposureType


class DependencyGraph:
    """Build and analyze stablecoin-protocol dependency networks."""

    def __init__(self):
        """Initialize dependency graph."""
        self.graph = nx.DiGraph()
        self.stablecoins: Dict[str, Stablecoin] = {}
        self.protocols: Dict[str, Protocol] = {}
        self.exposures: List[Exposure] = []

    def add_stablecoin(self, stablecoin: Stablecoin):
        """
        Add a stablecoin node to the graph.

        Args:
            stablecoin: Stablecoin object to add
        """
        self.stablecoins[stablecoin.symbol] = stablecoin
        self.graph.add_node(
            stablecoin.symbol,
            node_type="stablecoin",
            market_cap=stablecoin.market_cap,
            coin_type=stablecoin.stablecoin_type.value,
            current_price=stablecoin.current_price,
            is_depegged=stablecoin.is_depegged()
        )
        logger.debug(f"Added stablecoin node: {stablecoin.symbol}")

    def add_protocol(self, protocol: Protocol):
        """
        Add a protocol node to the graph.

        Args:
            protocol: Protocol object to add
        """
        self.protocols[protocol.slug] = protocol
        self.graph.add_node(
            protocol.slug,
            node_type="protocol",
            tvl=protocol.tvl,
            category=protocol.category.value,
            name=protocol.name
        )
        logger.debug(f"Added protocol node: {protocol.slug}")

    def add_exposure(self, exposure: Exposure):
        """
        Add an exposure edge between protocol and stablecoin.

        Args:
            exposure: Exposure object defining the relationship
        """
        self.exposures.append(exposure)

        # Direction: stablecoin -> protocol (protocol depends on stablecoin)
        self.graph.add_edge(
            exposure.stablecoin_symbol,
            exposure.protocol_name,
            weight=exposure.amount_usd,
            exposure_type=exposure.exposure_type.value,
            risk_score=exposure.risk_score(),
            percentage_of_tvl=exposure.percentage_of_tvl
        )
        logger.debug(
            f"Added exposure: {exposure.stablecoin_symbol} -> "
            f"{exposure.protocol_name} (${exposure.amount_usd:,.0f})"
        )

    def add_stablecoin_dependency(
        self,
        dependent: str,
        backing: str,
        amount: float,
        percentage: float = 0.0
    ):
        """
        Add dependency between stablecoins (e.g., DAI backed by USDC).

        Args:
            dependent: Symbol of the dependent stablecoin
            backing: Symbol of the backing stablecoin
            amount: USD amount of backing
            percentage: Percentage of collateral
        """
        self.graph.add_edge(
            backing,
            dependent,
            weight=amount,
            exposure_type="backing",
            risk_score=1.0,  # High risk for stablecoin-stablecoin dependencies
            percentage=percentage,
            is_stablecoin_backing=True
        )
        logger.info(f"Added stablecoin dependency: {backing} -> {dependent}")

    def build_from_data(
        self,
        stablecoins: List[Stablecoin],
        protocols: List[Protocol],
        exposures: List[Exposure]
    ):
        """
        Build graph from lists of data objects.

        Args:
            stablecoins: List of Stablecoin objects
            protocols: List of Protocol objects
            exposures: List of Exposure objects
        """
        for stablecoin in stablecoins:
            self.add_stablecoin(stablecoin)

        for protocol in protocols:
            self.add_protocol(protocol)

        for exposure in exposures:
            self.add_exposure(exposure)

        logger.info(
            f"Built graph with {len(stablecoins)} stablecoins, "
            f"{len(protocols)} protocols, {len(exposures)} exposures"
        )

    def get_downstream_protocols(self, stablecoin: str) -> List[str]:
        """
        Get all protocols that would be affected by a stablecoin depeg.

        Args:
            stablecoin: Stablecoin symbol

        Returns:
            List of protocol slugs that depend on this stablecoin
        """
        if stablecoin not in self.graph:
            return []

        downstream = []
        for successor in self.graph.successors(stablecoin):
            if successor in self.protocols:
                downstream.append(successor)
        return downstream

    def get_downstream_stablecoins(self, stablecoin: str) -> List[str]:
        """
        Get stablecoins that depend on this stablecoin.

        Args:
            stablecoin: Stablecoin symbol

        Returns:
            List of dependent stablecoin symbols
        """
        if stablecoin not in self.graph:
            return []

        downstream = []
        for successor in self.graph.successors(stablecoin):
            if successor in self.stablecoins:
                downstream.append(successor)
        return downstream

    def get_cascade_path(
        self,
        source_stablecoin: str,
        max_depth: int = 5,
        min_exposure_ratio: float = 0.05
    ) -> Dict[int, List[str]]:
        """
        Calculate cascade propagation paths from a depegging stablecoin.

        Args:
            source_stablecoin: Initial depegging stablecoin
            max_depth: Maximum cascade depth to explore
            min_exposure_ratio: Minimum exposure ratio to consider

        Returns:
            Dict mapping depth level to list of affected entities
        """
        cascade = {0: [source_stablecoin]}
        visited = {source_stablecoin}

        for depth in range(1, max_depth + 1):
            cascade[depth] = []
            for node in cascade[depth - 1]:
                for successor in self.graph.successors(node):
                    if successor not in visited:
                        # Check if exposure is significant
                        edge_data = self.graph.edges[node, successor]
                        exposure_ratio = edge_data.get("percentage_of_tvl", 0)

                        if exposure_ratio >= min_exposure_ratio or edge_data.get("is_stablecoin_backing"):
                            cascade[depth].append(successor)
                            visited.add(successor)

            if not cascade[depth]:
                break

        return {k: v for k, v in cascade.items() if v}

    def calculate_blast_radius(
        self,
        stablecoin: str,
        depeg_severity: float = 0.1
    ) -> Dict[str, Any]:
        """
        Calculate the 'blast radius' of a stablecoin depeg.

        Args:
            stablecoin: Stablecoin symbol to analyze
            depeg_severity: Severity of depeg (0-1)

        Returns:
            Dict with blast radius metrics
        """
        cascade = self.get_cascade_path(stablecoin)

        total_tvl_at_risk = 0.0
        direct_tvl_at_risk = 0.0
        protocols_affected = []
        stablecoins_affected = []

        for depth, nodes in cascade.items():
            for node in nodes:
                if node in self.protocols:
                    protocol = self.protocols[node]
                    tvl_at_risk = protocol.exposure_to(stablecoin) * depeg_severity
                    total_tvl_at_risk += tvl_at_risk
                    if depth == 1:
                        direct_tvl_at_risk += tvl_at_risk
                    protocols_affected.append({
                        "name": node,
                        "depth": depth,
                        "tvl_at_risk": tvl_at_risk
                    })
                elif node in self.stablecoins and node != stablecoin:
                    stablecoins_affected.append({
                        "symbol": node,
                        "depth": depth
                    })

        return {
            "source": stablecoin,
            "depeg_severity": depeg_severity,
            "total_tvl_at_risk": total_tvl_at_risk,
            "direct_tvl_at_risk": direct_tvl_at_risk,
            "protocols_affected": len(protocols_affected),
            "stablecoins_affected": len(stablecoins_affected),
            "cascade_depth": len(cascade),
            "cascade_path": cascade,
            "affected_protocols_detail": protocols_affected,
            "affected_stablecoins_detail": stablecoins_affected
        }

    def find_systemic_chokepoints(self) -> List[Tuple[str, float]]:
        """
        Identify stablecoins that are systemic chokepoints.

        Returns:
            List of (stablecoin, risk_score) tuples sorted by risk
        """
        chokepoints = []

        for stablecoin in self.stablecoins:
            blast = self.calculate_blast_radius(stablecoin)
            score = (
                blast["total_tvl_at_risk"] *
                (1 + blast["stablecoins_affected"] * 0.5)  # Extra weight for stablecoin contagion
            )
            chokepoints.append((stablecoin, score))

        return sorted(chokepoints, key=lambda x: x[1], reverse=True)

    def calculate_centrality_metrics(self) -> pd.DataFrame:
        """
        Calculate network centrality metrics for all nodes.

        Returns:
            DataFrame with centrality metrics for each node
        """
        metrics = []

        # Calculate various centrality measures
        degree_cent = nx.degree_centrality(self.graph)
        in_degree = dict(self.graph.in_degree(weight="weight"))
        out_degree = dict(self.graph.out_degree(weight="weight"))

        try:
            pagerank = nx.pagerank(self.graph, weight="weight")
        except Exception:
            pagerank = {n: 0 for n in self.graph.nodes()}

        try:
            betweenness = nx.betweenness_centrality(self.graph, weight="weight")
        except Exception:
            betweenness = {n: 0 for n in self.graph.nodes()}

        try:
            # For closeness, we need a connected graph
            if nx.is_weakly_connected(self.graph):
                closeness = nx.closeness_centrality(self.graph)
            else:
                closeness = {n: 0 for n in self.graph.nodes()}
        except Exception:
            closeness = {n: 0 for n in self.graph.nodes()}

        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            metrics.append({
                "node": node,
                "type": node_data.get("node_type", "unknown"),
                "degree_centrality": degree_cent.get(node, 0),
                "in_degree_weighted": in_degree.get(node, 0),
                "out_degree_weighted": out_degree.get(node, 0),
                "pagerank": pagerank.get(node, 0),
                "betweenness": betweenness.get(node, 0),
                "closeness": closeness.get(node, 0)
            })

        df = pd.DataFrame(metrics)
        return df.sort_values("pagerank", ascending=False)

    def find_critical_paths(
        self,
        source: str,
        target: str
    ) -> List[List[str]]:
        """
        Find all paths between two nodes.

        Args:
            source: Source node (usually a stablecoin)
            target: Target node (protocol or stablecoin)

        Returns:
            List of paths (each path is a list of nodes)
        """
        try:
            return list(nx.all_simple_paths(self.graph, source, target, cutoff=5))
        except nx.NetworkXNoPath:
            return []

    def identify_feedback_loops(self) -> List[List[str]]:
        """
        Identify feedback loops in the dependency graph.

        Returns:
            List of cycles (feedback loops)
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            # Filter to only include cycles with stablecoins
            stablecoin_cycles = [
                c for c in cycles
                if any(node in self.stablecoins for node in c)
            ]
            return stablecoin_cycles
        except Exception:
            return []

    def get_protocol_exposure_summary(self, protocol_slug: str) -> Dict[str, Any]:
        """
        Get exposure summary for a specific protocol.

        Args:
            protocol_slug: Protocol identifier

        Returns:
            Exposure summary dict
        """
        if protocol_slug not in self.protocols:
            return {}

        exposures = []
        for edge in self.graph.in_edges(protocol_slug, data=True):
            source, _, data = edge
            if source in self.stablecoins:
                exposures.append({
                    "stablecoin": source,
                    "amount_usd": data.get("weight", 0),
                    "exposure_type": data.get("exposure_type", "unknown"),
                    "risk_score": data.get("risk_score", 0)
                })

        return {
            "protocol": protocol_slug,
            "total_stablecoin_exposure": sum(e["amount_usd"] for e in exposures),
            "exposures": sorted(exposures, key=lambda x: x["amount_usd"], reverse=True),
            "stablecoin_count": len(exposures)
        }

    def get_stablecoin_dependents(self, stablecoin: str) -> Dict[str, Any]:
        """
        Get all entities depending on a stablecoin.

        Args:
            stablecoin: Stablecoin symbol

        Returns:
            Dict with dependent protocols and stablecoins
        """
        if stablecoin not in self.stablecoins:
            return {}

        protocols = []
        stablecoins = []

        for edge in self.graph.out_edges(stablecoin, data=True):
            _, target, data = edge
            if target in self.protocols:
                protocols.append({
                    "protocol": target,
                    "amount_usd": data.get("weight", 0),
                    "exposure_type": data.get("exposure_type", "unknown")
                })
            elif target in self.stablecoins:
                stablecoins.append({
                    "stablecoin": target,
                    "amount_usd": data.get("weight", 0)
                })

        return {
            "stablecoin": stablecoin,
            "dependent_protocols": sorted(protocols, key=lambda x: x["amount_usd"], reverse=True),
            "dependent_stablecoins": stablecoins,
            "total_dependent_tvl": sum(p["amount_usd"] for p in protocols)
        }

    def export_for_visualization(self) -> Dict[str, Any]:
        """
        Export graph data for visualization.

        Returns:
            Dict with nodes and edges for visualization
        """
        nodes = []
        for node, data in self.graph.nodes(data=True):
            node_info = {"id": node, **data}

            # Add additional info based on node type
            if data.get("node_type") == "stablecoin" and node in self.stablecoins:
                stablecoin = self.stablecoins[node]
                node_info["market_cap"] = stablecoin.market_cap
                node_info["price"] = stablecoin.current_price
            elif data.get("node_type") == "protocol" and node in self.protocols:
                protocol = self.protocols[node]
                node_info["tvl"] = protocol.tvl

            nodes.append(node_info)

        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **data
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "stablecoins": len(self.stablecoins),
                "protocols": len(self.protocols)
            }
        }

    def to_adjacency_matrix(self) -> pd.DataFrame:
        """
        Convert graph to adjacency matrix.

        Returns:
            DataFrame adjacency matrix
        """
        return nx.to_pandas_adjacency(self.graph, weight="weight")

    def summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for the graph.

        Returns:
            Summary dict
        """
        total_exposure = sum(e.amount_usd for e in self.exposures)

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "stablecoins": len(self.stablecoins),
            "protocols": len(self.protocols),
            "total_exposure_usd": total_exposure,
            "density": nx.density(self.graph),
            "is_weakly_connected": nx.is_weakly_connected(self.graph),
            "number_of_components": nx.number_weakly_connected_components(self.graph)
        }

    def __repr__(self) -> str:
        return (
            f"DependencyGraph(stablecoins={len(self.stablecoins)}, "
            f"protocols={len(self.protocols)}, edges={self.graph.number_of_edges()})"
        )
