"""
Visualization Modules for Phase 4 Enhanced Reporting
=====================================================

This package provides visualization components for the prosecutorial dossier:

- timeline_generator.py: Transaction timeline with material events
- network_graph.py: Actor network visualization
- heat_map.py: Trading intensity heatmap
- merkle_tree_viz.py: Evidence chain visualization
"""

from .timeline_generator import TimelineGenerator
from .network_graph import NetworkGraphGenerator
from .heat_map import HeatMapGenerator
from .merkle_tree_viz import MerkleTreeVisualizer

__all__ = [
    "TimelineGenerator",
    "NetworkGraphGenerator",
    "HeatMapGenerator",
    "MerkleTreeVisualizer",
]
