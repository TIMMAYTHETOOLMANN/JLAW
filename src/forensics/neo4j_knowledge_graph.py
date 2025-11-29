"""
Neo4j Knowledge Graph Foundation - Phase 3 Enhancement
Prepares for migration from NetworkX to Neo4j for scalable relationship analysis.

This module provides:
1. Neo4j schema design for forensic entities
2. Graph query interface for multi-hop traversal
3. Cypher query generation for investigations
4. GNN (Graph Neural Network) preparation
5. POLE model implementation (Person, Object, Location, Event)

When Neo4j is available, this enables:
- Billions of relationships (vs NetworkX millions)
- Multi-hop relationship traversal
- Graph algorithms (PageRank, community detection)
- Pattern matching across filings
- Temporal relationship evolution
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

# Optional Neo4j import
try:
    from neo4j import GraphDatabase, basic_auth
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None


class NodeType(Enum):
    """Forensic entity node types (POLE + Financial)."""
    PERSON = "PERSON"  # Executives, directors, auditors
    ORGANIZATION = "ORGANIZATION"  # Companies, subsidiaries
    LOCATION = "LOCATION"  # Addresses, jurisdictions
    EVENT = "EVENT"  # Transactions, filings, violations
    DOCUMENT = "DOCUMENT"  # SEC filings, exhibits
    CLAIM = "CLAIM"  # Extracted claims from filings
    ENTITY = "ENTITY"  # Financial entities (FinBERT)
    VIOLATION = "VIOLATION"  # Statute violations
    METRIC = "METRIC"  # Financial metrics


class RelationshipType(Enum):
    """Forensic relationship types."""
    # POLE relationships
    EMPLOYED_BY = "EMPLOYED_BY"
    LOCATED_AT = "LOCATED_AT"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    RELATED_TO = "RELATED_TO"
    
    # Document relationships
    FILED_BY = "FILED_BY"
    CONTAINS_CLAIM = "CONTAINS_CLAIM"
    MENTIONS_ENTITY = "MENTIONS_ENTITY"
    
    # Analysis relationships
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    VIOLATES = "VIOLATES"
    IMPLIES = "IMPLIES"
    
    # Temporal relationships
    PRECEDES = "PRECEDES"
    SUPERSEDES = "SUPERSEDES"
    AMENDS = "AMENDS"


@dataclass
class GraphNode:
    """Knowledge graph node."""
    id: str
    type: NodeType
    properties: Dict[str, Any]
    labels: List[str] = field(default_factory=list)


@dataclass
class GraphRelationship:
    """Knowledge graph relationship."""
    id: str
    type: RelationshipType
    from_node: str
    to_node: str
    properties: Dict[str, Any]


@dataclass
class GraphQuery:
    """Cypher query for Neo4j."""
    cypher: str
    parameters: Dict[str, Any]
    description: str


class Neo4jKnowledgeGraph:
    """
    Neo4j Knowledge Graph for Forensic Analysis.
    
    Provides scalable graph database capabilities for:
    - Entity relationship analysis
    - Multi-hop contradiction detection
    - Temporal pattern recognition
    - Cross-filing correlation
    - POLE model investigation
    
    Falls back to in-memory graph if Neo4j unavailable.
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        fallback_mode: bool = True
    ):
        """
        Initialize Neo4j knowledge graph.
        
        Args:
            uri: Neo4j URI (e.g., 'bolt://localhost:7687')
            username: Neo4j username
            password: Neo4j password
            fallback_mode: Use in-memory fallback if Neo4j unavailable
        """
        self.logger = logging.getLogger("Neo4jKnowledgeGraph")
        self.fallback_mode = fallback_mode
        
        # Try to connect to Neo4j
        self.driver = None
        self.using_neo4j = False
        
        if NEO4J_AVAILABLE and uri and username and password:
            try:
                self.driver = GraphDatabase.driver(
                    uri,
                    auth=basic_auth(username, password)
                )
                self.using_neo4j = True
                self.logger.info("✅ Connected to Neo4j database")
            except Exception as e:
                self.logger.warning(f"⚠️ Neo4j connection failed: {e}")
                if not fallback_mode:
                    raise
        
        # Fallback to in-memory graph
        if not self.using_neo4j:
            self.logger.info("ℹ️ Using in-memory graph (Neo4j unavailable)")
            self._nodes: Dict[str, GraphNode] = {}
            self._relationships: List[GraphRelationship] = []
        else:
            self._nodes = {}
            self._relationships = []
    
    @property
    def nodes(self) -> Dict[str, GraphNode]:
        """Get all nodes."""
        return self._nodes
    
    @nodes.setter
    def nodes(self, value: Dict[str, GraphNode]):
        self._nodes = value
    
    @property
    def relationships(self) -> List[GraphRelationship]:
        """Get all relationships."""
        return self._relationships
    
    @relationships.setter
    def relationships(self, value: List[GraphRelationship]):
        self._relationships = value
    
    def create_node(self, node: GraphNode) -> str:
        """Create node in graph."""
        if self.using_neo4j:
            return self._create_node_neo4j(node)
        else:
            return self._create_node_memory(node)
    
    def _create_node_neo4j(self, node: GraphNode) -> str:
        """Create node in Neo4j."""
        with self.driver.session() as session:
            query = f"""
            CREATE (n:{node.type.value} {{id: $id}})
            SET n += $properties
            RETURN n.id as id
            """
            
            result = session.run(
                query,
                id=node.id,
                properties=node.properties
            )
            
            return result.single()['id']
    
    def _create_node_memory(self, node: GraphNode) -> str:
        """Create node in memory."""
        self.nodes[node.id] = node
        return node.id
    
    def create_relationship(
        self,
        from_or_rel: Union[GraphRelationship, str] = None,
        to_node_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        # Also accept keyword argument style
        from_node_id: Optional[str] = None,
        relationship: Optional[GraphRelationship] = None
    ) -> str:
        """Create relationship in graph.
        
        Can be called with either:
        1. A GraphRelationship object: create_relationship(rel) or create_relationship(relationship=rel)
        2. Individual parameters: create_relationship(from_id, to_id, rel_type, properties)
           or create_relationship(from_node_id=..., to_node_id=..., relationship_type=..., properties=...)
        """
        # Handle relationship keyword argument
        if relationship is not None:
            from_or_rel = relationship
        
        # Handle from_node_id keyword argument
        if from_node_id is not None:
            from_or_rel = from_node_id
        
        # Handle GraphRelationship object
        if isinstance(from_or_rel, GraphRelationship):
            rel = from_or_rel
        else:
            # Handle individual parameters
            if to_node_id is None or relationship_type is None:
                raise ValueError("to_node_id and relationship_type required when using string parameters")
            
            rel_id = f"rel:{hashlib.md5(f'{from_or_rel}:{to_node_id}:{relationship_type}'.encode()).hexdigest()[:12]}"
            
            # Map string to enum
            rel_type_map = {
                'IMPLEMENTS': RelationshipType.RELATED_TO,
                'INTERPRETS': RelationshipType.RELATED_TO,
                'VIOLATES': RelationshipType.VIOLATES,
                'CONTRADICTS': RelationshipType.CONTRADICTS,
                'SUPPORTS': RelationshipType.SUPPORTS,
            }
            rel_type_enum = rel_type_map.get(relationship_type, RelationshipType.RELATED_TO)
            
            rel = GraphRelationship(
                id=rel_id,
                type=rel_type_enum,
                from_node=from_or_rel,
                to_node=to_node_id,
                properties=properties or {'type': relationship_type}
            )
        
        if self.using_neo4j:
            return self._create_relationship_neo4j(rel)
        else:
            return self._create_relationship_memory(rel)
    
    def _create_relationship_neo4j(self, rel: GraphRelationship) -> str:
        """Create relationship in Neo4j."""
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $from_id}})
            MATCH (b {{id: $to_id}})
            CREATE (a)-[r:{rel.type.value} {{id: $rel_id}}]->(b)
            SET r += $properties
            RETURN r.id as id
            """
            
            result = session.run(
                query,
                from_id=rel.from_node,
                to_id=rel.to_node,
                rel_id=rel.id,
                properties=rel.properties
            )
            
            return result.single()['id']
    
    def _create_relationship_memory(self, rel: GraphRelationship) -> str:
        """Create relationship in memory."""
        self.relationships.append(rel)
        return rel.id
    
    def find_contradictions(
        self,
        cik: str,
        max_hops: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find contradictions using multi-hop traversal.
        
        Args:
            cik: Company CIK
            max_hops: Maximum relationship hops to traverse
        
        Returns:
            List of contradiction patterns found
        """
        if self.using_neo4j:
            return self._find_contradictions_neo4j(cik, max_hops)
        else:
            return self._find_contradictions_memory(cik, max_hops)
    
    def _find_contradictions_neo4j(
        self,
        cik: str,
        max_hops: int
    ) -> List[Dict[str, Any]]:
        """Find contradictions using Neo4j Cypher."""
        query = f"""
        MATCH (e:ENTITY {{cik: $cik}})<-[:MENTIONS_ENTITY]-(c1:CLAIM)
              -[:CONTRADICTS]->(c2:CLAIM)-[:MENTIONS_ENTITY]->(e)
        MATCH (c1)<-[:CONTAINS_CLAIM]-(d1:DOCUMENT)
        MATCH (c2)<-[:CONTAINS_CLAIM]-(d2:DOCUMENT)
        WHERE d1.filing_date < d2.filing_date
        RETURN c1.text AS claim1, 
               d1.filing_date AS date1,
               c2.text AS claim2, 
               d2.filing_date AS date2,
               c1.CONTRADICTS.severity AS severity
        ORDER BY severity DESC
        LIMIT 100
        """
        
        with self.driver.session() as session:
            result = session.run(query, cik=cik)
            return [dict(record) for record in result]
    
    def _find_contradictions_memory(
        self,
        cik: str,
        max_hops: int
    ) -> List[Dict[str, Any]]:
        """Find contradictions in memory graph."""
        contradictions = []
        
        # Find CONTRADICTS relationships
        for rel in self.relationships:
            if rel.type == RelationshipType.CONTRADICTS:
                contradictions.append({
                    'from': rel.from_node,
                    'to': rel.to_node,
                    'properties': rel.properties
                })
        
        return contradictions
    
    def generate_investigation_queries(
        self,
        case_id: str,
        cik: str
    ) -> List[GraphQuery]:
        """
        Generate Cypher queries for forensic investigation.
        
        Returns:
            List of investigation queries
        """
        queries = []
        
        # Query 1: Find all contradictions for company
        queries.append(GraphQuery(
            cypher="""
            MATCH (e:ENTITY {cik: $cik})<-[:MENTIONS_ENTITY]-(c1:CLAIM)
                  -[:CONTRADICTS]->(c2:CLAIM)-[:MENTIONS_ENTITY]->(e)
            MATCH (c1)<-[:CONTAINS_CLAIM]-(d1:DOCUMENT)
            MATCH (c2)<-[:CONTAINS_CLAIM]-(d2:DOCUMENT)
            RETURN c1, c2, d1, d2
            """,
            parameters={'cik': cik},
            description="Find all contradictions"
        ))
        
        # Query 2: Multi-hop entity network
        queries.append(GraphQuery(
            cypher="""
            MATCH path = (e:ENTITY {cik: $cik})-[*1..3]-(related)
            RETURN path, length(path) as hops
            ORDER BY hops
            """,
            parameters={'cik': cik},
            description="Entity network (3 hops)"
        ))
        
        # Query 3: Temporal violation evolution
        queries.append(GraphQuery(
            cypher="""
            MATCH (v:VIOLATION)<-[:VIOLATES]-(c:CLAIM)<-[:CONTAINS_CLAIM]-(d:DOCUMENT {cik: $cik})
            RETURN v.statute, d.filing_date, count(*) as occurrences
            ORDER BY d.filing_date
            """,
            parameters={'cik': cik},
            description="Violation timeline"
        ))
        
        # Query 4: Executive involvement network
        queries.append(GraphQuery(
            cypher="""
            MATCH (p:PERSON)-[:EMPLOYED_BY]->(o:ORGANIZATION {cik: $cik})
            MATCH (p)-[:PARTICIPATED_IN]->(e:EVENT)
            WHERE e.type IN ['filing', 'transaction', 'violation']
            RETURN p.name, count(e) as event_count, collect(e.type) as event_types
            ORDER BY event_count DESC
            """,
            parameters={'cik': cik},
            description="Executive involvement analysis"
        ))
        
        return queries
    
    def populate_from_investigation(
        self,
        investigation_result: Any
    ) -> Dict[str, int]:
        """
        Populate graph from investigation result.
        
        Args:
            investigation_result: AutonomousInvestigationResult
        
        Returns:
            Statistics (nodes/relationships created)
        """
        stats = {'nodes': 0, 'relationships': 0}
        
        # Create company node
        company_node = GraphNode(
            id=f"ORG_{investigation_result.cik}",
            type=NodeType.ORGANIZATION,
            properties={
                'cik': investigation_result.cik,
                'name': investigation_result.company_name,
                'investigation_case_id': investigation_result.case_id
            }
        )
        self.create_node(company_node)
        stats['nodes'] += 1
        
        # Create entity nodes from extraction
        if investigation_result.entities_extracted:
            for entity in investigation_result.entities_extracted.entities:
                entity_node = GraphNode(
                    id=f"ENTITY_{entity.start_char}_{entity.end_char}",
                    type=NodeType.ENTITY,
                    properties={
                        'text': entity.text,
                        'entity_type': entity.entity_type.value,
                        'confidence': entity.confidence,
                        'normalized_value': entity.normalized_value
                    }
                )
                self.create_node(entity_node)
                stats['nodes'] += 1
        
        # Create contradiction relationships
        if investigation_result.contradictions_detected:
            for i, contradiction in enumerate(investigation_result.contradictions_detected.contradictions_detected):
                # Create claim nodes
                claim1_node = GraphNode(
                    id=f"CLAIM_{i}_1",
                    type=NodeType.CLAIM,
                    properties={'text': contradiction.claim1}
                )
                claim2_node = GraphNode(
                    id=f"CLAIM_{i}_2",
                    type=NodeType.CLAIM,
                    properties={'text': contradiction.claim2}
                )
                
                self.create_node(claim1_node)
                self.create_node(claim2_node)
                stats['nodes'] += 2
                
                # Create contradiction relationship
                contradiction_rel = GraphRelationship(
                    id=f"CONTRADICTS_{i}",
                    type=RelationshipType.CONTRADICTS,
                    from_node=claim1_node.id,
                    to_node=claim2_node.id,
                    properties={
                        'confidence': contradiction.contradiction_score,
                        'severity': contradiction.confidence_level,
                        'method': contradiction.detection_method
                    }
                )
                self.create_relationship(contradiction_rel)
                stats['relationships'] += 1
        
        # Create violation nodes
        for violation in investigation_result.statute_violations:
            violation_node = GraphNode(
                id=f"VIOLATION_{violation.get('statute', 'UNKNOWN').replace(' ', '_')}",
                type=NodeType.VIOLATION,
                properties={
                    'statute': violation.get('statute'),
                    'type': violation.get('type'),
                    'evidence': violation.get('evidence'),
                    'confidence': violation.get('confidence')
                }
            )
            self.create_node(violation_node)
            stats['nodes'] += 1
        
        self.logger.info(f"✅ Graph populated: {stats['nodes']} nodes, {stats['relationships']} relationships")
        return stats
    
    # =========================================================================
    # Phase 3 Enhanced Methods - Legal Statute Correlation
    # =========================================================================
    
    def create_statute_node(
        self,
        citation: str,
        title: int,
        section: str,
        text: str,
        effective_date: Optional[datetime] = None
    ) -> str:
        """Create a statute node in the graph."""
        node_id = f"statute:{citation}"
        node = GraphNode(
            id=node_id,
            type=NodeType.DOCUMENT,
            properties={
                'citation': citation,
                'title_number': title,
                'section': section,
                'text': text,
                'effective_date': effective_date.isoformat() if effective_date else None,
                'document_type': 'statute'
            },
            labels=['Statute', 'Document']
        )
        self.create_node(node)
        return node_id
    
    def create_regulation_node(
        self,
        cfr_citation: str,
        cfr_title: int,
        part: str,
        section: str,
        text: str
    ) -> str:
        """Create a regulation node in the graph."""
        node_id = f"regulation:{cfr_citation}"
        node = GraphNode(
            id=node_id,
            type=NodeType.DOCUMENT,
            properties={
                'citation': cfr_citation,
                'cfr_title': cfr_title,
                'part': part,
                'section': section,
                'text': text,
                'document_type': 'regulation'
            },
            labels=['Regulation', 'Document']
        )
        self.create_node(node)
        return node_id
    
    def create_case_node(
        self,
        citation: str,
        court: str,
        decision_date: Optional[datetime] = None,
        outcome: Optional[str] = None
    ) -> str:
        """Create a case law node in the graph."""
        node_id = f"case:{citation}"
        node = GraphNode(
            id=node_id,
            type=NodeType.DOCUMENT,
            properties={
                'citation': citation,
                'court': court,
                'decision_date': decision_date.isoformat() if decision_date else None,
                'outcome': outcome,
                'document_type': 'case'
            },
            labels=['Case', 'Document']
        )
        self.create_node(node)
        return node_id
    
    def create_violation_node(
        self,
        violation_type: str,
        description: str,
        severity: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a violation node in the graph."""
        import hashlib
        node_id = f"violation:{hashlib.md5(f'{violation_type}:{description[:50]}'.encode()).hexdigest()[:12]}"
        node = GraphNode(
            id=node_id,
            type=NodeType.VIOLATION,
            properties={
                'violation_type': violation_type,
                'description': description,
                'severity': severity,
                'evidence': evidence or {},
                'detected_at': datetime.now(timezone.utc).isoformat()
            },
            labels=['Violation']
        )
        self.create_node(node)
        return node_id
    
    def query_statutes_by_title(self, title_number: int) -> List[GraphNode]:
        """Query statutes by title number."""
        results = []
        for node in self._nodes.values():
            if (node.properties.get('document_type') == 'statute' and 
                node.properties.get('title_number') == title_number):
                results.append(node)
        return results
    
    def query_violations_by_severity(self, severity: str) -> List[GraphNode]:
        """Query violations by severity level."""
        results = []
        for node in self._nodes.values():
            if (node.type == NodeType.VIOLATION and 
                node.properties.get('severity') == severity):
                results.append(node)
        return results
    
    def get_statute_network(
        self,
        statute_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get network of relationships around a statute."""
        related_nodes = set()
        related_rels = []
        
        # BFS to find connected nodes
        to_visit = {statute_id}
        visited = set()
        
        for _ in range(depth):
            next_visit = set()
            for node_id in to_visit:
                if node_id in visited:
                    continue
                visited.add(node_id)
                related_nodes.add(node_id)
                
                # Find relationships involving this node
                for rel in self._relationships:
                    if rel.from_node == node_id:
                        related_rels.append(rel)
                        next_visit.add(rel.to_node)
                    elif rel.to_node == node_id:
                        related_rels.append(rel)
                        next_visit.add(rel.from_node)
            
            to_visit = next_visit - visited
        
        return {
            'center_node': statute_id,
            'node_count': len(related_nodes),
            'relationship_count': len(related_rels),
            'nodes': list(related_nodes),
            'relationships': [
                {'from': r.from_node, 'to': r.to_node, 'type': r.type.value}
                for r in related_rels
            ]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_types = {}
        for node in self._nodes.values():
            type_name = node.type.value
            node_types[type_name] = node_types.get(type_name, 0) + 1
        
        rel_types = {}
        for rel in self._relationships:
            type_name = rel.type.value
            rel_types[type_name] = rel_types.get(type_name, 0) + 1
        
        return {
            'total_nodes': len(self._nodes),
            'total_relationships': len(self._relationships),
            'using_neo4j': self.using_neo4j,
            'node_types': node_types,
            'relationship_types': rel_types
        }
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.logger.info("Neo4j connection closed")


# Integration helper for autonomous engine
async def create_knowledge_graph_from_investigation(
    investigation_result: Any,
    neo4j_uri: Optional[str] = None,
    neo4j_username: Optional[str] = None,
    neo4j_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create knowledge graph from investigation results.
    
    Example:
        graph_stats = await create_knowledge_graph_from_investigation(
            investigation_result=result,
            neo4j_uri="bolt://localhost:7687",
            neo4j_username="neo4j",
            neo4j_password="password"
        )
    """
    kg = Neo4jKnowledgeGraph(
        uri=neo4j_uri,
        username=neo4j_username,
        password=neo4j_password,
        fallback_mode=True
    )
    
    stats = kg.populate_from_investigation(investigation_result)
    
    # Generate investigation queries
    queries = kg.generate_investigation_queries(
        case_id=investigation_result.case_id,
        cik=investigation_result.cik
    )
    
    return {
        'statistics': stats,
        'using_neo4j': kg.using_neo4j,
        'queries_generated': len(queries),
        'investigation_queries': [
            {
                'description': q.description,
                'cypher': q.cypher
            }
            for q in queries
        ]
    }

