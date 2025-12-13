"""
Network Metrics Calculator
===========================

Calculates network centrality metrics for executive network analysis:
- PageRank
- Betweenness Centrality
- Closeness Centrality
- Degree Centrality
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import logging

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class CentralityMetrics:
    """Centrality metrics for a node."""
    node_id: str
    node_name: str
    pagerank: float
    betweenness: float
    closeness: float
    degree: int
    in_degree: int
    out_degree: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "metrics": {
                "pagerank": round(self.pagerank, 4),
                "betweenness": round(self.betweenness, 4),
                "closeness": round(self.closeness, 4),
                "degree": self.degree,
                "in_degree": self.in_degree,
                "out_degree": self.out_degree
            }
        }


@dataclass
class NetworkStats:
    """Overall network statistics."""
    node_count: int
    edge_count: int
    avg_degree: float
    density: float
    avg_clustering: float
    diameter: Optional[int]
    avg_path_length: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "avg_degree": round(self.avg_degree, 2),
            "density": round(self.density, 4),
            "avg_clustering": round(self.avg_clustering, 4),
            "diameter": self.diameter,
            "avg_path_length": round(self.avg_path_length, 2) if self.avg_path_length else None
        }


class NetworkMetrics:
    """
    Calculator for network centrality metrics.
    
    Uses NetworkX for graph analysis and centrality calculations.
    """
    
    def __init__(self, dampening_factor: float = 0.85):
        """
        Initialize metrics calculator.
        
        Args:
            dampening_factor: PageRank dampening factor (default 0.85)
        """
        self.dampening_factor = dampening_factor
        self.logger = logger
    
    def calculate_all_metrics(
        self,
        graph: nx.DiGraph
    ) -> Tuple[Dict[str, CentralityMetrics], NetworkStats]:
        """
        Calculate all centrality metrics for a graph.
        
        Args:
            graph: NetworkX directed graph
        
        Returns:
            Tuple of (node_metrics_dict, network_stats)
        """
        if len(graph.nodes()) == 0:
            return {}, NetworkStats(0, 0, 0.0, 0.0, 0.0, None, None)
        
        # Calculate centrality metrics
        pagerank = self.calculate_pagerank(graph)
        betweenness = self.calculate_betweenness(graph)
        closeness = self.calculate_closeness(graph)
        
        # Compile metrics for each node
        node_metrics = {}
        for node in graph.nodes():
            node_data = graph.nodes[node]
            node_name = node_data.get('name', str(node))
            
            metrics = CentralityMetrics(
                node_id=str(node),
                node_name=node_name,
                pagerank=pagerank.get(node, 0.0),
                betweenness=betweenness.get(node, 0.0),
                closeness=closeness.get(node, 0.0),
                degree=graph.degree(node),
                in_degree=graph.in_degree(node),
                out_degree=graph.out_degree(node)
            )
            node_metrics[str(node)] = metrics
        
        # Calculate network statistics
        network_stats = self.calculate_network_stats(graph)
        
        return node_metrics, network_stats
    
    def calculate_pagerank(
        self,
        graph: nx.DiGraph,
        alpha: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate PageRank centrality.
        
        PageRank measures the importance of nodes based on the structure
        of incoming links.
        
        Args:
            graph: NetworkX directed graph
            alpha: Dampening factor (uses self.dampening_factor if None)
        
        Returns:
            Dictionary mapping node to PageRank score
        """
        if len(graph.nodes()) == 0:
            return {}
        
        alpha = alpha or self.dampening_factor
        
        try:
            pagerank = nx.pagerank(graph, alpha=alpha)
            return pagerank
        except Exception as e:
            self.logger.error(f"PageRank calculation failed: {e}")
            return {node: 0.0 for node in graph.nodes()}
    
    def calculate_betweenness(
        self,
        graph: nx.DiGraph,
        normalized: bool = True
    ) -> Dict[str, float]:
        """
        Calculate betweenness centrality.
        
        Betweenness measures how often a node appears on shortest paths
        between other nodes (i.e., acts as a bridge).
        
        Args:
            graph: NetworkX directed graph
            normalized: Whether to normalize scores
        
        Returns:
            Dictionary mapping node to betweenness score
        """
        if len(graph.nodes()) == 0:
            return {}
        
        try:
            betweenness = nx.betweenness_centrality(graph, normalized=normalized)
            return betweenness
        except Exception as e:
            self.logger.error(f"Betweenness calculation failed: {e}")
            return {node: 0.0 for node in graph.nodes()}
    
    def calculate_closeness(
        self,
        graph: nx.DiGraph
    ) -> Dict[str, float]:
        """
        Calculate closeness centrality.
        
        Closeness measures how close a node is to all other nodes
        (average shortest path length).
        
        Args:
            graph: NetworkX directed graph
        
        Returns:
            Dictionary mapping node to closeness score
        """
        if len(graph.nodes()) == 0:
            return {}
        
        try:
            # For directed graphs, use weakly connected components
            closeness = {}
            for component in nx.weakly_connected_components(graph):
                subgraph = graph.subgraph(component)
                if len(subgraph.nodes()) > 1:
                    component_closeness = nx.closeness_centrality(subgraph)
                    closeness.update(component_closeness)
                else:
                    # Single node component
                    node = list(component)[0]
                    closeness[node] = 0.0
            
            return closeness
        except Exception as e:
            self.logger.error(f"Closeness calculation failed: {e}")
            return {node: 0.0 for node in graph.nodes()}
    
    def calculate_network_stats(
        self,
        graph: nx.DiGraph
    ) -> NetworkStats:
        """
        Calculate overall network statistics.
        
        Args:
            graph: NetworkX directed graph
        
        Returns:
            NetworkStats object
        """
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        
        if node_count == 0:
            return NetworkStats(0, 0, 0.0, 0.0, 0.0, None, None)
        
        # Average degree
        avg_degree = sum(dict(graph.degree()).values()) / node_count
        
        # Density
        density = nx.density(graph)
        
        # Average clustering (convert to undirected for clustering)
        try:
            undirected = graph.to_undirected()
            avg_clustering = nx.average_clustering(undirected)
        except Exception:
            avg_clustering = 0.0
        
        # Diameter and average path length (for weakly connected component)
        diameter = None
        avg_path_length = None
        
        try:
            # Get largest weakly connected component
            if nx.is_weakly_connected(graph):
                largest_cc = graph
            else:
                largest_cc = graph.subgraph(
                    max(nx.weakly_connected_components(graph), key=len)
                )
            
            # Convert to undirected for these metrics
            undirected_cc = largest_cc.to_undirected()
            
            if len(undirected_cc.nodes()) > 1:
                try:
                    diameter = nx.diameter(undirected_cc)
                except Exception:
                    diameter = None
                
                try:
                    avg_path_length = nx.average_shortest_path_length(undirected_cc)
                except Exception:
                    avg_path_length = None
        except Exception as e:
            self.logger.warning(f"Could not calculate diameter/path length: {e}")
        
        return NetworkStats(
            node_count=node_count,
            edge_count=edge_count,
            avg_degree=avg_degree,
            density=density,
            avg_clustering=avg_clustering,
            diameter=diameter,
            avg_path_length=avg_path_length
        )
    
    def identify_key_players(
        self,
        metrics: Dict[str, CentralityMetrics],
        pagerank_threshold: float = 0.01,
        betweenness_threshold: float = 0.1,
        closeness_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Identify key players based on centrality metrics.
        
        Args:
            metrics: Dictionary of node metrics
            pagerank_threshold: Minimum PageRank to be considered key
            betweenness_threshold: Minimum betweenness to be considered key
            closeness_threshold: Minimum closeness to be considered key
        
        Returns:
            List of key players with their metrics
        """
        key_players = []
        
        for node_id, node_metrics in metrics.items():
            reasons = []
            
            if node_metrics.pagerank >= pagerank_threshold:
                reasons.append(f"High PageRank ({node_metrics.pagerank:.4f})")
            
            if node_metrics.betweenness >= betweenness_threshold:
                reasons.append(f"High Betweenness ({node_metrics.betweenness:.4f})")
            
            if node_metrics.closeness >= closeness_threshold:
                reasons.append(f"High Closeness ({node_metrics.closeness:.4f})")
            
            if reasons:
                key_players.append({
                    "node_id": node_id,
                    "node_name": node_metrics.node_name,
                    "metrics": node_metrics.to_dict()["metrics"],
                    "key_reasons": reasons
                })
        
        # Sort by PageRank (descending)
        key_players.sort(key=lambda x: x["metrics"]["pagerank"], reverse=True)
        
        return key_players
    
    def find_communities(
        self,
        graph: nx.DiGraph,
        algorithm: str = "louvain"
    ) -> Dict[str, int]:
        """
        Detect communities in the network.
        
        Args:
            graph: NetworkX directed graph
            algorithm: Community detection algorithm ('louvain' or 'label_propagation')
        
        Returns:
            Dictionary mapping node to community ID
        """
        if len(graph.nodes()) == 0:
            return {}
        
        # Convert to undirected for community detection
        undirected = graph.to_undirected()
        
        try:
            if algorithm == "louvain":
                # Try to use python-louvain if available
                try:
                    import community as community_louvain
                    communities = community_louvain.best_partition(undirected)
                    return communities
                except ImportError:
                    self.logger.warning("python-louvain not available, using label propagation")
                    algorithm = "label_propagation"
            
            if algorithm == "label_propagation":
                communities_generator = nx.algorithms.community.label_propagation_communities(undirected)
                communities = {}
                for i, community_set in enumerate(communities_generator):
                    for node in community_set:
                        communities[node] = i
                return communities
        except Exception as e:
            self.logger.error(f"Community detection failed: {e}")
            return {node: 0 for node in graph.nodes()}
    
    def calculate_ego_network_metrics(
        self,
        graph: nx.DiGraph,
        node: str,
        radius: int = 1
    ) -> Dict[str, Any]:
        """
        Calculate metrics for ego network (node-centric subgraph).
        
        Args:
            graph: NetworkX directed graph
            node: Central node
            radius: Radius of ego network
        
        Returns:
            Dictionary with ego network metrics
        """
        if node not in graph:
            return {}
        
        # Extract ego network
        ego_graph = nx.ego_graph(graph, node, radius=radius)
        
        # Calculate metrics for ego network
        ego_metrics, ego_stats = self.calculate_all_metrics(ego_graph)
        
        return {
            "central_node": node,
            "radius": radius,
            "size": len(ego_graph.nodes()),
            "edges": len(ego_graph.edges()),
            "stats": ego_stats.to_dict(),
            "central_node_metrics": ego_metrics.get(node, None).to_dict() if node in ego_metrics else None
        }
