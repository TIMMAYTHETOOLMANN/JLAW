"""
Neo4j Knowledge Graph - Legal Relationship Modeling
===================================================

In-memory graph database for legal relationships:
- Statute nodes with metadata
- Regulation nodes
- Case law nodes
- Violation nodes
- Relationship types (AMENDS, IMPLEMENTS, INTERPRETS, etc.)
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Generic graph node"""
    node_id: str
    node_type: str  # 'statute', 'regulation', 'case', 'violation'
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphRelationship:
    """Graph relationship between nodes"""
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: str  # 'AMENDS', 'IMPLEMENTS', 'INTERPRETS', 'VIOLATES', 'CITES'
    properties: Dict[str, Any] = field(default_factory=dict)


class Neo4jKnowledgeGraph:
    """
    In-memory implementation of Neo4j-style knowledge graph
    for legal relationship modeling
    """
    
    RELATIONSHIP_TYPES = [
        'AMENDS',      # Statute amends another statute
        'IMPLEMENTS',  # Regulation implements statute
        'INTERPRETS',  # Case interprets statute
        'VIOLATES',    # Violation of statute
        'CITES',       # Document cites another
        'SUPERSEDES',  # Newer law supersedes older
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize knowledge graph
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # In-memory storage
        self._nodes: Dict[str, GraphNode] = {}
        self._relationships: Dict[str, GraphRelationship] = {}
        self._adjacency: Dict[str, Set[str]] = {}  # node_id -> set of relationship_ids
        
        # Statistics
        self.stats = {
            'nodes_created': 0,
            'relationships_created': 0,
            'queries_executed': 0
        }
        
        logger.info("🕸️ Neo4j Knowledge Graph initialized (in-memory)")
    
    def create_statute_node(
        self,
        citation: str,
        title: int,
        section: str,
        text: str = "",
        effective_date: Optional[str] = None
    ) -> str:
        """Create a statute node"""
        node_id = f"statute_{title}_{section}".replace(" ", "_")
        
        node = GraphNode(
            node_id=node_id,
            node_type='statute',
            properties={
                'citation': citation,
                'title': title,
                'section': section,
                'text': text,
                'effective_date': effective_date
            }
        )
        
        self._nodes[node_id] = node
        self._adjacency[node_id] = set()
        self.stats['nodes_created'] += 1
        
        return node_id
    
    def create_regulation_node(
        self,
        citation: str,
        cfr_title: int,
        part: str,
        section: str = "",
        text: str = ""
    ) -> str:
        """Create a regulation node"""
        node_id = f"regulation_{cfr_title}_{part}_{section}".replace(" ", "_")
        
        node = GraphNode(
            node_id=node_id,
            node_type='regulation',
            properties={
                'citation': citation,
                'cfr_title': cfr_title,
                'part': part,
                'section': section,
                'text': text
            }
        )
        
        self._nodes[node_id] = node
        self._adjacency[node_id] = set()
        self.stats['nodes_created'] += 1
        
        return node_id
    
    def create_case_node(
        self,
        citation: str,
        court: str,
        decision_date: str,
        outcome: str = ""
    ) -> str:
        """Create a case law node"""
        node_id = f"case_{citation}".replace(" ", "_").replace(".", "_")
        
        node = GraphNode(
            node_id=node_id,
            node_type='case',
            properties={
                'citation': citation,
                'court': court,
                'decision_date': decision_date,
                'outcome': outcome
            }
        )
        
        self._nodes[node_id] = node
        self._adjacency[node_id] = set()
        self.stats['nodes_created'] += 1
        
        return node_id
    
    def create_violation_node(
        self,
        violation_type: str,
        description: str,
        severity: str = "HIGH",
        evidence: str = ""
    ) -> str:
        """Create a violation node"""
        node_id = f"violation_{len(self._nodes)}_{violation_type}".replace(" ", "_")
        
        node = GraphNode(
            node_id=node_id,
            node_type='violation',
            properties={
                'violation_type': violation_type,
                'description': description,
                'severity': severity,
                'evidence': evidence
            }
        )
        
        self._nodes[node_id] = node
        self._adjacency[node_id] = set()
        self.stats['nodes_created'] += 1
        
        return node_id
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a relationship between nodes"""
        if source_id not in self._nodes:
            raise ValueError(f"Source node not found: {source_id}")
        if target_id not in self._nodes:
            raise ValueError(f"Target node not found: {target_id}")
        if relationship_type not in self.RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship type: {relationship_type}")
        
        rel_id = f"rel_{len(self._relationships)}_{relationship_type}"
        
        relationship = GraphRelationship(
            relationship_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {}
        )
        
        self._relationships[rel_id] = relationship
        self._adjacency[source_id].add(rel_id)
        self._adjacency[target_id].add(rel_id)
        self.stats['relationships_created'] += 1
        
        return rel_id
    
    def query_statutes_by_title(self, title: int) -> List[GraphNode]:
        """Query all statutes in a title"""
        self.stats['queries_executed'] += 1
        
        return [
            node for node in self._nodes.values()
            if node.node_type == 'statute' and node.properties.get('title') == title
        ]
    
    def get_related_nodes(
        self,
        node_id: str,
        relationship_type: Optional[str] = None,
        direction: str = 'both'
    ) -> List[GraphNode]:
        """Get nodes related to a given node"""
        self.stats['queries_executed'] += 1
        
        if node_id not in self._nodes:
            return []
        
        related = []
        for rel_id in self._adjacency.get(node_id, set()):
            rel = self._relationships[rel_id]
            
            if relationship_type and rel.relationship_type != relationship_type:
                continue
            
            if direction == 'outgoing' and rel.source_id != node_id:
                continue
            if direction == 'incoming' and rel.target_id != node_id:
                continue
            
            other_id = rel.target_id if rel.source_id == node_id else rel.source_id
            if other_id in self._nodes:
                related.append(self._nodes[other_id])
        
        return related
    
    def get_statute_network(
        self,
        node_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Get network of related nodes up to specified depth"""
        self.stats['queries_executed'] += 1
        
        visited = set()
        network_nodes = []
        network_relationships = []
        
        def traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            
            visited.add(current_id)
            if current_id in self._nodes:
                network_nodes.append(self._nodes[current_id])
            
            for rel_id in self._adjacency.get(current_id, set()):
                rel = self._relationships[rel_id]
                network_relationships.append(rel)
                
                other_id = rel.target_id if rel.source_id == current_id else rel.source_id
                traverse(other_id, current_depth + 1)
        
        traverse(node_id, 0)
        
        return {
            'node_count': len(network_nodes),
            'relationship_count': len(network_relationships),
            'nodes': [
                {'id': n.node_id, 'type': n.node_type, 'properties': n.properties}
                for n in network_nodes
            ],
            'relationships': [
                {'id': r.relationship_id, 'source': r.source_id, 'target': r.target_id, 'type': r.relationship_type}
                for r in network_relationships
            ]
        }
    
    def export_cypher(self) -> str:
        """Export graph as Cypher statements for Neo4j"""
        statements = []
        
        # Create nodes
        for node in self._nodes.values():
            props = ', '.join(f'{k}: "{v}"' for k, v in node.properties.items() if v)
            statements.append(f"CREATE (n:{node.node_type} {{{props}}})")
        
        # Create relationships
        for rel in self._relationships.values():
            statements.append(
                f"MATCH (a), (b) WHERE a.id = '{rel.source_id}' AND b.id = '{rel.target_id}' "
                f"CREATE (a)-[:{rel.relationship_type}]->(b)"
            )
        
        return ";\n".join(statements)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            **self.stats,
            'total_nodes': len(self._nodes),
            'total_relationships': len(self._relationships),
            'node_types': list(set(n.node_type for n in self._nodes.values())),
            'relationship_types': list(set(r.relationship_type for r in self._relationships.values()))
        }


if __name__ == "__main__":
    # Demo usage
    graph = Neo4jKnowledgeGraph()
    
    # Create nodes
    stat_id = graph.create_statute_node(
        citation="15 USC § 78j",
        title=15,
        section="78j",
        text="Securities Exchange Act Section 10(b)"
    )
    
    reg_id = graph.create_regulation_node(
        citation="17 CFR § 240.10b-5",
        cfr_title=17,
        part="240",
        section="10b-5"
    )
    
    # Create relationship
    graph.create_relationship(
        source_id=reg_id,
        target_id=stat_id,
        relationship_type='IMPLEMENTS'
    )
    
    # Query
    network = graph.get_statute_network(stat_id)
    print(f"Network: {network['node_count']} nodes, {network['relationship_count']} relationships")
    print(f"Stats: {graph.get_statistics()}")
