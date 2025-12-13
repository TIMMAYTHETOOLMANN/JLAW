"""
Temporal Network Analyzer
==========================

Analyzes how executive networks evolve over time using sliding windows.
Detects changes in network structure, key players, and relationships.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

import networkx as nx

from .network_metrics import NetworkMetrics, CentralityMetrics, NetworkStats

logger = logging.getLogger(__name__)


@dataclass
class TemporalSnapshot:
    """Network snapshot at a specific time period."""
    start_date: date
    end_date: date
    quarter: str  # e.g., "2024Q1"
    node_count: int
    edge_count: int
    key_players: List[str]
    network_stats: NetworkStats
    centrality_metrics: Dict[str, CentralityMetrics]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
                "quarter": self.quarter
            },
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "key_players": self.key_players,
            "network_stats": self.network_stats.to_dict(),
            "top_metrics": [
                m.to_dict() for m in sorted(
                    self.centrality_metrics.values(),
                    key=lambda x: x.pagerank,
                    reverse=True
                )[:10]
            ]
        }


@dataclass
class NetworkChange:
    """Detected change in network structure."""
    change_type: str  # node_added, node_removed, edge_added, edge_removed, key_player_emerged
    from_quarter: str
    to_quarter: str
    entity_id: str
    entity_name: str
    change_magnitude: float  # 0.0-1.0
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type,
            "period": {
                "from": self.from_quarter,
                "to": self.to_quarter
            },
            "entity": {
                "id": self.entity_id,
                "name": self.entity_name
            },
            "magnitude": round(self.change_magnitude, 3),
            "description": self.description
        }


class TemporalNetworkAnalyzer:
    """
    Analyzes executive networks over time using sliding window approach.
    
    Creates quarterly snapshots and detects:
    - Network growth/contraction
    - Emergence of new key players
    - Changes in network structure
    - Relationship formation/dissolution
    """
    
    def __init__(
        self,
        window_quarters: int = 8,
        key_player_pagerank_threshold: float = 0.01
    ):
        """
        Initialize temporal analyzer.
        
        Args:
            window_quarters: Number of quarters to analyze (default 8 = 2 years)
            key_player_pagerank_threshold: PageRank threshold for key players
        """
        self.window_quarters = window_quarters
        self.key_player_threshold = key_player_pagerank_threshold
        self.metrics_calculator = NetworkMetrics()
        self.logger = logger
    
    def analyze_temporal_evolution(
        self,
        relationships: List[Dict[str, Any]],
        start_date: date,
        end_date: date
    ) -> Tuple[List[TemporalSnapshot], List[NetworkChange]]:
        """
        Analyze network evolution over time.
        
        Args:
            relationships: List of relationships with start_date, end_date
            start_date: Analysis start date
            end_date: Analysis end date
        
        Returns:
            Tuple of (snapshots, changes)
        """
        # Generate quarterly windows
        quarters = self._generate_quarters(start_date, end_date)
        
        # Create snapshot for each quarter
        snapshots = []
        for quarter_start, quarter_end, quarter_str in quarters:
            snapshot = self._create_snapshot(
                relationships,
                quarter_start,
                quarter_end,
                quarter_str
            )
            snapshots.append(snapshot)
        
        # Detect changes between consecutive snapshots
        changes = self._detect_changes(snapshots)
        
        return snapshots, changes
    
    def _generate_quarters(
        self,
        start_date: date,
        end_date: date
    ) -> List[Tuple[date, date, str]]:
        """
        Generate list of quarters in date range.
        
        Returns:
            List of (start_date, end_date, quarter_string) tuples
        """
        quarters = []
        current = start_date
        
        while current <= end_date:
            # Determine quarter
            quarter_num = (current.month - 1) // 3 + 1
            quarter_str = f"{current.year}Q{quarter_num}"
            
            # Quarter start
            quarter_start_month = (quarter_num - 1) * 3 + 1
            quarter_start = date(current.year, quarter_start_month, 1)
            
            # Quarter end
            quarter_end_month = quarter_num * 3
            if quarter_end_month == 12:
                quarter_end = date(current.year, 12, 31)
            else:
                # Last day of quarter end month
                next_month = quarter_end_month + 1
                quarter_end = date(current.year, next_month, 1) - timedelta(days=1)
            
            quarters.append((quarter_start, quarter_end, quarter_str))
            
            # Move to next quarter
            if quarter_num == 4:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, quarter_end_month + 1, 1)
        
        return quarters
    
    def _create_snapshot(
        self,
        relationships: List[Dict[str, Any]],
        start_date: date,
        end_date: date,
        quarter_str: str
    ) -> TemporalSnapshot:
        """Create network snapshot for a specific time period."""
        # Filter relationships active in this period
        active_relationships = [
            rel for rel in relationships
            if self._is_active_in_period(rel, start_date, end_date)
        ]
        
        # Build graph
        graph = self._build_graph(active_relationships)
        
        # Calculate metrics
        if len(graph.nodes()) > 0:
            centrality_metrics, network_stats = self.metrics_calculator.calculate_all_metrics(graph)
            
            # Identify key players
            key_players = [
                node_id for node_id, metrics in centrality_metrics.items()
                if metrics.pagerank >= self.key_player_threshold
            ]
        else:
            centrality_metrics = {}
            network_stats = NetworkStats(0, 0, 0.0, 0.0, 0.0, None, None)
            key_players = []
        
        return TemporalSnapshot(
            start_date=start_date,
            end_date=end_date,
            quarter=quarter_str,
            node_count=len(graph.nodes()),
            edge_count=len(graph.edges()),
            key_players=key_players,
            network_stats=network_stats,
            centrality_metrics=centrality_metrics
        )
    
    def _is_active_in_period(
        self,
        relationship: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> bool:
        """Check if relationship was active during period."""
        rel_start = relationship.get('start_date')
        rel_end = relationship.get('end_date')
        
        if isinstance(rel_start, str):
            rel_start = datetime.fromisoformat(rel_start).date()
        if isinstance(rel_end, str):
            rel_end = datetime.fromisoformat(rel_end).date()
        
        # If no start date, assume active
        if not rel_start:
            rel_start = start_date
        
        # If no end date, assume still active
        if not rel_end:
            rel_end = end_date
        
        # Check overlap
        return rel_start <= end_date and rel_end >= start_date
    
    def _build_graph(
        self,
        relationships: List[Dict[str, Any]]
    ) -> nx.DiGraph:
        """Build NetworkX graph from relationships."""
        graph = nx.DiGraph()
        
        for rel in relationships:
            source = rel.get('source_id')
            target = rel.get('target_id')
            source_name = rel.get('source_name', source)
            target_name = rel.get('target_name', target)
            rel_type = rel.get('type', 'UNKNOWN')
            
            if source and target:
                # Add nodes with names
                if source not in graph:
                    graph.add_node(source, name=source_name)
                if target not in graph:
                    graph.add_node(target, name=target_name)
                
                # Add edge
                graph.add_edge(source, target, type=rel_type)
        
        return graph
    
    def _detect_changes(
        self,
        snapshots: List[TemporalSnapshot]
    ) -> List[NetworkChange]:
        """Detect changes between consecutive snapshots."""
        changes = []
        
        for i in range(len(snapshots) - 1):
            snapshot1 = snapshots[i]
            snapshot2 = snapshots[i + 1]
            
            # Node changes
            nodes1 = set(snapshot1.centrality_metrics.keys())
            nodes2 = set(snapshot2.centrality_metrics.keys())
            
            # New nodes
            new_nodes = nodes2 - nodes1
            for node_id in new_nodes:
                metrics = snapshot2.centrality_metrics[node_id]
                changes.append(NetworkChange(
                    change_type='node_added',
                    from_quarter=snapshot1.quarter,
                    to_quarter=snapshot2.quarter,
                    entity_id=node_id,
                    entity_name=metrics.node_name,
                    change_magnitude=metrics.pagerank,
                    description=f"New executive joined network: {metrics.node_name}"
                ))
            
            # Removed nodes
            removed_nodes = nodes1 - nodes2
            for node_id in removed_nodes:
                metrics = snapshot1.centrality_metrics[node_id]
                changes.append(NetworkChange(
                    change_type='node_removed',
                    from_quarter=snapshot1.quarter,
                    to_quarter=snapshot2.quarter,
                    entity_id=node_id,
                    entity_name=metrics.node_name,
                    change_magnitude=metrics.pagerank,
                    description=f"Executive left network: {metrics.node_name}"
                ))
            
            # Key player changes
            key_players1 = set(snapshot1.key_players)
            key_players2 = set(snapshot2.key_players)
            
            # Emerged key players
            emerged = key_players2 - key_players1
            for node_id in emerged:
                if node_id in snapshot2.centrality_metrics:
                    metrics = snapshot2.centrality_metrics[node_id]
                    changes.append(NetworkChange(
                        change_type='key_player_emerged',
                        from_quarter=snapshot1.quarter,
                        to_quarter=snapshot2.quarter,
                        entity_id=node_id,
                        entity_name=metrics.node_name,
                        change_magnitude=metrics.pagerank,
                        description=f"Emerged as key player: {metrics.node_name} (PageRank: {metrics.pagerank:.4f})"
                    ))
            
            # Network growth/contraction
            growth_rate = (snapshot2.node_count - snapshot1.node_count) / max(1, snapshot1.node_count)
            if abs(growth_rate) > 0.1:  # 10% change
                change_type = 'network_expansion' if growth_rate > 0 else 'network_contraction'
                changes.append(NetworkChange(
                    change_type=change_type,
                    from_quarter=snapshot1.quarter,
                    to_quarter=snapshot2.quarter,
                    entity_id='network',
                    entity_name='Overall Network',
                    change_magnitude=abs(growth_rate),
                    description=f"Network {'expanded' if growth_rate > 0 else 'contracted'} by {abs(growth_rate)*100:.1f}%"
                ))
        
        return changes
    
    def generate_temporal_report(
        self,
        snapshots: List[TemporalSnapshot],
        changes: List[NetworkChange]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive temporal analysis report.
        
        Args:
            snapshots: List of temporal snapshots
            changes: List of detected changes
        
        Returns:
            Dictionary with temporal analysis summary
        """
        if not snapshots:
            return {}
        
        return {
            "analysis_period": {
                "start": snapshots[0].start_date.isoformat(),
                "end": snapshots[-1].end_date.isoformat(),
                "quarters_analyzed": len(snapshots)
            },
            "network_evolution": {
                "initial_nodes": snapshots[0].node_count,
                "final_nodes": snapshots[-1].node_count,
                "initial_edges": snapshots[0].edge_count,
                "final_edges": snapshots[-1].edge_count,
                "growth_rate": (snapshots[-1].node_count - snapshots[0].node_count) / max(1, snapshots[0].node_count)
            },
            "changes_detected": {
                "total_changes": len(changes),
                "by_type": self._count_changes_by_type(changes),
                "significant_changes": [c.to_dict() for c in changes if c.change_magnitude > 0.5]
            },
            "snapshots": [s.to_dict() for s in snapshots],
            "all_changes": [c.to_dict() for c in changes]
        }
    
    def _count_changes_by_type(
        self,
        changes: List[NetworkChange]
    ) -> Dict[str, int]:
        """Count changes by type."""
        counts = {}
        for change in changes:
            change_type = change.change_type
            counts[change_type] = counts.get(change_type, 0) + 1
        return counts
