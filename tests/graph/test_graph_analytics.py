"""
Tests for Graph Analytics
"""

import pytest
from src.graph.graph_analytics import (
    GraphAnalytics,
    BoardInterlock,
    ExecutiveInfluence,
    Community
)


def test_board_interlock_dataclass():
    """Test BoardInterlock dataclass."""
    interlock = BoardInterlock(
        company1="Company A",
        company2="Company B",
        shared_directors=["John Doe", "Jane Smith"],
        interlock_count=2
    )
    
    assert interlock.company1 == "Company A"
    assert interlock.company2 == "Company B"
    assert len(interlock.shared_directors) == 2
    assert interlock.interlock_count == 2
    
    # Test to_dict
    interlock_dict = interlock.to_dict()
    assert interlock_dict["company1"] == "Company A"
    assert interlock_dict["interlock_count"] == 2


def test_executive_influence_dataclass():
    """Test ExecutiveInfluence dataclass."""
    influence = ExecutiveInfluence(
        name="John Doe",
        pagerank_score=0.15,
        betweenness_score=0.08,
        degree_centrality=5,
        board_memberships=3
    )
    
    assert influence.name == "John Doe"
    assert influence.pagerank_score == 0.15
    assert influence.board_memberships == 3
    
    # Test to_dict
    influence_dict = influence.to_dict()
    assert influence_dict["name"] == "John Doe"
    assert "pagerank_score" in influence_dict


def test_community_dataclass():
    """Test Community dataclass."""
    community = Community(
        community_id=1,
        members=["John Doe", "Jane Smith", "Bob Johnson"],
        size=3,
        companies={"Company A", "Company B"}
    )
    
    assert community.community_id == 1
    assert community.size == 3
    assert len(community.members) == 3
    assert len(community.companies) == 2
    
    # Test to_dict
    community_dict = community.to_dict()
    assert community_dict["community_id"] == 1
    assert community_dict["size"] == 3


def test_graph_analytics_initialization():
    """Test GraphAnalytics initialization."""
    analytics = GraphAnalytics(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test"
    )
    
    assert analytics.uri == "bolt://localhost:7687"
    assert analytics.user == "neo4j"


def test_mock_board_interlocks():
    """Test mock board interlock detection."""
    analytics = GraphAnalytics()
    
    # In mock mode, should return sample data
    interlocks = analytics._mock_board_interlocks()
    
    assert isinstance(interlocks, list)
    assert len(interlocks) > 0
    assert isinstance(interlocks[0], BoardInterlock)


def test_mock_pagerank():
    """Test mock PageRank calculation."""
    analytics = GraphAnalytics()
    
    # In mock mode, should return sample data
    executives = analytics._mock_pagerank()
    
    assert isinstance(executives, list)
    assert len(executives) > 0
    assert isinstance(executives[0], ExecutiveInfluence)


def test_mock_communities():
    """Test mock community detection."""
    analytics = GraphAnalytics()
    
    # In mock mode, should return sample data
    communities = analytics._mock_communities()
    
    assert isinstance(communities, list)
    assert len(communities) > 0
    assert isinstance(communities[0], Community)
