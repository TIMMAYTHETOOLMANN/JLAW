"""
Network Graph Generator - Phase 4 Visualization
================================================

Generates actor network visualizations showing:
- Board interlocks
- Beneficial ownership flows
- Transaction coordination patterns

Uses networkx for graph construction and plotly for visualization.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import networkx as nx
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


class NetworkGraphGenerator:
    """
    Generates network graph visualizations of actor relationships.
    
    Usage:
        generator = NetworkGraphGenerator()
        fig = generator.generate_network(
            actors=[...],
            relationships=[...],
            title="NIKE 2019 Actor Network"
        )
        fig.show()
    """
    
    def __init__(self):
        """Initialize the network graph generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_network(
        self,
        actors: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]] = None,
        title: str = "Actor Network",
        layout: str = 'spring',
    ) -> go.Figure:
        """
        Generate an interactive network graph.
        
        Args:
            actors: List of actor dicts with keys:
                - actor_id: Unique identifier
                - name: Actor name
                - risk_score: Risk score (0-100)
                - actor_type: Type (INDIVIDUAL, ENTITY)
                - roles: List of roles
            relationships: List of relationship dicts with keys:
                - source: Source actor_id
                - target: Target actor_id
                - relationship_type: Type (BOARD_INTERLOCK, OWNERSHIP, etc.)
                - strength: Relationship strength (0-1)
            title: Chart title
            layout: Layout algorithm ('spring', 'circular', 'hierarchical')
            
        Returns:
            Plotly figure object
        """
        self.logger.info(f"Generating network with {len(actors)} actors")
        
        if relationships is None:
            relationships = []
        
        # Create networkx graph
        G = nx.Graph()
        
        # Add nodes
        for actor in actors:
            G.add_node(
                actor['actor_id'],
                name=actor.get('name', 'Unknown'),
                risk_score=actor.get('risk_score', 0),
                actor_type=actor.get('actor_type', 'INDIVIDUAL'),
                roles=actor.get('roles', []),
            )
        
        # Add edges
        for rel in relationships:
            G.add_edge(
                rel['source'],
                rel['target'],
                relationship_type=rel.get('relationship_type', 'UNKNOWN'),
                strength=rel.get('strength', 0.5),
            )
        
        # Generate layout
        if layout == 'spring':
            pos = nx.spring_layout(G, k=0.5, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'hierarchical':
            pos = nx.kamada_kawai_layout(G)
        else:
            pos = nx.spring_layout(G)
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=1, color='#888'),
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
            name = node_data.get('name', 'Unknown')
            risk_score = node_data.get('risk_score', 0)
            roles = node_data.get('roles', [])
            
            node_text.append(
                f"<b>{name}</b><br>"
                f"Risk Score: {risk_score:.1f}<br>"
                f"Roles: {', '.join(roles)}"
            )
            
            # Color by risk score
            if risk_score >= 80:
                node_color.append('red')
            elif risk_score >= 60:
                node_color.append('orange')
            elif risk_score >= 40:
                node_color.append('yellow')
            else:
                node_color.append('green')
            
            # Size by number of connections
            node_size.append(10 + len(list(G.neighbors(node))) * 5)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white'),
            ),
            text=[G.nodes[n]['name'] for n in G.nodes()],
            textposition="top center",
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
            height=800,
            width=1200,
        )
        
        self.logger.info("Network graph generation complete")
        return fig
    
    def save_network(
        self,
        fig: go.Figure,
        output_path: Path,
        format: str = 'png',
    ) -> Path:
        """Save network figure to file."""
        if format == 'html':
            fig.write_html(str(output_path))
        elif format == 'png':
            fig.write_image(str(output_path))
        elif format == 'svg':
            fig.write_image(str(output_path), format='svg')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info(f"Network saved to {output_path}")
        return output_path
