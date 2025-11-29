"""
Prosecution Path Builder
Builds optimal prosecution paths integrating all forensic modules.
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

from .decision_tree import DecisionTree, DecisionNode, NodeType, OutcomeType, PathScore
from .evidence_evaluator import (
    ForensicEvidenceEvaluator, Evidence, EvaluatedEvidence, EvidenceType
)

logger = logging.getLogger(__name__)


class ProsecutionObjective(Enum):
    """Prosecution objectives."""
    MAXIMIZE_PENALTIES = "maximize_penalties"
    ENSURE_CONVICTION = "ensure_conviction"
    DETER_FUTURE_VIOLATIONS = "deter_future_violations"
    RECOVER_DAMAGES = "recover_damages"
    PRESERVE_RESOURCES = "preserve_resources"
    EXPEDITE_RESOLUTION = "expedite_resolution"


class EnforcementAction(Enum):
    """Types of enforcement actions."""
    DOJ_CRIMINAL_REFERRAL = "doj_criminal_referral"
    SEC_CIVIL_ACTION = "sec_civil_action"
    STATE_PROSECUTION = "state_prosecution"
    ADMINISTRATIVE_PROCEEDING = "administrative_proceeding"
    SETTLEMENT_NEGOTIATION = "settlement_negotiation"
    DEFERRED_PROSECUTION_AGREEMENT = "deferred_prosecution_agreement"


@dataclass
class DecisionPath:
    """A path through the decision tree."""
    nodes: List[DecisionNode]
    actions: List[EnforcementAction]
    expected_outcome: OutcomeType
    score: PathScore
    timeline_months: int
    resource_requirements: Dict[str, Any]
    risks: List[str] = field(default_factory=list)
    success_probability: float = 0.0


@dataclass
class ProsecutionStrategy:
    """Complete prosecution strategy."""
    primary_action: EnforcementAction
    supporting_actions: List[EnforcementAction]
    legal_theories: List[str]
    statutes_invoked: List[str]
    evidence_plan: Dict[str, List[str]]
    timeline: Dict[str, datetime]
    resource_allocation: Dict[str, float]
    contingencies: List[str]


@dataclass
class ProsecutionPath:
    """Complete prosecution path with all details."""
    target_entity: str
    path: DecisionPath
    strategy: ProsecutionStrategy
    evidence: List[EvaluatedEvidence]
    success_probability: float
    alternative_paths: List[DecisionPath]
    risks: List[str]
    timeline: Dict[str, datetime]
    resources: Dict[str, Any]
    
    # Integration with forensic modules
    timeline_analysis: Optional[Any] = None  # From Phase 4
    contradictions: List[Any] = field(default_factory=list)  # From Phase 4
    statute_violations: List[Any] = field(default_factory=list)  # From Phase 3
    intelligence_sources: List[Any] = field(default_factory=list)  # From Phase 2
    
    # Recommendations
    recommended_action: str = ""
    next_steps: List[str] = field(default_factory=list)


class ProsecutionPathBuilder:
    """
    Prosecution Path Builder - Phase 5
    
    Integrates all forensic modules to build optimal prosecution strategies.
    
    Integrations:
    - Phase 1: Document parsing for evidence extraction
    - Phase 2: Intelligence gathering for context
    - Phase 3: Statute mapping for legal foundation
    - Phase 4: Timeline analysis for temporal evidence
    """
    
    def __init__(self):
        """Initialize prosecution path builder."""
        self.evidence_evaluator = ForensicEvidenceEvaluator()
        logger.info("ProsecutionPathBuilder initialized")
    
    async def build_prosecution_path(
        self,
        evidence: List[Evidence],
        target_entity: str,
        objectives: List[ProsecutionObjective],
        case_context: Optional[Dict[str, Any]] = None
    ) -> ProsecutionPath:
        """
        Build optimal prosecution path.
        
        Args:
            evidence: Available evidence
            target_entity: Target entity/person
            objectives: Prosecution objectives
            case_context: Optional case context with forensic analysis
        
        Returns:
            Complete prosecution path
        """
        logger.info(f"Building prosecution path for {target_entity}...")
        logger.info(f"Evidence pieces: {len(evidence)}, Objectives: {len(objectives)}")
        
        case_context = case_context or {}
        
        # Step 1: Evaluate all evidence
        logger.info("Step 1: Evaluating evidence...")
        evaluated_evidence = await self.evidence_evaluator.evaluate(
            evidence, case_context
        )
        
        # Step 2: Build decision tree based on evidence
        logger.info("Step 2: Building decision tree...")
        tree = await self._build_decision_tree(evaluated_evidence, objectives)
        
        # Step 3: Find optimal path
        logger.info("Step 3: Finding optimal path...")
        optimal_path = self._find_optimal_path(tree, evaluated_evidence, objectives)
        
        # Step 4: Generate strategy
        logger.info("Step 4: Generating prosecution strategy...")
        strategy = await self._generate_strategy(optimal_path, evaluated_evidence)
        
        # Step 5: Calculate success probability
        logger.info("Step 5: Calculating success probability...")
        success_prob = self._calculate_success_probability(
            optimal_path, evaluated_evidence
        )
        
        # Step 6: Find alternative paths
        logger.info("Step 6: Finding alternative paths...")
        alternatives = self._find_alternative_paths(tree, evaluated_evidence, objectives)
        
        # Step 7: Identify risks
        logger.info("Step 7: Identifying risks...")
        risks = self._identify_risks(optimal_path, evaluated_evidence)
        
        # Step 8: Generate timeline
        logger.info("Step 8: Generating timeline...")
        timeline = self._generate_timeline(optimal_path)
        
        # Step 9: Estimate resources
        logger.info("Step 9: Estimating resources...")
        resources = self._estimate_resources(optimal_path)
        
        # Step 10: Generate recommendations
        logger.info("Step 10: Generating recommendations...")
        recommended_action, next_steps = self._generate_recommendations(
            optimal_path, success_prob, evaluated_evidence
        )
        
        # Build complete path with forensic integration
        path = ProsecutionPath(
            target_entity=target_entity,
            path=optimal_path,
            strategy=strategy,
            evidence=evaluated_evidence,
            success_probability=success_prob,
            alternative_paths=alternatives,
            risks=risks,
            timeline=timeline,
            resources=resources,
            timeline_analysis=case_context.get('timeline_analysis'),
            contradictions=case_context.get('contradictions', []),
            statute_violations=case_context.get('statute_violations', []),
            intelligence_sources=case_context.get('intelligence_sources', []),
            recommended_action=recommended_action,
            next_steps=next_steps
        )
        
        logger.info(f"Prosecution path built. Success probability: {success_prob:.2%}")
        return path
    
    async def _build_decision_tree(
        self,
        evidence: List[EvaluatedEvidence],
        objectives: List[ProsecutionObjective]
    ) -> DecisionTree:
        """Build decision tree based on available evidence."""
        root = DecisionNode("Start Investigation", NodeType.ROOT)
        
        # Classify evidence by strength
        strong_evidence = [e for e in evidence if e.weight > 0.7]
        moderate_evidence = [e for e in evidence if 0.4 < e.weight <= 0.7]
        weak_evidence = [e for e in evidence if e.weight <= 0.4]
        
        logger.debug(f"Evidence classification: {len(strong_evidence)} strong, "
                    f"{len(moderate_evidence)} moderate, {len(weak_evidence)} weak")
        
        # Criminal path (requires strong evidence)
        if strong_evidence:
            criminal_node = DecisionNode("Criminal Prosecution", NodeType.CRIMINAL)
            criminal_node.add_condition("Strong evidence available")
            
            # DOJ referral
            if self._has_federal_violations(evidence):
                doj_node = DecisionNode("DOJ Criminal Referral", NodeType.OUTCOME)
                doj_node.add_outcome(OutcomeType.CRIMINAL_CHARGES)
                criminal_node.add_branch(
                    "Federal violations present",
                    doj_node,
                    probability=0.8,
                    evidence_required=['financial_fraud', 'securities_fraud'],
                    statutes=['15 USC 78j(b)', '18 USC 1348']
                )
            
            # State prosecution
            if self._has_state_violations(evidence):
                state_node = DecisionNode("State Prosecution", NodeType.OUTCOME)
                state_node.add_outcome(OutcomeType.CRIMINAL_CHARGES)
                criminal_node.add_branch(
                    "State law violations",
                    state_node,
                    probability=0.7,
                    evidence_required=['fraud', 'theft'],
                    statutes=['State Penal Code']
                )
            
            root.add_branch("Strong criminal evidence", criminal_node, probability=0.9)
        
        # Civil path (moderate evidence acceptable)
        if moderate_evidence or strong_evidence:
            civil_node = DecisionNode("Civil Enforcement", NodeType.CIVIL)
            civil_node.add_condition("Civil remedies available")
            
            # SEC enforcement
            sec_node = DecisionNode("SEC Enforcement Action", NodeType.OUTCOME)
            sec_node.add_outcome(OutcomeType.CIVIL_PENALTIES)
            civil_node.add_branch(
                "Securities violations",
                sec_node,
                probability=0.85,
                evidence_required=['disclosure_violation', 'accounting_fraud'],
                statutes=['Securities Act 1933', 'Exchange Act 1934']
            )
            
            # Private litigation
            litigation_node = DecisionNode("Private Litigation", NodeType.OUTCOME)
            litigation_node.add_outcome(OutcomeType.CIVIL_PENALTIES)
            civil_node.add_branch(
                "Damages demonstrable",
                litigation_node,
                probability=0.75,
                evidence_required=['financial_harm'],
                statutes=['State tort law']
            )
            
            root.add_branch("Civil enforcement viable", civil_node, probability=0.8)
        
        # Administrative path (always available)
        admin_node = DecisionNode("Administrative Action", NodeType.ADMINISTRATIVE)
        admin_node.add_condition("Regulatory authority")
        
        compliance_node = DecisionNode("Compliance Order", NodeType.OUTCOME)
        compliance_node.add_outcome(OutcomeType.ADMINISTRATIVE_ACTION)
        admin_node.add_branch(
            "Regulatory violations",
            compliance_node,
            probability=0.95,
            statutes=['Regulatory framework']
        )
        
        root.add_branch("Administrative action", admin_node, probability=0.9)
        
        # Settlement path
        if ProsecutionObjective.EXPEDITE_RESOLUTION in objectives:
            settlement_node = DecisionNode("Settlement", NodeType.OUTCOME)
            settlement_node.add_outcome(OutcomeType.SETTLEMENT)
            root.add_branch("Settlement option", settlement_node, probability=0.7)
        
        tree = DecisionTree(root)
        logger.info(f"Decision tree built: {tree.get_statistics()}")
        
        return tree
    
    def _find_optimal_path(
        self,
        tree: DecisionTree,
        evidence: List[EvaluatedEvidence],
        objectives: List[ProsecutionObjective]
    ) -> DecisionPath:
        """Find optimal path through decision tree."""
        # Get available evidence types
        available_evidence = set()
        for ev in evidence:
            if ev.weight > 0.5:
                available_evidence.add(ev.evidence.evidence_type.value)
                # Add specific fraud types
                if 'fraud' in ev.evidence.description.lower():
                    available_evidence.add('fraud')
                if 'securities' in ev.evidence.description.lower():
                    available_evidence.add('securities_fraud')
        
        # Convert objectives to weights
        objective_weights = self._objectives_to_weights(objectives)
        
        # Find optimal path
        path_nodes = tree.find_optimal_path(
            available_evidence,
            objective_weights,
            min_probability=0.3
        )
        
        if not path_nodes:
            # Fallback to administrative path
            logger.warning("No optimal path found, defaulting to administrative")
            path_nodes = [tree.root]
        
        # Extract actions and outcome
        actions = self._extract_actions(path_nodes)
        outcome = path_nodes[-1].outcomes[0] if path_nodes[-1].outcomes else OutcomeType.NO_ACTION
        
        # Calculate path score
        score = self._calculate_path_score(path_nodes, evidence, objectives)
        
        # Estimate timeline
        timeline_months = self._estimate_timeline(outcome, len(evidence))
        
        # Estimate resources
        resources = {'investigators': 2, 'attorneys': 1, 'budget': 100000}
        
        # Identify risks
        risks = self._identify_path_risks(path_nodes, evidence)
        
        return DecisionPath(
            nodes=path_nodes,
            actions=actions,
            expected_outcome=outcome,
            score=score,
            timeline_months=timeline_months,
            resource_requirements=resources,
            risks=risks,
            success_probability=score.overall_score
        )
    
    async def _generate_strategy(
        self,
        path: DecisionPath,
        evidence: List[EvaluatedEvidence]
    ) -> ProsecutionStrategy:
        """Generate prosecution strategy."""
        # Determine primary action
        primary = path.actions[0] if path.actions else EnforcementAction.ADMINISTRATIVE_PROCEEDING
        supporting = path.actions[1:] if len(path.actions) > 1 else []
        
        # Extract legal theories
        legal_theories = [
            "Securities fraud via material misstatements",
            "Violation of disclosure requirements",
            "Accounting fraud and manipulation"
        ]
        
        # Extract statutes
        statutes = []
        for node in path.nodes:
            for branch in node.branches:
                statutes.extend(branch.statutes_applicable)
        statutes = list(set(statutes))  # Deduplicate
        
        # Build evidence plan
        evidence_plan = {
            'documentary': [e.evidence.id for e in evidence if e.evidence.evidence_type == EvidenceType.DOCUMENT],
            'financial': [e.evidence.id for e in evidence if e.evidence.evidence_type == EvidenceType.FINANCIAL_RECORD],
            'forensic': [e.evidence.id for e in evidence if e.evidence.evidence_type == EvidenceType.FORENSIC_ANALYSIS]
        }
        
        # Generate timeline
        now = datetime.now()
        timeline = {
            'investigation_start': now,
            'evidence_collection_complete': now + timedelta(days=90),
            'filing_deadline': now + timedelta(days=180),
            'trial_date': now + timedelta(days=365)
        }
        
        # Resource allocation
        resource_allocation = {
            'investigation': 0.4,
            'legal_analysis': 0.3,
            'trial_prep': 0.3
        }
        
        # Contingencies
        contingencies = [
            "If evidence inadmissible, seek corroboration",
            "If statute of limitations issue, expedite filing",
            "If settlement offered, evaluate cost-benefit"
        ]
        
        return ProsecutionStrategy(
            primary_action=primary,
            supporting_actions=supporting,
            legal_theories=legal_theories,
            statutes_invoked=statutes,
            evidence_plan=evidence_plan,
            timeline=timeline,
            resource_allocation=resource_allocation,
            contingencies=contingencies
        )
    
    def _calculate_success_probability(
        self,
        path: DecisionPath,
        evidence: List[EvaluatedEvidence]
    ) -> float:
        """Calculate probability of successful prosecution."""
        # Base probability from path
        base_prob = path.score.overall_score
        
        # Adjust for evidence strength
        avg_evidence_weight = sum(e.weight for e in evidence) / len(evidence) if evidence else 0.5
        
        # Adjust for admissibility
        admissible_count = sum(1 for e in evidence if e.admissibility.is_admissible)
        admissibility_ratio = admissible_count / len(evidence) if evidence else 0.5
        
        # Combined probability
        success_prob = base_prob * 0.4 + avg_evidence_weight * 0.3 + admissibility_ratio * 0.3
        
        return min(0.95, max(0.1, success_prob))
    
    def _find_alternative_paths(
        self,
        tree: DecisionTree,
        evidence: List[EvaluatedEvidence],
        objectives: List[ProsecutionObjective]
    ) -> List[DecisionPath]:
        """Find alternative prosecution paths."""
        # Get all possible paths
        all_paths = tree.get_all_paths()
        
        alternatives = []
        for path_nodes in all_paths[:3]:  # Top 3 alternatives
            if len(path_nodes) < 2:
                continue
            
            actions = self._extract_actions(path_nodes)
            outcome = path_nodes[-1].outcomes[0] if path_nodes[-1].outcomes else OutcomeType.NO_ACTION
            score = self._calculate_path_score(path_nodes, evidence, objectives)
            
            alternatives.append(DecisionPath(
                nodes=path_nodes,
                actions=actions,
                expected_outcome=outcome,
                score=score,
                timeline_months=12,
                resource_requirements={}
            ))
        
        return alternatives
    
    def _identify_risks(
        self,
        path: DecisionPath,
        evidence: List[EvaluatedEvidence]
    ) -> List[str]:
        """Identify prosecution risks."""
        risks = []
        
        # Evidence risks
        inadmissible = [e for e in evidence if not e.admissibility.is_admissible]
        if len(inadmissible) > len(evidence) * 0.3:
            risks.append("HIGH: Significant portion of evidence may be inadmissible")
        
        # Statute of limitations
        risks.append("MEDIUM: Monitor statute of limitations deadlines")
        
        # Resource risks
        if path.timeline_months > 24:
            risks.append("MEDIUM: Extended timeline may strain resources")
        
        # Defendant risks
        risks.append("MEDIUM: Well-funded defendant may mount strong defense")
        
        return risks
    
    def _generate_timeline(self, path: DecisionPath) -> Dict[str, datetime]:
        """Generate prosecution timeline."""
        now = datetime.now()
        
        timeline = {
            'investigation_complete': now + timedelta(days=90),
            'charges_filed': now + timedelta(days=180),
            'discovery_complete': now + timedelta(days=270),
            'trial_start': now + timedelta(days=365),
            'expected_resolution': now + timedelta(days=path.timeline_months * 30)
        }
        
        return timeline
    
    def _estimate_resources(self, path: DecisionPath) -> Dict[str, Any]:
        """Estimate resource requirements."""
        # Base on outcome type
        if path.expected_outcome == OutcomeType.CRIMINAL_CHARGES:
            return {
                'investigators': 4,
                'prosecutors': 2,
                'support_staff': 2,
                'budget': 500000,
                'expert_witnesses': 3
            }
        elif path.expected_outcome == OutcomeType.CIVIL_PENALTIES:
            return {
                'investigators': 2,
                'attorneys': 2,
                'support_staff': 1,
                'budget': 250000,
                'expert_witnesses': 2
            }
        else:
            return {
                'investigators': 1,
                'attorneys': 1,
                'budget': 100000
            }
    
    def _generate_recommendations(
        self,
        path: DecisionPath,
        success_prob: float,
        evidence: List[EvaluatedEvidence]
    ) -> tuple:
        """Generate recommendations."""
        # Recommended action
        if success_prob > 0.7:
            action = f"RECOMMEND: Proceed with {path.expected_outcome.value}"
        elif success_prob > 0.5:
            action = f"CONSIDER: {path.expected_outcome.value} with additional evidence"
        else:
            action = "CAUTION: Success probability low, consider alternative strategies"
        
        # Next steps
        next_steps = [
            "Complete evidence evaluation and authentication",
            "Consult with legal team on admissibility issues",
            "Prepare charging documents or complaint",
            "Identify and secure expert witnesses",
            "Monitor statute of limitations deadlines"
        ]
        
        return action, next_steps
    
    # Helper methods
    
    def _has_federal_violations(self, evidence: List[EvaluatedEvidence]) -> bool:
        """Check for federal violations in evidence."""
        for ev in evidence:
            desc = ev.evidence.description.lower()
            if any(term in desc for term in ['securities', 'wire fraud', 'federal']):
                return True
        return False
    
    def _has_state_violations(self, evidence: List[EvaluatedEvidence]) -> bool:
        """Check for state violations."""
        return True  # Default to true for flexibility
    
    def _objectives_to_weights(
        self,
        objectives: List[ProsecutionObjective]
    ) -> Dict[str, float]:
        """Convert objectives to scoring weights."""
        weights = {
            'conviction': 0.3,
            'penalty': 0.2,
            'deterrence': 0.2,
            'recovery': 0.15,
            'cost': 0.15
        }
        
        # Adjust based on objectives
        for obj in objectives:
            if obj == ProsecutionObjective.ENSURE_CONVICTION:
                weights['conviction'] = 0.5
            elif obj == ProsecutionObjective.MAXIMIZE_PENALTIES:
                weights['penalty'] = 0.4
            elif obj == ProsecutionObjective.RECOVER_DAMAGES:
                weights['recovery'] = 0.3
        
        # Normalize
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    def _extract_actions(self, nodes: List[DecisionNode]) -> List[EnforcementAction]:
        """Extract enforcement actions from path nodes."""
        actions = []
        
        for node in nodes:
            if 'DOJ' in node.name:
                actions.append(EnforcementAction.DOJ_CRIMINAL_REFERRAL)
            elif 'SEC' in node.name:
                actions.append(EnforcementAction.SEC_CIVIL_ACTION)
            elif 'State' in node.name:
                actions.append(EnforcementAction.STATE_PROSECUTION)
            elif 'Administrative' in node.name or 'Compliance' in node.name:
                actions.append(EnforcementAction.ADMINISTRATIVE_PROCEEDING)
            elif 'Settlement' in node.name:
                actions.append(EnforcementAction.SETTLEMENT_NEGOTIATION)
        
        return actions if actions else [EnforcementAction.ADMINISTRATIVE_PROCEEDING]
    
    def _calculate_path_score(
        self,
        nodes: List[DecisionNode],
        evidence: List[EvaluatedEvidence],
        objectives: List[ProsecutionObjective]
    ) -> PathScore:
        """Calculate score for a path."""
        # Base scores
        conviction_prob = 0.7  # Base probability
        expected_penalty = 1000000  # Base penalty
        deterrence = 0.8
        recovery = 500000
        cost = 0.3
        
        # Adjust for evidence quality
        if evidence:
            avg_weight = sum(e.weight for e in evidence) / len(evidence)
            conviction_prob *= avg_weight
        
        # Adjust for path type
        if nodes and nodes[-1].node_type == NodeType.OUTCOME:
            if OutcomeType.CRIMINAL_CHARGES in nodes[-1].outcomes:
                expected_penalty *= 2
                deterrence = 0.95
            elif OutcomeType.CIVIL_PENALTIES in nodes[-1].outcomes:
                expected_penalty *= 1.5
                deterrence = 0.75
        
        # Calculate overall score
        weights = self._objectives_to_weights(objectives)
        
        score = PathScore(
            conviction_probability=conviction_prob,
            expected_penalty=expected_penalty,
            deterrence_effect=deterrence,
            expected_recovery=recovery,
            resource_cost=cost,
            time_estimate_months=12,
            overall_score=0.0
        )
        
        score.overall_score = score.calculate_overall(weights)
        
        return score
    
    def _identify_path_risks(
        self,
        nodes: List[DecisionNode],
        evidence: List[EvaluatedEvidence]
    ) -> List[str]:
        """Identify risks for a specific path."""
        risks = []
        
        if len(evidence) < 5:
            risks.append("Limited evidence may weaken case")
        
        if nodes and nodes[-1].node_type == NodeType.OUTCOME:
            if OutcomeType.CRIMINAL_CHARGES in nodes[-1].outcomes:
                risks.append("High burden of proof (beyond reasonable doubt)")
        
        return risks
    
    def _estimate_timeline(self, outcome: OutcomeType, evidence_count: int) -> int:
        """Estimate timeline in months."""
        base = {
            OutcomeType.CRIMINAL_CHARGES: 18,
            OutcomeType.CIVIL_PENALTIES: 12,
            OutcomeType.ADMINISTRATIVE_ACTION: 6,
            OutcomeType.SETTLEMENT: 4
        }
        
        months = base.get(outcome, 12)
        
        # Adjust for complexity
        if evidence_count > 20:
            months += 6
        
        return months

