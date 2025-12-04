"""
Decision Tree - Core decision tree structure for prosecution paths.
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of decision nodes."""
    ROOT = "root"
    INVESTIGATION = "investigation"
    CRIMINAL = "criminal"
    CIVIL = "civil"
    ADMINISTRATIVE = "administrative"
    OUTCOME = "outcome"


class OutcomeType(Enum):
    """Types of prosecution outcomes."""
    CRIMINAL_CHARGES = "criminal_charges"
    CIVIL_PENALTIES = "civil_penalties"
    ADMINISTRATIVE_ACTION = "administrative_action"
    SETTLEMENT = "settlement"
    DEFERRED_PROSECUTION = "deferred_prosecution"
    NO_ACTION = "no_action"


@dataclass
class DecisionBranch:
    """A branch in the decision tree."""
    condition: str
    probability: float
    target_node: 'DecisionNode'
    evidence_required: List[str] = field(default_factory=list)
    statutes_applicable: List[str] = field(default_factory=list)
    
    def evaluate_feasibility(self, available_evidence: Set[str]) -> float:
        """Evaluate if this branch is feasible given available evidence."""
        if not self.evidence_required:
            return self.probability
        
        matching = len(set(self.evidence_required) & available_evidence)
        required = len(self.evidence_required)
        
        return (matching / required) * self.probability


@dataclass
class PathScore:
    """Score for a prosecution path."""
    conviction_probability: float
    expected_penalty: float
    deterrence_effect: float
    expected_recovery: float
    resource_cost: float
    time_estimate_months: int
    overall_score: float
    
    def calculate_overall(self, weights: Dict[str, float]) -> float:
        """Calculate weighted overall score."""
        score = 0.0
        score += self.conviction_probability * weights.get('conviction', 0.4)
        score += self.expected_penalty * weights.get('penalty', 0.2)
        score += self.deterrence_effect * weights.get('deterrence', 0.2)
        score += self.expected_recovery * weights.get('recovery', 0.1)
        score -= self.resource_cost * weights.get('cost', 0.1)
        
        return max(0.0, min(1.0, score))


class DecisionNode:
    """A node in the decision tree representing a decision point or outcome."""
    
    def __init__(
        self,
        name: str,
        node_type: NodeType = NodeType.INVESTIGATION,
        description: str = ""
    ):
        """
        Initialize decision node.
        
        Args:
            name: Node name
            node_type: Type of node
            description: Node description
        """
        self.name = name
        self.node_type = node_type
        self.description = description
        self.branches: List[DecisionBranch] = []
        self.conditions: List[str] = []
        self.outcomes: List[OutcomeType] = []
        self.metadata: Dict[str, Any] = {}
        
        logger.debug(f"Created DecisionNode: {name} ({node_type.value})")
    
    def add_branch(
        self,
        condition: str,
        target: 'DecisionNode',
        probability: float = 1.0,
        evidence_required: Optional[List[str]] = None,
        statutes: Optional[List[str]] = None
    ):
        """Add a branch to this node."""
        branch = DecisionBranch(
            condition=condition,
            probability=probability,
            target_node=target,
            evidence_required=evidence_required or [],
            statutes_applicable=statutes or []
        )
        self.branches.append(branch)
        logger.debug(f"Added branch to {self.name}: {condition}")
    
    def add_condition(self, condition: str):
        """Add a condition to this node."""
        self.conditions.append(condition)
    
    def add_outcome(self, outcome: OutcomeType):
        """Add an outcome to this node."""
        self.outcomes.append(outcome)
    
    def is_terminal(self) -> bool:
        """Check if this is a terminal node (no branches)."""
        return len(self.branches) == 0
    
    def get_feasible_branches(
        self,
        available_evidence: Set[str],
        min_probability: float = 0.3
    ) -> List[DecisionBranch]:
        """Get feasible branches given available evidence."""
        feasible = []
        
        for branch in self.branches:
            feasibility = branch.evaluate_feasibility(available_evidence)
            if feasibility >= min_probability:
                feasible.append(branch)
        
        return sorted(feasible, key=lambda b: b.probability, reverse=True)
    
    def __repr__(self) -> str:
        return f"DecisionNode({self.name}, type={self.node_type.value}, branches={len(self.branches)})"


