"""
Prosecution Path Builder - Master Prosecution Strategy Orchestrator
==================================================================

Unified prosecution planning system coordinating:
- EvidenceChainAnalyzer: Evidence validation
- WitnessGraph: Witness credibility analysis  
- BurdenOfProofCalculator: Legal burden calculation
- CaseStrengthEvaluator: Overall case assessment

Workflow:
1. Collect evidence and validate chains
2. Map witness relationships and credibility
3. Define charges and required elements
4. Calculate burden of proof
5. Evaluate case strength
6. Generate prosecution strategy report
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from .evidence_chain import EvidenceChainAnalyzer, EvidenceItem, EvidenceType, AdmissibilityStatus
from .witness_graph import WitnessGraph, Witness, WitnessType, Testimony
from .burden_calculator import BurdenOfProofCalculator, BurdenStandard, ChargeElement
from .case_evaluator import CaseStrengthEvaluator

logger = logging.getLogger(__name__)


@dataclass
class Charge:
    """Criminal charge"""
    charge_id: str
    statute: str
    description: str
    elements: List[ChargeElement] = field(default_factory=list)
    severity: str = "felony"  # 'felony', 'misdemeanor'


@dataclass
class ProsecutionStrategy:
    """Comprehensive prosecution strategy"""
    target: str
    generation_date: datetime
    
    # Charges
    charges: List[Charge]
    primary_charge: str
    
    # Evidence
    total_evidence: int
    admissible_evidence: int
    evidence_strength: float
    
    # Witnesses
    total_witnesses: int
    key_witnesses: List[str]
    average_credibility: float
    
    # Burden analysis
    burden_met: Dict[str, bool]  # charge_id -> met
    burden_scores: Dict[str, float]
    
    # Case evaluation
    case_strength: str
    conviction_probability: float
    recommendations: List[str]
    
    # Strategy
    prosecution_theory: str
    evidence_sequence: List[str]
    witness_order: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target': self.target,
            'generation_date': self.generation_date.isoformat(),
            'charges': [
                {
                    'charge_id': c.charge_id,
                    'statute': c.statute,
                    'description': c.description,
                    'elements': len(c.elements),
                    'burden_met': self.burden_met.get(c.charge_id, False),
                    'burden_score': self.burden_scores.get(c.charge_id, 0.0)
                }
                for c in self.charges
            ],
            'evidence': {
                'total': self.total_evidence,
                'admissible': self.admissible_evidence,
                'strength': self.evidence_strength
            },
            'witnesses': {
                'total': self.total_witnesses,
                'key_witnesses': self.key_witnesses,
                'average_credibility': self.average_credibility
            },
            'case_assessment': {
                'strength': self.case_strength,
                'conviction_probability': self.conviction_probability,
                'recommendations': self.recommendations
            },
            'strategy': {
                'prosecution_theory': self.prosecution_theory,
                'evidence_sequence': self.evidence_sequence,
                'witness_order': self.witness_order
            }
        }


class ProsecutionPathBuilder:
    """
    Master prosecution strategy orchestrator
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Prosecution Path Builder
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.evidence_analyzer = EvidenceChainAnalyzer(config)
        self.witness_graph = WitnessGraph(config)
        self.burden_calculator = BurdenOfProofCalculator(
            BurdenStandard.BEYOND_REASONABLE_DOUBT
        )
        self.case_evaluator = CaseStrengthEvaluator(config)
        
        # Case data
        self._charges: List[Charge] = []
        
        # Statistics
        self.stats = {
            'strategies_built': 0,
            'charges_analyzed': 0,
            'total_evidence': 0,
            'total_witnesses': 0
        }
        
        logger.info("⚖️ Prosecution Path Builder initialized")
    
    async def build_prosecution_strategy(
        self,
        target: str,
        charges: List[Charge],
        evidence_items: List[EvidenceItem],
        witnesses: List[Witness],
        testimonies: List[Testimony]
    ) -> ProsecutionStrategy:
        """
        Build comprehensive prosecution strategy
        
        Args:
            target: Investigation target
            charges: List of charges to prosecute
            evidence_items: Evidence items
            witnesses: Witness list
            testimonies: Witness testimonies
        
        Returns:
            Comprehensive prosecution strategy
        """
        logger.info(f"⚖️ Building prosecution strategy for: {target}")
        logger.info(f"   Charges: {len(charges)}")
        logger.info(f"   Evidence: {len(evidence_items)}")
        logger.info(f"   Witnesses: {len(witnesses)}")
        
        self.stats['strategies_built'] += 1
        self.stats['charges_analyzed'] += len(charges)
        self.stats['total_evidence'] += len(evidence_items)
        self.stats['total_witnesses'] += len(witnesses)
        
        self._charges = charges
        
        # Step 1: Validate evidence
        logger.info("   Step 1: Validating evidence chains...")
        for evidence in evidence_items:
            self.evidence_analyzer.add_evidence(evidence)
        
        admissible_count = sum(
            1 for e in evidence_items
            if e.admissibility_status == AdmissibilityStatus.ADMISSIBLE
        )
        
        logger.info(f"✓ Evidence validated: {admissible_count}/{len(evidence_items)} admissible")
        
        # Step 2: Build witness graph
        logger.info("   Step 2: Analyzing witnesses...")
        for witness in witnesses:
            self.witness_graph.add_witness(witness)
        
        for testimony in testimonies:
            self.witness_graph.add_testimony(testimony)
        
        key_witnesses = self.witness_graph.identify_key_witnesses(top_n=5)
        avg_credibility = sum(w.credibility_score for w in witnesses) / len(witnesses) if witnesses else 0.0
        
        logger.info(f"✓ Witnesses analyzed: avg credibility {avg_credibility:.1%}")
        
        # Step 3: Calculate burden of proof
        logger.info("   Step 3: Calculating burden of proof...")
        burden_results = {}
        burden_scores = {}
        
        # Get evidence scores
        evidence_scores = {
            e.evidence_id: e.reliability_score
            for e in evidence_items
        }
        
        for charge in charges:
            burden_met, score, details = self.burden_calculator.calculate_charge_burden(
                charge.elements,
                evidence_scores
            )
            burden_results[charge.charge_id] = burden_met
            burden_scores[charge.charge_id] = score
        
        burden_met_count = sum(1 for met in burden_results.values() if met)
        logger.info(f"✓ Burden analysis: {burden_met_count}/{len(charges)} charges meet burden")
        
        # Step 4: Evaluate case strength
        logger.info("   Step 4: Evaluating case strength...")
        
        evidence_reliabilities = [e.reliability_score for e in evidence_items]
        witness_credibilities = [w.credibility_score for w in witnesses]
        
        # Determine if any charge burden met
        any_burden_met = any(burden_results.values())
        
        # Get timeline confidence from evidence metadata (if available)
        timeline_confidence = self.config.get('timeline_confidence', 0.85)
        
        evaluation = self.case_evaluator.evaluate_case_strength(
            evidence_scores=evidence_reliabilities,
            witness_credibilities=witness_credibilities,
            burden_met=any_burden_met,
            timeline_confidence=timeline_confidence,
            legal_violations=len(charges)
        )
        
        logger.info(f"✓ Case strength: {evaluation['overall_strength']} ({evaluation['probability_of_conviction']:.1%})")
        
        # Step 5: Develop prosecution theory
        logger.info("   Step 5: Developing prosecution theory...")
        theory = self._develop_prosecution_theory(charges, evidence_items, witnesses)
        
        # Step 6: Sequence evidence and witnesses
        evidence_sequence = self._sequence_evidence(evidence_items)
        witness_order = self._order_witnesses(witnesses)
        
        # Create strategy
        strategy = ProsecutionStrategy(
            target=target,
            generation_date=datetime.now(),
            charges=charges,
            primary_charge=self._identify_primary_charge(charges, burden_scores),
            total_evidence=len(evidence_items),
            admissible_evidence=admissible_count,
            evidence_strength=sum(evidence_reliabilities) / len(evidence_reliabilities) if evidence_reliabilities else 0.0,
            total_witnesses=len(witnesses),
            key_witnesses=[w.name for w in key_witnesses],
            average_credibility=avg_credibility,
            burden_met=burden_results,
            burden_scores=burden_scores,
            case_strength=evaluation['overall_strength'],
            conviction_probability=evaluation['probability_of_conviction'],
            recommendations=evaluation['recommendations'],
            prosecution_theory=theory,
            evidence_sequence=evidence_sequence,
            witness_order=witness_order
        )
        
        logger.info(f"✓ Prosecution strategy complete")
        logger.info(f"   Primary charge: {strategy.primary_charge}")
        logger.info(f"   Conviction probability: {strategy.conviction_probability:.1%}")
        
        return strategy
    
    def _develop_prosecution_theory(
        self,
        charges: List[Charge],
        evidence: List[EvidenceItem],
        witnesses: List[Witness]
    ) -> str:
        """Develop narrative prosecution theory"""
        # Get primary charge
        primary = max(charges, key=lambda c: len(c.elements))
        
        # Count evidence types
        doc_evidence = sum(1 for e in evidence if e.evidence_type == EvidenceType.DOCUMENTARY)
        digital_evidence = sum(1 for e in evidence if e.evidence_type == EvidenceType.DIGITAL)
        
        theory = f"""The prosecution will prove {primary.description} through:

1. Documentary and digital evidence showing {doc_evidence} instances of {primary.description.lower()}
2. Testimony from {len(witnesses)} witnesses establishing intent and knowledge
3. Timeline demonstrating pattern of conduct from [earliest] to [latest]
4. Expert analysis confirming {primary.statute} violations

The evidence will show beyond a reasonable doubt that the defendant engaged in 
a deliberate scheme to {primary.description.lower()}, causing substantial harm 
and violating federal law."""
        
        return theory
    
    def _sequence_evidence(self, evidence: List[EvidenceItem]) -> List[str]:
        """Determine optimal evidence presentation sequence"""
        # Sort by reliability and admissibility
        sorted_evidence = sorted(
            evidence,
            key=lambda e: (
                e.admissibility_status == AdmissibilityStatus.ADMISSIBLE,
                e.reliability_score
            ),
            reverse=True
        )
        
        return [e.evidence_id for e in sorted_evidence]
    
    def _order_witnesses(self, witnesses: List[Witness]) -> List[str]:
        """Determine optimal witness testimony order"""
        # Sort by credibility and type
        sorted_witnesses = sorted(
            witnesses,
            key=lambda w: (
                w.witness_type == WitnessType.EXPERT_WITNESS,
                w.credibility_score
            ),
            reverse=True
        )
        
        return [w.name for w in sorted_witnesses]
    
    def _identify_primary_charge(
        self,
        charges: List[Charge],
        burden_scores: Dict[str, float]
    ) -> str:
        """Identify strongest charge as primary"""
        if not charges:
            return ""
        
        # Find charge with highest burden score
        best_charge = max(charges, key=lambda c: burden_scores.get(c.charge_id, 0.0))
        
        return best_charge.charge_id
    
    def export_strategy(
        self,
        strategy: ProsecutionStrategy,
        format: str = 'json'
    ) -> str:
        """
        Export prosecution strategy
        
        Args:
            strategy: Prosecution strategy
            format: Output format ('json', 'html')
        
        Returns:
            Formatted strategy string
        """
        if format == 'json':
            return json.dumps(strategy.to_dict(), indent=2)
        elif format == 'html':
            return self._export_html(strategy)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_html(self, strategy: ProsecutionStrategy) -> str:
        """Export as HTML prosecution memo"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Prosecution Strategy: {strategy.target}</title>
            <style>
                body {{ font-family: 'Times New Roman', serif; margin: 40px; }}
                h1 {{ text-align: center; }}
                .section {{ margin: 20px 0; }}
                .charge {{ margin: 10px 0; padding: 10px; border-left: 3px solid #0066cc; }}
                .evidence {{ background-color: #f5f5f5; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>PROSECUTION STRATEGY MEMORANDUM</h1>
            <div class="section">
                <p><strong>Target:</strong> {strategy.target}</p>
                <p><strong>Date:</strong> {strategy.generation_date.strftime('%B %d, %Y')}</p>
                <p><strong>Case Strength:</strong> {strategy.case_strength.upper()}</p>
                <p><strong>Estimated Probability of Conviction:</strong> {strategy.conviction_probability:.1%}</p>
            </div>
            
            <h2>I. CHARGES</h2>
            <div class="section">
                <p><strong>Primary Charge:</strong> {strategy.primary_charge}</p>
        """
        
        for charge in strategy.charges:
            burden_met = strategy.burden_met.get(charge.charge_id, False)
            score = strategy.burden_scores.get(charge.charge_id, 0.0)
            
            html += f"""
                <div class="charge">
                    <p><strong>{charge.statute}:</strong> {charge.description}</p>
                    <p>Elements: {len(charge.elements)} | Burden Met: {"YES" if burden_met else "NO"} | Score: {score:.1%}</p>
                </div>
            """
        
        html += f"""
            </div>
            
            <h2>II. PROSECUTION THEORY</h2>
            <div class="section">
                <p style="white-space: pre-wrap;">{strategy.prosecution_theory}</p>
            </div>
            
            <h2>III. EVIDENCE</h2>
            <div class="section">
                <p>Total Evidence: {strategy.total_evidence}</p>
                <p>Admissible: {strategy.admissible_evidence} ({strategy.admissible_evidence/strategy.total_evidence:.1%})</p>
                <p>Average Strength: {strategy.evidence_strength:.1%}</p>
            </div>
            
            <h2>IV. WITNESSES</h2>
            <div class="section">
                <p>Total Witnesses: {strategy.total_witnesses}</p>
                <p>Average Credibility: {strategy.average_credibility:.1%}</p>
                <p><strong>Key Witnesses:</strong></p>
                <ul>
        """
        
        for witness in strategy.key_witnesses:
            html += f"<li>{witness}</li>"
        
        html += f"""
                </ul>
            </div>
            
            <h2>V. RECOMMENDATIONS</h2>
            <div class="section">
                <ul>
        """
        
        for rec in strategy.recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get builder statistics"""
        return {
            **self.stats,
            'evidence_analyzer': self.evidence_analyzer.get_statistics(),
            'witness_graph': self.witness_graph.get_statistics()
        }


if __name__ == "__main__":
    # Demo usage
    async def demo():
        builder = ProsecutionPathBuilder()
        
        # Create charges
        charge = Charge(
            charge_id="securities_fraud",
            statute="15 USC § 78j(b)",
            description="Securities Fraud",
            elements=[
                ChargeElement(
                    element_id="E1",
                    charge_id="securities_fraud",
                    description="Material misstatement",
                    supporting_evidence=["EV001"]
                )
            ]
        )
        
        # Create evidence
        evidence = EvidenceItem(
            evidence_id="EV001",
            description="Email evidence",
            evidence_type=EvidenceType.DIGITAL,
            source="email_server",
            collected_date=datetime.now(),
            collected_by="Agent",
            content="...",
            supports_charges=["securities_fraud"]
        )
        
        # Create witness
        witness = Witness(
            witness_id="W001",
            name="John Doe",
            witness_type=WitnessType.FACT_WITNESS
        )
        
        # Build strategy
        strategy = await builder.build_prosecution_strategy(
            target="Case001",
            charges=[charge],
            evidence_items=[evidence],
            witnesses=[witness],
            testimonies=[]
        )
        
        print(f"Strategy: {strategy.case_strength}")
        print(f"Probability: {strategy.conviction_probability:.1%}")
    
    asyncio.run(demo())

