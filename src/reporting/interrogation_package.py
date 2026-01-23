"""
Interrogation Package Generator
================================

Generates DOJ-ready interview protocols for actors identified in forensic analysis.

Package Structure (5 Sections):
1. BACKGROUND: Positions, compensation, corporate history
2. VIOLATIONS ATTRIBUTED: Statutory violations with actor's role
3. EVIDENCE EXHIBITS: Chronologically organized evidence
4. INTERROGATION PROTOCOL: Question trees and interview strategy
5. LEGAL FRAMEWORK: Applicable statutes and sentencing guidelines
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from src.detection.actor_extraction_engine import ActorProfile
from src.detection.actor_role_classifier import ActorRole
from src.core.evidence_chain.evidence_attribution import EvidenceAttribution, AttributionType

logger = logging.getLogger(__name__)


class InterviewPhase(Enum):
    """FBI interview question flow phases."""
    RAPPORT = "RAPPORT"  # Build rapport, baseline behavior
    BASELINE = "BASELINE"  # Establish factual baseline
    ACCUSATION = "ACCUSATION"  # Present accusations/evidence
    CONFRONTATION = "CONFRONTATION"  # Direct confrontation with evidence


@dataclass
class InterrogationQuestion:
    """Individual interrogation question with legal purpose."""
    phase: InterviewPhase
    question_number: int
    question_text: str
    legal_purpose: str  # Legal element this question establishes
    anticipated_response: str
    follow_up_questions: List[str] = field(default_factory=list)
    rebuttal_evidence: List[str] = field(default_factory=list)  # Evidence IDs to counter denials
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "legal_purpose": self.legal_purpose,
            "anticipated_response": self.anticipated_response,
            "follow_up_questions": self.follow_up_questions,
            "rebuttal_evidence": self.rebuttal_evidence
        }


@dataclass
class InterrogationPackage:
    """
    Complete DOJ-ready interrogation package for a single actor.
    """
    actor_id: str
    actor_name: str
    actor_role: ActorRole
    risk_score: float
    generation_date: datetime
    
    # Section I: Background
    corporate_positions: List[Dict[str, Any]] = field(default_factory=list)
    compensation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Section II: Violations Attributed
    violations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Section III: Evidence Exhibits
    evidence_exhibits: List[Dict[str, Any]] = field(default_factory=list)
    
    # Section IV: Interrogation Protocol
    interview_objectives: List[str] = field(default_factory=list)
    questions: List[InterrogationQuestion] = field(default_factory=list)
    anticipated_defenses: List[Dict[str, Any]] = field(default_factory=list)
    
    # Section V: Legal Framework
    applicable_statutes: List[Dict[str, Any]] = field(default_factory=list)
    evidence_strength_by_element: Dict[str, float] = field(default_factory=dict)
    ussg_sentencing: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_role": self.actor_role.value,
            "risk_score": self.risk_score,
            "generation_date": self.generation_date.isoformat(),
            "corporate_positions": self.corporate_positions,
            "compensation_history": self.compensation_history,
            "violations": self.violations,
            "evidence_exhibits": self.evidence_exhibits,
            "interview_objectives": self.interview_objectives,
            "questions": [q.to_dict() for q in self.questions],
            "anticipated_defenses": self.anticipated_defenses,
            "applicable_statutes": self.applicable_statutes,
            "evidence_strength_by_element": self.evidence_strength_by_element,
            "ussg_sentencing": self.ussg_sentencing
        }


class InterrogationPackageGenerator:
    """
    Generates DOJ-ready interrogation packages for priority actors.
    """
    
    # Statutory frameworks
    STATUTES = {
        "securities_fraud": {
            "citation": "18 U.S.C. § 1348",
            "title": "Securities and Commodities Fraud",
            "elements": [
                "Knowingly executed or attempted to execute a scheme",
                "To defraud persons in connection with securities",
                "To obtain money or property by false pretenses"
            ],
            "max_penalty": "25 years imprisonment"
        },
        "insider_trading": {
            "citation": "17 CFR § 240.10b-5",
            "title": "Employment of Manipulative and Deceptive Devices",
            "elements": [
                "Use of manipulative or deceptive device",
                "In connection with purchase or sale of security",
                "While in possession of material non-public information"
            ],
            "max_penalty": "20 years imprisonment, $5M fine"
        },
        "sox_302": {
            "citation": "SOX § 302",
            "title": "Corporate Responsibility for Financial Reports",
            "elements": [
                "CEO/CFO certification of accuracy",
                "Establishment of internal controls",
                "Disclosure of deficiencies"
            ],
            "max_penalty": "20 years imprisonment"
        },
        "sox_906": {
            "citation": "SOX § 906",
            "title": "Corporate Responsibility for Financial Reports",
            "elements": [
                "CEO/CFO certification",
                "Knowing certification of false statements"
            ],
            "max_penalty": "20 years imprisonment, $5M fine"
        }
    }
    
    def __init__(self):
        """Initialize interrogation package generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_package(
        self,
        actor: ActorProfile,
        actor_role: ActorRole,
        violations: List[Dict[str, Any]],
        evidence_attributions: List[EvidenceAttribution],
        evidence_items: List[Dict[str, Any]]
    ) -> InterrogationPackage:
        """
        Generate complete interrogation package for actor.
        
        Args:
            actor: ActorProfile object
            actor_role: Classified ActorRole
            violations: List of violations attributed to actor
            evidence_attributions: Evidence attributions for actor
            evidence_items: Full evidence items with content
            
        Returns:
            InterrogationPackage object
        """
        self.logger.info(f"Generating interrogation package for {actor.name} ({actor_role.value})")
        
        package = InterrogationPackage(
            actor_id=actor.actor_id,
            actor_name=actor.name,
            actor_role=actor_role,
            risk_score=actor.risk_score,
            generation_date=datetime.utcnow()
        )
        
        # Section I: Background
        package.corporate_positions = self._build_positions_section(actor)
        package.compensation_history = self._build_compensation_section(actor)
        
        # Section II: Violations
        package.violations = self._build_violations_section(actor, violations)
        
        # Section III: Evidence Exhibits
        package.evidence_exhibits = self._build_evidence_section(
            actor, evidence_attributions, evidence_items
        )
        
        # Section IV: Interrogation Protocol
        package.interview_objectives = self._build_objectives(actor, violations)
        package.questions = self._build_question_tree(actor, violations, evidence_attributions)
        package.anticipated_defenses = self._build_defenses_section(actor, violations)
        
        # Section V: Legal Framework
        package.applicable_statutes = self._build_statutes_section(violations)
        package.evidence_strength_by_element = self._calculate_element_strength(
            violations, evidence_attributions
        )
        package.ussg_sentencing = self._calculate_ussg_sentencing(actor, violations)
        
        return package
    
    def _build_positions_section(self, actor: ActorProfile) -> List[Dict[str, Any]]:
        """Build corporate positions section with dates."""
        positions = []
        
        for role in actor.roles:
            position = {
                "title": role,
                "start_date": actor.first_appearance.isoformat() if actor.first_appearance else "Unknown",
                "end_date": actor.last_appearance.isoformat() if actor.last_appearance else "Present",
                "source": "SEC Filings"
            }
            positions.append(position)
        
        return positions
    
    def _build_compensation_section(self, actor: ActorProfile) -> List[Dict[str, Any]]:
        """Build compensation history section."""
        compensation = []
        
        metadata = actor.metadata or {}
        
        if metadata.get('total_compensation'):
            comp_entry = {
                "period": "Latest Available",
                "salary": metadata.get('salary', 0),
                "bonus": metadata.get('bonus', 0),
                "stock_awards": metadata.get('stock_awards', 0),
                "total_compensation": metadata.get('total_compensation', 0),
                "source": "DEF 14A Proxy Statement"
            }
            compensation.append(comp_entry)
        
        return compensation
    
    def _build_violations_section(
        self,
        actor: ActorProfile,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build violations attributed section."""
        violation_entries = []
        
        for violation in violations:
            entry = {
                "violation_type": violation.get('violation_type', 'Unknown'),
                "statutory_citation": violation.get('statute', 'TBD'),
                "actor_role": self._determine_actor_role_in_violation(actor, violation),
                "financial_impact": violation.get('financial_impact', 0),
                "severity": violation.get('severity', 'MEDIUM'),
                "evidence_strength": violation.get('evidence_strength', 'Moderate'),
                "description": violation.get('description', '')
            }
            violation_entries.append(entry)
        
        return violation_entries
    
    def _build_evidence_section(
        self,
        actor: ActorProfile,
        evidence_attributions: List[EvidenceAttribution],
        evidence_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build chronologically organized evidence exhibits."""
        exhibits = []
        
        # Create evidence ID to item mapping
        evidence_map = {item.get('id', item.get('evidence_id')): item for item in evidence_items}
        
        # Sort attributions by date
        sorted_attributions = sorted(
            evidence_attributions,
            key=lambda a: a.attribution_date or date.min
        )
        
        for idx, attribution in enumerate(sorted_attributions, start=1):
            evidence_item = evidence_map.get(attribution.evidence_id, {})
            
            exhibit = {
                "exhibit_number": f"EX-{idx:03d}",
                "evidence_id": attribution.evidence_id,
                "attribution_type": attribution.attribution_type.value,
                "relevance_score": attribution.relevance_score,
                "date": attribution.attribution_date.isoformat() if attribution.attribution_date else "Unknown",
                "document_type": evidence_item.get('type', 'Document'),
                "description": evidence_item.get('description', ''),
                "key_excerpts": self._extract_key_excerpts(actor, evidence_item),
                "fre_902_authentication": "Self-authenticating SEC filing per FRE 902(13)"
            }
            exhibits.append(exhibit)
        
        return exhibits
    
    def _build_objectives(
        self,
        actor: ActorProfile,
        violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Build interview objectives (legal elements to establish)."""
        objectives = [
            f"Establish {actor.name}'s knowledge of corporate disclosure obligations",
            "Determine extent of {actor.name}'s involvement in decision-making process",
            "Assess {actor.name}'s awareness of material facts"
        ]
        
        # Add violation-specific objectives
        for violation in violations:
            vtype = violation.get('violation_type', '').lower()
            
            if 'insider_trading' in vtype:
                objectives.append("Establish possession of material non-public information")
                objectives.append("Determine timing and motivation for transactions")
            elif 'sox' in vtype or 'certification' in vtype:
                objectives.append("Confirm understanding of SOX certification requirements")
                objectives.append("Establish review process for financial statements")
            elif 'compensation' in vtype:
                objectives.append("Verify approval process for executive compensation")
                objectives.append("Establish board oversight of compensation practices")
        
        return objectives
    
    def _build_question_tree(
        self,
        actor: ActorProfile,
        violations: List[Dict[str, Any]],
        evidence_attributions: List[EvidenceAttribution]
    ) -> List[InterrogationQuestion]:
        """Build interview question tree following FBI protocol."""
        questions = []
        question_num = 1
        
        # PHASE 1: Rapport building
        questions.append(InterrogationQuestion(
            phase=InterviewPhase.RAPPORT,
            question_number=question_num,
            question_text=f"Thank you for coming in today. Can you tell me about your background with the company?",
            legal_purpose="Establish rapport and baseline behavior",
            anticipated_response="Cooperative description of career history",
            follow_up_questions=[
                "How long have you been with the company?",
                "What are your primary responsibilities?"
            ]
        ))
        question_num += 1
        
        # PHASE 2: Baseline questions
        questions.append(InterrogationQuestion(
            phase=InterviewPhase.BASELINE,
            question_number=question_num,
            question_text="Can you describe your role in the company's financial reporting process?",
            legal_purpose="Establish knowledge of disclosure obligations",
            anticipated_response="Description of responsibilities",
            follow_up_questions=[
                "Who do you report to?",
                "What oversight do you have of financial statements?"
            ]
        ))
        question_num += 1
        
        # Add violation-specific questions
        for violation in violations:
            vtype = violation.get('violation_type', '').lower()
            
            if 'insider_trading' in vtype or 'form4' in vtype:
                questions.append(InterrogationQuestion(
                    phase=InterviewPhase.ACCUSATION,
                    question_number=question_num,
                    question_text=f"Were you aware of {violation.get('description', 'material information')} before your stock transaction on {violation.get('date', 'DATE')}?",
                    legal_purpose="Establish knowledge of material non-public information",
                    anticipated_response="Denial or admission",
                    follow_up_questions=[
                        "When did you first learn this information?",
                        "Who else knew this information?",
                        "Why did you decide to trade at that specific time?"
                    ],
                    rebuttal_evidence=[
                        attr.evidence_id for attr in evidence_attributions 
                        if attr.attribution_type == AttributionType.TRANSACTION_PARTY
                    ][:2]  # Top 2 pieces of transaction evidence
                ))
                question_num += 1
            
            elif 'sox' in vtype or 'certification' in vtype:
                questions.append(InterrogationQuestion(
                    phase=InterviewPhase.ACCUSATION,
                    question_number=question_num,
                    question_text="You signed the SOX certification for this filing. Did you review the financial statements before certifying them?",
                    legal_purpose="Establish knowing certification",
                    anticipated_response="Claims of review",
                    follow_up_questions=[
                        "What specific procedures did you follow?",
                        "Did you identify any issues during your review?",
                        "Who assisted you in the review process?"
                    ],
                    rebuttal_evidence=[
                        attr.evidence_id for attr in evidence_attributions 
                        if attr.attribution_type == AttributionType.DIRECT_AUTHORSHIP
                    ][:2]
                ))
                question_num += 1
        
        # PHASE 4: Confrontation (if high-confidence evidence)
        high_confidence_evidence = [
            attr for attr in evidence_attributions 
            if attr.relevance_score >= 0.9
        ]
        
        if high_confidence_evidence:
            questions.append(InterrogationQuestion(
                phase=InterviewPhase.CONFRONTATION,
                question_number=question_num,
                question_text=f"I have your signature on {len(high_confidence_evidence)} documents that contradict your statements. Can you explain this?",
                legal_purpose="Confront with direct evidence",
                anticipated_response="Explanations or admissions",
                follow_up_questions=[
                    "Are you saying this is not your signature?",
                    "Did someone else sign on your behalf?",
                    "Were you misled about the content of these documents?"
                ],
                rebuttal_evidence=[attr.evidence_id for attr in high_confidence_evidence[:3]]
            ))
        
        return questions
    
    def _build_defenses_section(
        self,
        actor: ActorProfile,
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build anticipated defenses with rebuttal strategies."""
        defenses = []
        
        # Common defenses
        defenses.append({
            "defense": "Good faith reliance on counsel/accountants",
            "rebuttal": "Establish personal knowledge and decision-making authority",
            "counter_questions": [
                "Did you discuss concerns with counsel?",
                "What specific advice did you receive?",
                "Did you follow that advice?"
            ]
        })
        
        defenses.append({
            "defense": "Lack of knowledge/awareness",
            "rebuttal": "Present evidence of position, certifications, and direct involvement",
            "counter_questions": [
                "What were your specific duties?",
                "Who reported to you?",
                "How often did you review financial statements?"
            ]
        })
        
        # Violation-specific defenses
        for violation in violations:
            vtype = violation.get('violation_type', '').lower()
            
            if 'insider_trading' in vtype:
                defenses.append({
                    "defense": "10b5-1 trading plan defense",
                    "rebuttal": "Review plan adoption date vs. information knowledge date",
                    "counter_questions": [
                        "When was your 10b5-1 plan established?",
                        "Have you ever modified the plan?",
                        "Were you aware of material information when you established it?"
                    ]
                })
        
        return defenses
    
    def _build_statutes_section(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build applicable statutes section."""
        statutes = []
        statute_keys_used = set()
        
        for violation in violations:
            vtype = violation.get('violation_type', '').lower()
            
            # Map violation types to statutes
            if 'securities_fraud' in vtype and 'securities_fraud' not in statute_keys_used:
                statutes.append(self.STATUTES['securities_fraud'])
                statute_keys_used.add('securities_fraud')
            
            if 'insider_trading' in vtype and 'insider_trading' not in statute_keys_used:
                statutes.append(self.STATUTES['insider_trading'])
                statute_keys_used.add('insider_trading')
            
            if 'sox_302' in vtype and 'sox_302' not in statute_keys_used:
                statutes.append(self.STATUTES['sox_302'])
                statute_keys_used.add('sox_302')
            
            if 'sox_906' in vtype and 'sox_906' not in statute_keys_used:
                statutes.append(self.STATUTES['sox_906'])
                statute_keys_used.add('sox_906')
        
        return statutes
    
    def _calculate_element_strength(
        self,
        violations: List[Dict[str, Any]],
        evidence_attributions: List[EvidenceAttribution]
    ) -> Dict[str, float]:
        """Calculate evidence strength for each legal element."""
        element_strength = {}
        
        # Aggregate by attribution type as proxy for elements
        direct_auth_count = sum(1 for a in evidence_attributions if a.attribution_type == AttributionType.DIRECT_AUTHORSHIP)
        fiduciary_count = sum(1 for a in evidence_attributions if a.attribution_type == AttributionType.FIDUCIARY_ROLE)
        transaction_count = sum(1 for a in evidence_attributions if a.attribution_type == AttributionType.TRANSACTION_PARTY)
        
        # Knowledge element
        element_strength["knowledge"] = min(0.9, (direct_auth_count + fiduciary_count) * 0.15)
        
        # Intent element
        element_strength["intent"] = min(0.85, transaction_count * 0.2 + len(violations) * 0.15)
        
        # Materiality element
        element_strength["materiality"] = min(0.95, len(violations) * 0.3)
        
        return element_strength
    
    def _calculate_ussg_sentencing(
        self,
        actor: ActorProfile,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate USSG sentencing guidelines (simplified)."""
        base_offense_level = 6  # Starting point
        
        # Increase for financial loss
        total_loss = sum(v.get('financial_impact', 0) for v in violations)
        if total_loss > 10_000_000:
            base_offense_level += 20
        elif total_loss > 1_000_000:
            base_offense_level += 16
        elif total_loss > 100_000:
            base_offense_level += 12
        
        # Increase for leadership role
        roles_lower = [r.lower() for r in actor.roles]
        if any('ceo' in r or 'cfo' in r for r in roles_lower):
            base_offense_level += 4  # Leadership role enhancement
        
        # Increase for sophisticated means
        if len(violations) > 3:
            base_offense_level += 2
        
        return {
            "base_offense_level": base_offense_level,
            "estimated_loss_amount": total_loss,
            "leadership_enhancement": 4 if any('ceo' in r or 'cfo' in r for r in roles_lower) else 0,
            "estimated_guidelines_range": f"{base_offense_level}-{base_offense_level+4} months",
            "notes": "Preliminary calculation subject to plea negotiations and judicial discretion"
        }
    
    def _determine_actor_role_in_violation(
        self,
        actor: ActorProfile,
        violation: Dict[str, Any]
    ) -> str:
        """Determine actor's specific role in violation."""
        roles_lower = [r.lower() for r in actor.roles]
        
        # Check for specific roles first (most specific to least specific)
        if any('certifying' in r for r in roles_lower):
            return "Certifying Officer"
        elif any('ceo' in r or 'cfo' in r for r in roles_lower):
            return "Primary Architect"
        elif any('officer' in r or 'director' in r for r in roles_lower):
            return "Key Participant"
        else:
            return "Participant"
    
    def _extract_key_excerpts(
        self,
        actor: ActorProfile,
        evidence_item: Dict[str, Any]
    ) -> List[str]:
        """Extract key excerpts mentioning actor."""
        excerpts = []
        content = evidence_item.get('content', '')
        
        if not content:
            return excerpts
        
        # Simple sentence extraction (look for actor name)
        sentences = content.split('.')
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            if actor.name.lower() in sentence.lower():
                excerpt = sentence.strip() + '.'
                if len(excerpt) > 20:  # Filter very short matches
                    excerpts.append(excerpt)
                    if len(excerpts) >= 3:  # Max 3 excerpts per evidence
                        break
        
        return excerpts