class DecisionTree:
    """
    Decision tree for prosecution path planning.
    
    Builds and evaluates decision trees for optimal prosecution strategy.
    """
    
    def __init__(self, root: DecisionNode):
        """
        Initialize decision tree.
        
        Args:
            root: Root node of the tree
        """
        self.root = root
        self.all_nodes: List[DecisionNode] = []
        self._build_node_index()
        
        logger.info(f"DecisionTree initialized with root: {root.name}")
    
    def _build_node_index(self):
        """Build index of all nodes in tree."""
        visited = set()
        queue = [self.root]
        
        while queue:
            node = queue.pop(0)
            if id(node) in visited:
                continue
            
            visited.add(id(node))
            self.all_nodes.append(node)
            
            for branch in node.branches:
                queue.append(branch.target_node)
        
        logger.debug(f"Indexed {len(self.all_nodes)} nodes")
    
    def get_all_paths(self, max_depth: int = 10) -> List[List[DecisionNode]]:
        """
        Get all paths from root to terminal nodes.
        
        Args:
            max_depth: Maximum path depth
        
        Returns:
            List of paths (each path is a list of nodes)
        """
        paths = []
        
        def dfs(node: DecisionNode, path: List[DecisionNode], depth: int):
            if depth > max_depth:
                return
            
            path = path + [node]
            
            if node.is_terminal():
                paths.append(path)
                return
            
            for branch in node.branches:
                dfs(branch.target_node, path, depth + 1)
        
        dfs(self.root, [], 0)
        
        logger.info(f"Found {len(paths)} paths in tree")
        return paths
    
    def find_optimal_path(
        self,
        available_evidence: Set[str],
        objectives: Dict[str, float],
        min_probability: float = 0.3
    ) -> Optional[List[DecisionNode]]:
        """
        Find optimal path through tree given evidence and objectives.
        
        Args:
            available_evidence: Set of available evidence types
            objectives: Objective weights
            min_probability: Minimum branch probability
        
        Returns:
            Optimal path or None
        """
        all_paths = self.get_all_paths()
        
        if not all_paths:
            return None
        
        # Score each path
        scored_paths = []
        for path in all_paths:
            score = self._score_path(path, available_evidence, objectives)
            scored_paths.append((path, score))
        
        # Return path with highest score
        best_path, best_score = max(scored_paths, key=lambda x: x[1])
        
        logger.info(f"Found optimal path with score {best_score:.2f}")
        return best_path
    
    def _score_path(
        self,
        path: List[DecisionNode],
        available_evidence: Set[str],
        objectives: Dict[str, float]
    ) -> float:
        """Score a path based on evidence and objectives."""
        if not path:
            return 0.0
        
        # Base score from path length (prefer shorter paths)
        score = 1.0 / len(path)
        
        # Add score for evidence availability
        evidence_score = 0.0
        evidence_count = 0
        
        for i in range(len(path) - 1):
            node = path[i]
            next_node = path[i + 1]
            
            # Find branch connecting these nodes
            for branch in node.branches:
                if branch.target_node == next_node:
                    feasibility = branch.evaluate_feasibility(available_evidence)
                    evidence_score += feasibility
                    evidence_count += 1
                    break
        
        if evidence_count > 0:
            score *= (evidence_score / evidence_count)
        
        # Add score for terminal outcome type
        terminal = path[-1]
        if terminal.outcomes:
            outcome_value = self._get_outcome_value(terminal.outcomes[0])
            score *= outcome_value
        
        return score
    
    def _get_outcome_value(self, outcome: OutcomeType) -> float:
        """Get value score for outcome type."""
        values = {
            OutcomeType.CRIMINAL_CHARGES: 1.0,
            OutcomeType.CIVIL_PENALTIES: 0.8,
            OutcomeType.DEFERRED_PROSECUTION: 0.7,
            OutcomeType.ADMINISTRATIVE_ACTION: 0.6,
            OutcomeType.SETTLEMENT: 0.5,
            OutcomeType.NO_ACTION: 0.1
        }
        return values.get(outcome, 0.5)
    
    def visualize(self) -> Dict[str, Any]:
        """Generate tree visualization data."""
        nodes = []
        edges = []
        
        visited = set()
        queue = [(self.root, None)]
        
        while queue:
            node, parent_id = queue.pop(0)
            node_id = id(node)
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            
            nodes.append({
                'id': node_id,
                'name': node.name,
                'type': node.node_type.value,
                'branches': len(node.branches),
                'terminal': node.is_terminal()
            })
            
            if parent_id is not None:
                edges.append({
                    'source': parent_id,
                    'target': node_id
                })
            
            for branch in node.branches:
                queue.append((branch.target_node, node_id))
        
        return {
            'nodes': nodes,
            'edges': edges,
            'root': id(self.root),
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tree statistics."""
        paths = self.get_all_paths()
        
        if not paths:
            return {'total_nodes': len(self.all_nodes), 'paths': 0}
        
        path_lengths = [len(p) for p in paths]
        
        return {
            'total_nodes': len(self.all_nodes),
            'total_paths': len(paths),
            'avg_path_length': sum(path_lengths) / len(path_lengths),
            'min_path_length': min(path_lengths),
            'max_path_length': max(path_lengths),
            'terminal_nodes': sum(1 for n in self.all_nodes if n.is_terminal())
        }

