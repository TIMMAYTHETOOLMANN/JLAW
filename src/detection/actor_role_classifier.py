"""
Actor Role Classifier
=====================

DOJ 6-tier role classification system for prosecutorial prioritization.

Classification Tiers:
- SUBJECT (90-100): C-suite + direct violation + material benefit
- TARGET (70-89): Officer/Director + substantial evidence
- WITNESS (50-69): Transaction participant + documentary evidence
- PERSON_OF_INTEREST (30-49): Peripheral involvement
- VICTIM (0-29): Shareholders harmed
- ENABLER (0-29): Facilitated violations

Risk Score Components:
- Violation Severity: 30%
- Evidence Strength: 25%
- Corporate Position: 25%
- Financial Benefit: 20%
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

from .actor_extraction_engine import ActorProfile

logger = logging.getLogger(__name__)


class ActorRole(Enum):
    """DOJ 6-tier role classification."""
    SUBJECT = "SUBJECT"  # 90-100 risk score
    TARGET = "TARGET"  # 70-89 risk score
    WITNESS = "WITNESS"  # 50-69 risk score
    PERSON_OF_INTEREST = "PERSON_OF_INTEREST"  # 30-49 risk score
    VICTIM = "VICTIM"  # 0-29 risk score
    ENABLER = "ENABLER"  # 0-29 risk score (facilitated violations)


@dataclass
class RiskScoreComponents:
    """
    Breakdown of risk score components.
    """
    violation_severity: float  # 0-30 points (30% weight)
    evidence_strength: float  # 0-25 points (25% weight)
    corporate_position: float  # 0-25 points (25% weight)
    financial_benefit: float  # 0-20 points (20% weight)
    total_score: float  # 0-100
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "violation_severity": round(self.violation_severity, 2),
            "evidence_strength": round(self.evidence_strength, 2),
            "corporate_position": round(self.corporate_position, 2),
            "financial_benefit": round(self.financial_benefit, 2),
            "total_score": round(self.total_score, 2)
        }


class ActorRoleClassifier:
    """
    Classifies actors according to DOJ 6-tier role system and calculates risk scores.
    """
    
    # C-suite and senior executive positions (highest weight)
    C_SUITE_POSITIONS = {
        'ceo', 'chief executive officer', 'president',
        'cfo', 'chief financial officer',
        'coo', 'chief operating officer',
        'cto', 'chief technology officer',
        'general counsel', 'chief legal officer'
    }
    
    # Officer and director positions
    OFFICER_DIRECTOR_POSITIONS = {
        'director', 'board member', 'executive', 'officer',
        'vice president', 'vp', 'senior vice president', 'svp',
        'treasurer', 'secretary', 'controller'
    }
    
    # High severity violation types
    HIGH_SEVERITY_VIOLATIONS = {
        'securities_fraud', 'insider_trading', 'financial_misstatement',
        'sox_violation', 'backdating', 'market_manipulation'
    }
    
    # Medium severity violation types
    MEDIUM_SEVERITY_VIOLATIONS = {
        'disclosure_failure', 'late_filing', 'compensation_excess',
        'related_party_transaction', 'conflict_of_interest'
    }
    
    def __init__(self):
        """Initialize actor role classifier."""
        self.logger = logging.getLogger(__name__)
    
    def classify_actor(
        self,
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]] = None,
        evidence_items: Optional[List[Dict[str, Any]]] = None
    ) -> ActorRole:
        """
        Classify actor into DOJ 6-tier role system.
        
        Args:
            actor: ActorProfile to classify
            violation_details: List of violation details with severity
            evidence_items: List of evidence items with strength ratings
            
        Returns:
            ActorRole classification
        """
        # Calculate risk score components
        components = self.calculate_risk_score(actor, violation_details, evidence_items)
        
        # Update actor's risk score
        actor.risk_score = components.total_score
        
        # Classify based on risk score
        if components.total_score >= 90:
            return ActorRole.SUBJECT
        elif components.total_score >= 70:
            return ActorRole.TARGET
        elif components.total_score >= 50:
            return ActorRole.WITNESS
        elif components.total_score >= 30:
            return ActorRole.PERSON_OF_INTEREST
        else:
            # Distinguish between VICTIM and ENABLER
            if self._is_enabler(actor, violation_details):
                return ActorRole.ENABLER
            else:
                return ActorRole.VICTIM
    
    def calculate_risk_score(
        self,
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]] = None,
        evidence_items: Optional[List[Dict[str, Any]]] = None
    ) -> RiskScoreComponents:
        """
        Calculate comprehensive risk score with component breakdown.
        
        Risk Score Components:
        - Violation Severity: 30% (0-30 points)
        - Evidence Strength: 25% (0-25 points)
        - Corporate Position: 25% (0-25 points)
        - Financial Benefit: 20% (0-20 points)
        
        Args:
            actor: ActorProfile to score
            violation_details: List of violation details
            evidence_items: List of evidence items
            
        Returns:
            RiskScoreComponents with breakdown
        """
        # Calculate each component
        violation_severity = self._calculate_violation_severity(actor, violation_details)
        evidence_strength = self._calculate_evidence_strength(actor, evidence_items)
        corporate_position = self._calculate_corporate_position_score(actor)
        financial_benefit = self._calculate_financial_benefit_score(actor)
        
        # Total score
        total_score = violation_severity + evidence_strength + corporate_position + financial_benefit
        
        return RiskScoreComponents(
            violation_severity=violation_severity,
            evidence_strength=evidence_strength,
            corporate_position=corporate_position,
            financial_benefit=financial_benefit,
            total_score=min(total_score, 100.0)  # Cap at 100
        )
    
    def _calculate_violation_severity(
        self,
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate violation severity score (0-30 points).
        
        30% weight of total risk score.
        """
        if not actor.violations and not violation_details:
            return 0.0
        
        score = 0.0
        violation_count = len(actor.violations)
        
        # Base score from violation count
        if violation_count == 0:
            return 0.0
        elif violation_count == 1:
            score = 10.0
        elif violation_count <= 3:
            score = 20.0
        else:
            score = 30.0
        
        # Adjust based on violation details
        if violation_details:
            high_severity_count = 0
            medium_severity_count = 0
            
            for violation in violation_details:
                violation_type = violation.get('violation_type', '').lower()
                severity = violation.get('severity', '').upper()
                
                # Check explicit severity
                if severity == 'CRITICAL' or severity == 'HIGH':
                    high_severity_count += 1
                elif severity == 'MEDIUM':
                    medium_severity_count += 1
                
                # Check violation type
                if any(high_type in violation_type for high_type in self.HIGH_SEVERITY_VIOLATIONS):
                    high_severity_count += 1
                elif any(med_type in violation_type for med_type in self.MEDIUM_SEVERITY_VIOLATIONS):
                    medium_severity_count += 1
            
            # Adjust score based on severity
            if high_severity_count > 0:
                score = 30.0  # Maximum score for high severity
            elif medium_severity_count > 0:
                score = max(score, 20.0)
        
        return min(score, 30.0)
    
    def _calculate_evidence_strength(
        self,
        actor: ActorProfile,
        evidence_items: Optional[List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate evidence strength score (0-25 points).
        
        25% weight of total risk score.
        """
        if not actor.evidence_items and not evidence_items:
            return 0.0
        
        score = 0.0
        
        # Combine actor evidence items and passed evidence items for counting
        all_evidence = list(actor.evidence_items or [])
        if evidence_items:
            all_evidence.extend(evidence_items)
        
        evidence_count = len(all_evidence)
        
        # Base score from evidence count
        if evidence_count == 0:
            return 0.0
        elif evidence_count <= 2:
            score = 10.0
        elif evidence_count <= 5:
            score = 15.0
        else:
            score = 20.0
        
        # Adjust based on evidence strength from passed evidence_items
        if evidence_items:
            direct_evidence_count = 0
            
            for evidence in evidence_items:
                evidence_type = evidence.get('type', '').lower()
                strength = evidence.get('strength', '').upper()
                
                # Direct evidence (signatures, certifications, transactions)
                if evidence_type in ['signature', 'certification', 'transaction', 'direct_authorship']:
                    direct_evidence_count += 1
                
                # High strength evidence
                if strength == 'STRONG' or strength == 'DIRECT':
                    direct_evidence_count += 1
            
            # Bonus for direct evidence
            if direct_evidence_count > 0:
                score = 25.0  # Maximum score for direct evidence
        
        return min(score, 25.0)
    
    def _calculate_corporate_position_score(self, actor: ActorProfile) -> float:
        """
        Calculate corporate position score (0-25 points).
        
        25% weight of total risk score.
        """
        if not actor.roles:
            return 0.0
        
        score = 0.0
        
        # Normalize roles to lowercase for comparison
        roles_lower = [role.lower() for role in actor.roles]
        
        # C-suite positions (25 points)
        for position in self.C_SUITE_POSITIONS:
            if any(position in role for role in roles_lower):
                return 25.0  # Maximum score
        
        # Officer/Director positions (20 points)
        for position in self.OFFICER_DIRECTOR_POSITIONS:
            if any(position in role for role in roles_lower):
                score = max(score, 20.0)
        
        # Certifying officers (SOX 302/906) (22 points)
        if any('certifying' in role for role in roles_lower):
            score = max(score, 22.0)
        
        # Compensation committee (15 points)
        if any('compensation committee' in role for role in roles_lower):
            score = max(score, 15.0)
        
        # Board member (18 points)
        if any('board' in role or 'director' in role for role in roles_lower):
            score = max(score, 18.0)
        
        # Insider (10 points)
        if any('insider' in role for role in roles_lower):
            score = max(score, 10.0)
        
        # Base score if no specific position identified
        if score == 0.0:
            score = 5.0
        
        return min(score, 25.0)
    
    def _calculate_financial_benefit_score(self, actor: ActorProfile) -> float:
        """
        Calculate financial benefit score (0-20 points).
        
        20% weight of total risk score.
        """
        metadata = actor.metadata or {}
        score = 0.0
        
        # Check various financial indicators
        total_compensation = metadata.get('total_compensation', 0)
        stock_awards = metadata.get('stock_awards', 0)
        transaction_value = metadata.get('total_value', 0)
        shares_value = metadata.get('value', 0)
        
        # Calculate total financial benefit
        total_benefit = total_compensation + stock_awards + transaction_value + shares_value
        
        # Score based on magnitude
        if total_benefit > 10_000_000:  # > $10M
            score = 20.0
        elif total_benefit > 5_000_000:  # > $5M
            score = 18.0
        elif total_benefit > 1_000_000:  # > $1M
            score = 15.0
        elif total_benefit > 500_000:  # > $500K
            score = 12.0
        elif total_benefit > 100_000:  # > $100K
            score = 10.0
        elif total_benefit > 0:
            score = 5.0
        
        # Bonus for suspicious patterns
        if metadata.get('is_zero_dollar'):
            score += 5.0  # Zero-dollar transactions are suspicious
        
        if metadata.get('transaction_code') in ['G', 'J', 'L']:  # Gifts and unusual transfers
            score += 3.0
        
        return min(score, 20.0)
    
    def _is_enabler(
        self,
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """
        Determine if low-risk actor is an enabler rather than victim.
        
        Enablers facilitate violations without direct benefit.
        """
        # Check roles
        roles_lower = [role.lower() for role in actor.roles]
        
        # Professional enablers
        enabler_roles = ['auditor', 'accountant', 'legal counsel', 'attorney', 'advisor', 
                        'consultant', 'banker', 'underwriter']
        
        for enabler_role in enabler_roles:
            if any(enabler_role in role for role in roles_lower):
                return True
        
        # Check if actor facilitated but didn't benefit
        if not violation_details:
            # No violations provided, check if has evidence but no direct violations
            if actor.evidence_items and len(actor.violations) == 0:
                # Has evidence of involvement but no direct violations
                return True
        
        return False
    
    def classify_multiple_actors(
        self,
        actors: List[ActorProfile],
        violation_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        evidence_map: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, ActorRole]:
        """
        Classify multiple actors in batch.
        
        Args:
            actors: List of ActorProfile objects
            violation_map: Dict mapping actor_id to violation details
            evidence_map: Dict mapping actor_id to evidence items
            
        Returns:
            Dict mapping actor_id to ActorRole
        """
        classifications = {}
        
        for actor in actors:
            violations = violation_map.get(actor.actor_id, []) if violation_map else None
            evidence = evidence_map.get(actor.actor_id, []) if evidence_map else None
            
            role = self.classify_actor(actor, violations, evidence)
            classifications[actor.actor_id] = role
        
        self.logger.info(f"Classified {len(actors)} actors")
        return classifications
    
    def get_actors_by_classification(
        self,
        actors: List[ActorProfile],
        classifications: Dict[str, ActorRole]
    ) -> Dict[ActorRole, List[ActorProfile]]:
        """
        Group actors by their classification.
        
        Returns:
            Dict mapping ActorRole to list of actors
        """
        grouped = {role: [] for role in ActorRole}
        
        for actor in actors:
            role = classifications.get(actor.actor_id)
            if role:
                grouped[role].append(actor)
        
        return grouped
    
    def get_priority_actors(
        self,
        actors: List[ActorProfile],
        min_risk_score: float = 50.0
    ) -> List[ActorProfile]:
        """
        Get actors meeting minimum risk score threshold.
        
        Args:
            actors: List of ActorProfile objects
            min_risk_score: Minimum risk score threshold (default: 50.0)
            
        Returns:
            List of actors sorted by risk score (descending)
        """
        priority_actors = [
            actor for actor in actors 
            if actor.risk_score >= min_risk_score
        ]
        
        # Sort by risk score (highest first)
        priority_actors.sort(key=lambda a: a.risk_score, reverse=True)
        
        return priority_actors
