"""
Visualization Modules for Phase 4 Enhanced Reporting
=====================================================

This package provides visualization components for the prosecutorial dossier:

- timeline_generator.py: Transaction timeline with material events
- network_graph.py: Actor network visualization
- heat_map.py: Trading intensity heatmap
- merkle_tree_viz.py: Evidence chain visualization
- bubble_chart.py: Transaction and beneficiary bubble charts
- filing_deadline_chart.py: Filing deadline compliance visualization
- beneficiary_profit_chart.py: Financial beneficiary profit analysis
- financial_network_map.py: Multi-layer financial network and capital-flow map
"""

from .timeline_generator import TimelineGenerator
from .network_graph import NetworkGraphGenerator
from .heat_map import HeatMapGenerator
from .merkle_tree_viz import MerkleTreeVisualizer
from .bubble_chart import BubbleChartGenerator
from .filing_deadline_chart import FilingDeadlineChart
from .beneficiary_profit_chart import BeneficiaryProfitChart
from .financial_network_map import (
    FinancialNetworkMapper,
    FinancialNetworkData,
    NetworkNode,
    NetworkEdge,
)

__all__ = [
    "TimelineGenerator",
    "NetworkGraphGenerator",
    "HeatMapGenerator",
    "MerkleTreeVisualizer",
    "BubbleChartGenerator",
    "FilingDeadlineChart",
    "BeneficiaryProfitChart",
    # New: multi-layer financial network map
    "FinancialNetworkMapper",
    "FinancialNetworkData",
    "NetworkNode",
    "NetworkEdge",
]
