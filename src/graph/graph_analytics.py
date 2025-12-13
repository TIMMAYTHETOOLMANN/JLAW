"""
Graph Analytics for Executive Networks
======================================

Implements Neo4j GDS (Graph Data Science) library algorithms for
executive network analysis.

Algorithms:
- PageRank: Identifies influential executives
- Louvain: Detects communities (groups with shared connections)
- Betweenness Centrality: Finds network bridges/connectors

Use Cases:
- Board interlock detection (shared directors)
- Executive influence ranking
- Community detection (corporate cliques)
- Information flow analysis
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j not available. Using mock mode.")


@dataclass
class BoardInterlock:
    """Board interlock between two companies."""
    company1: str
    company2: str
    shared_directors: List[str]
    interlock_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company1": self.company1,
            "company2": self.company2,
            "shared_directors": self.shared_directors,
            "interlock_count": self.interlock_count
        }


@dataclass
class ExecutiveInfluence:
    """Executive influence metrics."""
    name: str
    pagerank_score: float
    betweenness_score: float
    degree_centrality: int  # Number of connections
    board_memberships: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pagerank_score": round(self.pagerank_score, 6),
            "betweenness_score": round(self.betweenness_score, 6),
            "degree_centrality": self.degree_centrality,
            "board_memberships": self.board_memberships
        }


@dataclass
class Community:
    """Detected community of executives."""
    community_id: int
    members: List[str]
    size: int
    companies: Set[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "community_id": self.community_id,
            "members": self.members,
            "size": self.size,
            "companies": list(self.companies)
        }


class GraphAnalytics:
    """
    Neo4j Graph Data Science analytics for executive networks.
    
    Features:
    - Board interlock detection (minimum 2 shared directors)
    - PageRank influence scoring (dampingFactor=0.85, maxIterations=20)
    - Louvain community detection
    - Betweenness centrality calculation
    - Temporal relationship queries (with startDate/endDate)
    
    Example:
        analytics = GraphAnalytics("bolt://localhost:7687", "neo4j", "password")
        
        # Find board interlocks
        interlocks = analytics.find_board_interlocks(min_shared=2)
        
        # Get influential executives
        top_execs = analytics.get_top_influential_executives(limit=10)
        
        # Detect communities
        communities = analytics.detect_communities()
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """
        Initialize graph analytics client.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        
        if NEO4J_AVAILABLE:
            self.mock_mode = False
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                logger.info(f"Connected to Neo4j at {uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self.mock_mode = True
        else:
            self.mock_mode = True
    
    def close(self):
        """Close connection."""
        if not self.mock_mode and hasattr(self, 'driver'):
            self.driver.close()
    
    def find_board_interlocks(
        self,
        min_shared: int = 2,
        active_only: bool = True
    ) -> List[BoardInterlock]:
        """
        Find board interlocks (companies sharing directors).
        
        Args:
            min_shared: Minimum number of shared directors (default: 2)
            active_only: Only consider current relationships
            
        Returns:
            List of BoardInterlock objects
        """
        if self.mock_mode:
            return self._mock_board_interlocks()
        
        # Cypher query to find board interlocks
        query = """
        MATCH (e:Executive)-[r1:BOARD_MEMBER]->(c1:Company)
        MATCH (e)-[r2:BOARD_MEMBER]->(c2:Company)
        WHERE c1 <> c2
        """
        
        if active_only:
            query += """
            AND (r1.endDate IS NULL OR r1.endDate > datetime())
            AND (r2.endDate IS NULL OR r2.endDate > datetime())
            """
        
        query += """
        WITH c1, c2, collect(DISTINCT e.name) AS shared_directors
        WHERE size(shared_directors) >= $min_shared
        RETURN c1.name AS company1, c2.name AS company2, 
               shared_directors, size(shared_directors) AS count
        ORDER BY count DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, min_shared=min_shared)
                
                interlocks = []
                seen_pairs = set()
                
                for record in result:
                    # Avoid duplicate pairs (A-B and B-A)
                    pair = tuple(sorted([record["company1"], record["company2"]]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        
                        interlocks.append(BoardInterlock(
                            company1=record["company1"],
                            company2=record["company2"],
                            shared_directors=record["shared_directors"],
                            interlock_count=record["count"]
                        ))
                
                return interlocks
        
        except Exception as e:
            logger.error(f"Board interlock query failed: {e}")
            return []
    
    def calculate_pagerank(
        self,
        max_iterations: int = 20,
        damping_factor: float = 0.85
    ) -> List[ExecutiveInfluence]:
        """
        Calculate PageRank scores for executives.
        
        Args:
            max_iterations: Maximum iterations (default: 20)
            damping_factor: Damping factor (default: 0.85)
            
        Returns:
            List of executives with PageRank scores
        """
        if self.mock_mode:
            return self._mock_pagerank()
        
        # PageRank via GDS library
        query = """
        CALL gds.pageRank.stream({
            nodeProjection: 'Executive',
            relationshipProjection: {
                BOARD_MEMBER: {orientation: 'UNDIRECTED'}
            },
            maxIterations: $max_iterations,
            dampingFactor: $damping_factor
        })
        YIELD nodeId, score
        MATCH (e:Executive) WHERE id(e) = nodeId
        OPTIONAL MATCH (e)-[:BOARD_MEMBER]->(c:Company)
        WITH e, score, count(c) AS board_count
        RETURN e.name AS name, score, board_count
        ORDER BY score DESC
        LIMIT 100
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    max_iterations=max_iterations,
                    damping_factor=damping_factor
                )
                
                executives = []
                for record in result:
                    executives.append(ExecutiveInfluence(
                        name=record["name"],
                        pagerank_score=record["score"],
                        betweenness_score=0.0,  # Calculated separately
                        degree_centrality=record["board_count"],
                        board_memberships=record["board_count"]
                    ))
                
                return executives
        
        except Exception as e:
            logger.error(f"PageRank calculation failed: {e}")
            # Try simpler query without GDS
            return self._calculate_simple_influence()
    
    def calculate_betweenness_centrality(self) -> List[Tuple[str, float]]:
        """
        Calculate betweenness centrality for executives.
        
        Betweenness centrality identifies executives who act as bridges
        between different parts of the network.
        
        Returns:
            List of (executive_name, betweenness_score) tuples
        """
        if self.mock_mode:
            return [("John Doe", 0.25), ("Jane Smith", 0.18)]
        
        query = """
        CALL gds.betweenness.stream({
            nodeProjection: 'Executive',
            relationshipProjection: {
                BOARD_MEMBER: {orientation: 'UNDIRECTED'}
            }
        })
        YIELD nodeId, score
        MATCH (e:Executive) WHERE id(e) = nodeId
        RETURN e.name AS name, score
        ORDER BY score DESC
        LIMIT 50
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [(record["name"], record["score"]) for record in result]
        
        except Exception as e:
            logger.error(f"Betweenness centrality failed: {e}")
            return []
    
    def detect_communities(self) -> List[Community]:
        """
        Detect communities using Louvain algorithm.
        
        Communities are groups of executives with dense connections
        (e.g., serving on same boards).
        
        Returns:
            List of Community objects
        """
        if self.mock_mode:
            return self._mock_communities()
        
        query = """
        CALL gds.louvain.stream({
            nodeProjection: 'Executive',
            relationshipProjection: {
                BOARD_MEMBER: {orientation: 'UNDIRECTED'}
            }
        })
        YIELD nodeId, communityId
        MATCH (e:Executive) WHERE id(e) = nodeId
        OPTIONAL MATCH (e)-[:BOARD_MEMBER]->(c:Company)
        WITH communityId, collect(e.name) AS members, collect(DISTINCT c.name) AS companies
        RETURN communityId, members, size(members) AS size, companies
        ORDER BY size DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                
                communities = []
                for record in result:
                    communities.append(Community(
                        community_id=record["communityId"],
                        members=record["members"],
                        size=record["size"],
                        companies=set(record["companies"])
                    ))
                
                return communities
        
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []
    
    def get_top_influential_executives(self, limit: int = 10) -> List[ExecutiveInfluence]:
        """
        Get top influential executives by combined metrics.
        
        Args:
            limit: Number of results to return
            
        Returns:
            List of ExecutiveInfluence objects
        """
        pagerank_results = self.calculate_pagerank()
        betweenness_results = dict(self.calculate_betweenness_centrality())
        
        # Merge results
        for exec_influence in pagerank_results:
            exec_influence.betweenness_score = betweenness_results.get(
                exec_influence.name, 0.0
            )
        
        # Sort by combined score (PageRank + Betweenness)
        pagerank_results.sort(
            key=lambda x: x.pagerank_score + x.betweenness_score,
            reverse=True
        )
        
        return pagerank_results[:limit]
    
    def find_revolving_door(
        self,
        min_companies: int = 3,
        time_window_years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find "revolving door" executives (moved between multiple companies).
        
        Args:
            min_companies: Minimum companies to flag
            time_window_years: Time window for transitions
            
        Returns:
            List of executives with company transitions
        """
        if self.mock_mode:
            return []
        
        query = """
        MATCH (e:Executive)-[r:OFFICER|BOARD_MEMBER]->(c:Company)
        WHERE r.startDate IS NOT NULL
        WITH e, c, r.startDate AS start_date
        ORDER BY e.name, start_date
        WITH e, collect({company: c.name, start_date: start_date}) AS transitions
        WHERE size(transitions) >= $min_companies
        RETURN e.name AS name, transitions, size(transitions) AS count
        ORDER BY count DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, min_companies=min_companies)
                return [dict(record) for record in result]
        
        except Exception as e:
            logger.error(f"Revolving door query failed: {e}")
            return []
    
    def _calculate_simple_influence(self) -> List[ExecutiveInfluence]:
        """Calculate simple influence without GDS."""
        query = """
        MATCH (e:Executive)-[:BOARD_MEMBER]->(c:Company)
        WITH e, count(c) AS board_count
        RETURN e.name AS name, board_count
        ORDER BY board_count DESC
        LIMIT 50
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                
                return [
                    ExecutiveInfluence(
                        name=record["name"],
                        pagerank_score=float(record["board_count"]) / 10,
                        betweenness_score=0.0,
                        degree_centrality=record["board_count"],
                        board_memberships=record["board_count"]
                    )
                    for record in result
                ]
        
        except Exception as e:
            logger.error(f"Simple influence query failed: {e}")
            return []
    
    def _mock_board_interlocks(self) -> List[BoardInterlock]:
        """Mock board interlocks."""
        return [
            BoardInterlock(
                company1="Company A",
                company2="Company B",
                shared_directors=["John Doe", "Jane Smith"],
                interlock_count=2
            )
        ]
    
    def _mock_pagerank(self) -> List[ExecutiveInfluence]:
        """Mock PageRank results."""
        return [
            ExecutiveInfluence(
                name="John Doe",
                pagerank_score=0.15,
                betweenness_score=0.0,
                degree_centrality=5,
                board_memberships=5
            )
        ]
    
    def _mock_communities(self) -> List[Community]:
        """Mock community detection."""
        return [
            Community(
                community_id=1,
                members=["John Doe", "Jane Smith"],
                size=2,
                companies={"Company A", "Company B"}
            )
        ]
