"""
Neo4j Graph Database Client
============================

Client for Neo4j graph database integration for executive network analysis.

Provides:
- Connection management with authentication
- Cypher query execution
- Node and relationship CRUD operations
- Transaction support
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase, Driver, Session
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not available. Using mock implementation.")


@dataclass
class Neo4jConfig:
    """Configuration for Neo4j connection."""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60


class Neo4jGraphClient:
    """
    Client for Neo4j graph database operations.
    
    Manages executive network graph with:
    - Executive nodes
    - Company nodes
    - Board membership relationships
    - Officer relationships
    - Advisory relationships
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize Neo4j client.
        
        Args:
            config: Neo4j configuration (defaults to localhost)
        """
        self.config = config or Neo4jConfig()
        self.driver: Optional[Driver] = None
        self.logger = logger
        
        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j driver not available. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        if self.mock_mode:
            self.logger.info("Mock mode: Simulating Neo4j connection")
            return
        
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_acquisition_timeout=self.config.connection_acquisition_timeout
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            self.logger.info(f"Connected to Neo4j at {self.config.uri}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result records as dictionaries
        """
        if self.mock_mode:
            self.logger.debug(f"Mock query: {query}")
            return []
        
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def create_executive_node(
        self,
        cik: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an executive node.
        
        Args:
            cik: CIK number
            name: Executive name
            properties: Additional properties
        
        Returns:
            Created node data
        """
        props = properties or {}
        props.update({"cik": cik, "name": name})
        
        query = """
        MERGE (e:Executive {cik: $cik})
        SET e.name = $name
        SET e += $properties
        RETURN e
        """
        
        results = self.execute_query(
            query,
            {"cik": cik, "name": name, "properties": props}
        )
        
        return results[0] if results else {}
    
    def create_company_node(
        self,
        cik: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a company node.
        
        Args:
            cik: Company CIK
            name: Company name
            properties: Additional properties
        
        Returns:
            Created node data
        """
        props = properties or {}
        props.update({"cik": cik, "name": name})
        
        query = """
        MERGE (c:Company {cik: $cik})
        SET c.name = $name
        SET c += $properties
        RETURN c
        """
        
        results = self.execute_query(
            query,
            {"cik": cik, "name": name, "properties": props}
        )
        
        return results[0] if results else {}
    
    def create_board_membership(
        self,
        executive_cik: str,
        company_cik: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a board membership relationship.
        
        Args:
            executive_cik: Executive CIK
            company_cik: Company CIK
            start_date: Start date (ISO format)
            end_date: End date (ISO format, None if current)
            properties: Additional properties
        
        Returns:
            Created relationship data
        """
        props = properties or {}
        if start_date:
            props["start_date"] = start_date
        if end_date:
            props["end_date"] = end_date
        
        query = """
        MATCH (e:Executive {cik: $executive_cik})
        MATCH (c:Company {cik: $company_cik})
        MERGE (e)-[r:BOARD_MEMBER_OF]->(c)
        SET r += $properties
        RETURN r
        """
        
        results = self.execute_query(
            query,
            {
                "executive_cik": executive_cik,
                "company_cik": company_cik,
                "properties": props
            }
        )
        
        return results[0] if results else {}
    
    def create_officer_relationship(
        self,
        executive_cik: str,
        company_cik: str,
        title: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an officer relationship.
        
        Args:
            executive_cik: Executive CIK
            company_cik: Company CIK
            title: Officer title (CEO, CFO, etc.)
            start_date: Start date
            end_date: End date
            properties: Additional properties
        
        Returns:
            Created relationship data
        """
        props = properties or {}
        props["title"] = title
        if start_date:
            props["start_date"] = start_date
        if end_date:
            props["end_date"] = end_date
        
        query = """
        MATCH (e:Executive {cik: $executive_cik})
        MATCH (c:Company {cik: $company_cik})
        MERGE (e)-[r:OFFICER_OF]->(c)
        SET r += $properties
        RETURN r
        """
        
        results = self.execute_query(
            query,
            {
                "executive_cik": executive_cik,
                "company_cik": company_cik,
                "properties": props
            }
        )
        
        return results[0] if results else {}
    
    def create_advisor_relationship(
        self,
        advisor_name: str,
        company_cik: str,
        advisor_type: str,
        year: int,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an advisor relationship.
        
        Args:
            advisor_name: Advisor firm name
            company_cik: Company CIK
            advisor_type: Type (legal, auditor, compensation_consultant)
            year: Year of engagement
            properties: Additional properties
        
        Returns:
            Created relationship data
        """
        props = properties or {}
        props.update({"type": advisor_type, "year": year})
        
        query = """
        MERGE (a:Advisor {name: $advisor_name})
        MATCH (c:Company {cik: $company_cik})
        MERGE (a)-[r:ADVISES]->(c)
        SET r += $properties
        RETURN r
        """
        
        results = self.execute_query(
            query,
            {
                "advisor_name": advisor_name,
                "company_cik": company_cik,
                "properties": props
            }
        )
        
        return results[0] if results else {}
    
    def find_board_interlocks(
        self,
        min_companies: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find executives serving on multiple boards (board interlocks).
        
        Args:
            min_companies: Minimum number of boards to qualify
        
        Returns:
            List of executives with their board memberships
        """
        query = """
        MATCH (e:Executive)-[r:BOARD_MEMBER_OF]->(c:Company)
        WITH e, COUNT(c) as board_count, COLLECT(c.name) as companies
        WHERE board_count >= $min_companies
        RETURN e.cik as cik, e.name as name, board_count, companies
        ORDER BY board_count DESC
        """
        
        return self.execute_query(query, {"min_companies": min_companies})
    
    def find_revolving_door(
        self,
        time_window_days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Find executives who moved between companies (revolving door).
        
        Args:
            time_window_days: Time window to consider (days)
        
        Returns:
            List of executive movements
        """
        query = """
        MATCH (e:Executive)-[r1:OFFICER_OF]->(c1:Company)
        MATCH (e)-[r2:OFFICER_OF]->(c2:Company)
        WHERE c1 <> c2
        AND r1.end_date IS NOT NULL
        AND r2.start_date IS NOT NULL
        AND date(r2.start_date) - date(r1.end_date) <= duration({days: $days})
        RETURN e.cik as cik, e.name as name,
               c1.name as from_company, r1.title as from_title, r1.end_date as end_date,
               c2.name as to_company, r2.title as to_title, r2.start_date as start_date,
               duration.between(date(r1.end_date), date(r2.start_date)).days as days_between
        ORDER BY days_between ASC
        """
        
        return self.execute_query(query, {"days": time_window_days})
    
    def find_shared_advisors(
        self,
        company_ciks: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Find advisors shared between companies.
        
        Args:
            company_ciks: List of company CIKs to check
        
        Returns:
            List of shared advisors
        """
        query = """
        MATCH (a:Advisor)-[r:ADVISES]->(c:Company)
        WHERE c.cik IN $ciks
        WITH a, COUNT(DISTINCT c) as company_count, COLLECT(DISTINCT c.name) as companies
        WHERE company_count > 1
        RETURN a.name as advisor, company_count, companies
        ORDER BY company_count DESC
        """
        
        return self.execute_query(query, {"ciks": company_ciks})
    
    def get_executive_network(
        self,
        executive_cik: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get network of connections for an executive.
        
        Args:
            executive_cik: Executive CIK
            depth: Depth of network to traverse
        
        Returns:
            Network data with nodes and relationships
        """
        query = """
        MATCH path = (e:Executive {cik: $cik})-[*1..$depth]-(connected)
        RETURN path
        """
        
        results = self.execute_query(
            query,
            {"cik": executive_cik, "depth": depth}
        )
        
        # Extract nodes and relationships from paths
        nodes = []
        relationships = []
        
        for result in results:
            path = result.get("path", [])
            # Process path data (simplified)
            nodes.append(path)
        
        return {
            "executive_cik": executive_cik,
            "depth": depth,
            "nodes": nodes,
            "relationships": relationships
        }
    
    def clear_database(self) -> None:
        """Clear all nodes and relationships (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        self.logger.warning("Database cleared")
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        stats = {}
        
        # Count executives
        result = self.execute_query("MATCH (e:Executive) RETURN COUNT(e) as count")
        stats["executives"] = result[0]["count"] if result else 0
        
        # Count companies
        result = self.execute_query("MATCH (c:Company) RETURN COUNT(c) as count")
        stats["companies"] = result[0]["count"] if result else 0
        
        # Count advisors
        result = self.execute_query("MATCH (a:Advisor) RETURN COUNT(a) as count")
        stats["advisors"] = result[0]["count"] if result else 0
        
        # Count relationships
        result = self.execute_query("MATCH ()-[r]->() RETURN COUNT(r) as count")
        stats["relationships"] = result[0]["count"] if result else 0
        
        return stats


class MockNeo4jGraphClient(Neo4jGraphClient):
    """Mock Neo4j client for testing without database."""
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        super().__init__(config)
        self.mock_mode = True
        self.mock_data = {
            "executives": {},
            "companies": {},
            "relationships": []
        }
    
    def connect(self) -> None:
        self.logger.info("Mock Neo4j client connected")
    
    def close(self) -> None:
        self.logger.info("Mock Neo4j client closed")
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Mock query: {query[:100]}...")
        # Return empty results for mock mode
        return []
