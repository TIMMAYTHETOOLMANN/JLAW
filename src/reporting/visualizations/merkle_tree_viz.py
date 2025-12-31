"""
Merkle Tree Visualizer - Phase 4 Visualization
===============================================

Generates Merkle tree visualizations for evidence chain integrity.

Features:
- Tree structure visualization
- Hash display at each node
- Evidence item labels
- Interactive navigation
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import plotly.graph_objects as go
import networkx as nx

logger = logging.getLogger(__name__)


class MerkleTreeVisualizer:
    """
    Generates Merkle tree visualizations for evidence chain.
    
    Usage:
        visualizer = MerkleTreeVisualizer()
        fig = visualizer.generate_merkle_tree(
            evidence_items=[...],
            merkle_root="abc123...",
            title="Evidence Chain Merkle Tree"
        )
        fig.show()
    """
    
    def __init__(self):
        """Initialize the Merkle tree visualizer."""
        self.logger = logging.getLogger(__name__)
    
    def generate_merkle_tree(
        self,
        evidence_items: List[Dict[str, Any]],
        merkle_root: str,
        title: str = "Evidence Chain Merkle Tree",
    ) -> go.Figure:
        """
        Generate a Merkle tree visualization.
        
        Args:
            evidence_items: List of evidence item dicts with keys:
                - evidence_id: Unique identifier
                - hash: SHA-256 hash
                - description: Evidence description
            merkle_root: Root hash of the Merkle tree
            title: Chart title
            
        Returns:
            Plotly figure object
        """
        self.logger.info(f"Generating Merkle tree with {len(evidence_items)} evidence items")
        
        # Build tree structure
        G = nx.DiGraph()
        
        # Add root node
        root_id = "root"
        G.add_node(root_id, label="Root", hash=merkle_root, level=0)
        
        # Add evidence leaf nodes
        for i, item in enumerate(evidence_items):
            node_id = f"evidence_{i}"
            G.add_node(
                node_id,
                label=item.get('evidence_id', f'Evidence {i+1}'),
                hash=item.get('hash', ''),
                description=item.get('description', ''),
                level=2,  # Leaf level
            )
            
            # Add intermediate node (simplified - in reality would build full tree)
            parent_id = f"parent_{i // 2}"
            if parent_id not in G.nodes():
                G.add_node(parent_id, label=f"Branch {i // 2}", hash="...", level=1)
                G.add_edge(root_id, parent_id)
            
            G.add_edge(parent_id, node_id)
        
        # Generate hierarchical layout
        pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if nx.nx_agraph else self._hierarchical_layout(G)
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='#888'),
                hoverinfo='none',
                showlegend=False,
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = G.nodes[node]
            label = node_data.get('label', '')
            hash_val = node_data.get('hash', '')
            level = node_data.get('level', 0)
            
            # Truncate hash for display
            hash_short = hash_val[:16] + "..." if len(hash_val) > 16 else hash_val
            
            node_text.append(
                f"<b>{label}</b><br>"
                f"Hash: {hash_short}<br>"
                f"Level: {level}"
            )
            
            # Color by level
            if level == 0:  # Root
                node_color.append('red')
                node_size.append(30)
            elif level == 1:  # Intermediate
                node_color.append('orange')
                node_size.append(20)
            else:  # Leaf
                node_color.append('green')
                node_size.append(15)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white'),
            ),
            hovertext=node_text,
            hoverinfo='text',
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial, sans-serif'}
            },
            showlegend=False,
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            template="plotly_white",
            height=600,
            width=1200,
        )
        
        self.logger.info("Merkle tree visualization complete")
        return fig
    
    def _hierarchical_layout(self, G: nx.DiGraph) -> Dict[str, tuple]:
        """
        Generate hierarchical layout manually (fallback if graphviz not available).
        
        Args:
            G: NetworkX directed graph
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        pos = {}
        
        # Group nodes by level
        levels = {}
        for node in G.nodes():
            level = G.nodes[node].get('level', 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        
        # Position nodes
        for level, nodes in levels.items():
            y = -level * 100
            x_spacing = 1000 / (len(nodes) + 1)
            
            for i, node in enumerate(nodes):
                x = (i + 1) * x_spacing
                pos[node] = (x, y)
        
        return pos
    
    def save_merkle_tree(
        self,
        fig: go.Figure,
        output_path: Path,
        format: str = 'png',
    ) -> Path:
        """Save Merkle tree figure to file."""
        if format == 'html':
            fig.write_html(str(output_path))
        elif format == 'png':
            fig.write_image(str(output_path))
        elif format == 'svg':
            fig.write_image(str(output_path), format='svg')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Merkle tree saved to {output_path}")
        return output_path
