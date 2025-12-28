"""
Behavioral Risk Scoring Engine
===============================

Synthesizes outputs from temporal clustering, event proximity, and ownership
chain modules into a unified behavioral risk assessment.

This module implements Section 8: Behavioral Pattern Scoring Engine per JLAW Zero-Dollar
Transaction Forensic Specification v1.0.

Reference:
    - Section 8: Behavioral Pattern Scoring Engine
    - Section 8.1: Score Component Definitions
    - Section 8.2: Aggregation Methodology
    - Section 8.3: Prosecutorial Priority Ranking
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass

from src.zero_dollar.models import (
    Transaction,
    BehavioralScoreComponents,
    BehavioralRiskAssessment,
    EventProximityFlag,
    OwnershipChain,
)
from src.zero_dollar.modules import TemporalClusteringOutput
from src.zero_dollar.constants import classify_magnitude, MagnitudeTier


logger = logging.getLogger(__name__)


@dataclass
class BehavioralScoringEngine:
    """
    Behavioral Risk Scoring Engine.
    
    Synthesizes forensic analysis outputs into unified behavioral risk score
    with prosecutorial priority ranking.
    
    Score Components (Total: 100 points):
        - Magnitude Score: 0-25 points
        - Frequency Score: 0-25 points
        - Timing Score: 0-20 points
        - Filing Compliance Score: 0-15 points
        - Entity Complexity Score: 0-15 points
    
    Risk Tiers:
        - CRITICAL: 80-100 (Immediate referral to enforcement)
        - HIGH: 60-79 (Enhanced investigation)
        - MODERATE: 40-59 (Monitoring and documentation)
        - LOW: 0-39 (Routine surveillance)
    """
    
    def calculate_assessment(
        self,
        reporting_person_cik: str,
        reporting_person_name: str,
        issuer_cik: str,
        issuer_name: str,
        transactions: List[Transaction],
        temporal_output: TemporalClusteringOutput,
        event_flags: List[EventProximityFlag],
        ownership_chain: OwnershipChain,
    ) -> BehavioralRiskAssessment:
        """
        Calculate comprehensive behavioral risk assessment.
        
        Args:
            reporting_person_cik: CIK of reporting person
            reporting_person_name: Name of reporting person
            issuer_cik: CIK of issuer
            issuer_name: Name of issuer
            transactions: List of all transactions analyzed
            temporal_output: Output from temporal clustering module
            event_flags: List of event proximity flags
            ownership_chain: Ownership chain analysis output
            
        Returns:
            BehavioralRiskAssessment with complete scoring and recommendations
        """
        logger.info(f"Calculating behavioral assessment for {reporting_person_name} (CIK: {reporting_person_cik})")
        
        # Filter zero-dollar transactions
        zero_dollar_txns = [t for t in transactions if t.is_zero_dollar]
        
        # Calculate score components
        magnitude_score = self._calculate_magnitude_score(zero_dollar_txns)
        frequency_score = self._calculate_frequency_score(zero_dollar_txns, temporal_output)
        timing_score = self._calculate_timing_score(event_flags)
        filing_score = self._calculate_filing_compliance_score(zero_dollar_txns)
        entity_score = self._calculate_entity_complexity_score(ownership_chain)
        
        # Apply compound multiplier for multi-anomaly patterns
        compound_multiplier = self._calculate_compound_multiplier(
            magnitude_score, frequency_score, timing_score, filing_score, entity_score
        )
        
        # Apply multiplier to total score
        base_total = magnitude_score + frequency_score + timing_score + filing_score + entity_score
        adjusted_total = min(100.0, base_total * compound_multiplier)  # Cap at 100
        
        # Adjust individual scores proportionally if multiplier applied
        if compound_multiplier > 1.0:
            scale_factor = adjusted_total / base_total if base_total > 0 else 1.0
            magnitude_score *= scale_factor
            frequency_score *= scale_factor
            timing_score *= scale_factor
            filing_score *= scale_factor
            entity_score *= scale_factor
        
        # Create score components
        score_components = BehavioralScoreComponents(
            magnitude_score=magnitude_score,
            frequency_score=frequency_score,
            timing_score=timing_score,
            filing_compliance_score=filing_score,
            entity_complexity_score=entity_score,
        )
        
        # Determine prosecutorial priority
        priority = self._determine_prosecutorial_priority(score_components.total_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            score_components.total_score,
            len(zero_dollar_txns),
            temporal_output.cluster_count,
            len(event_flags),
            ownership_chain,
        )
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            score_components.total_score,
            temporal_output,
            event_flags,
            ownership_chain,
        )
        
        # Collect anomaly flag IDs
        anomaly_flags = [f.flag_id for f in event_flags]
        
        # Create assessment
        assessment = BehavioralRiskAssessment(
            assessment_id=self._generate_assessment_id(reporting_person_cik, issuer_cik),
            reporting_person_cik=reporting_person_cik,
            reporting_person_name=reporting_person_name,
            issuer_cik=issuer_cik,
            issuer_name=issuer_name,
            assessment_date=datetime.utcnow(),
            score_components=score_components,
            zero_dollar_transaction_count=len(zero_dollar_txns),
            total_transaction_count=len(transactions),
            temporal_clusters_detected=temporal_output.cluster_count,
            anomaly_flags=anomaly_flags,
            prosecutorial_priority=priority,
            recommendation=recommendation,
            next_steps=next_steps,
        )
        
        logger.info(
            f"Assessment complete: Risk Level={assessment.risk_level}, "
            f"Score={assessment.risk_score:.1f}, Priority={priority}"
        )
        
        return assessment
    
    def _calculate_magnitude_score(self, transactions: List[Transaction]) -> float:
        """
        Calculate magnitude score (0-25 points) based on transaction size.
        
        Scoring:
            - STRATEGIC (>500K shares): 25 points
            - SUBSTANTIAL (100K-500K): 20 points
            - MODERATE (50K-100K): 15 points
            - NOMINAL (10K-50K): 10 points
            - MINIMAL (<10K): 5 points
        """
        if not transactions:
            return 0.0
        
        # Classify all transactions by magnitude
        magnitude_scores = []
        for txn in transactions:
            tier = classify_magnitude(int(txn.shares))
            if tier == MagnitudeTier.STRATEGIC:
                magnitude_scores.append(25)
            elif tier == MagnitudeTier.SUBSTANTIAL:
                magnitude_scores.append(20)
            elif tier == MagnitudeTier.MODERATE:
                magnitude_scores.append(15)
            elif tier == MagnitudeTier.NOMINAL:
                magnitude_scores.append(10)
            else:  # MINIMAL
                magnitude_scores.append(5)
        
        # Return maximum score (worst case)
        return float(max(magnitude_scores))
    
    def _calculate_frequency_score(
        self,
        transactions: List[Transaction],
        temporal_output: TemporalClusteringOutput,
    ) -> float:
        """
        Calculate frequency score (0-25 points) based on clustering patterns.
        
        Scoring:
            - 5+ clusters or 10+ transactions: 25 points
            - 3-4 clusters or 7-9 transactions: 20 points
            - 2 clusters or 5-6 transactions: 15 points
            - 3-4 transactions: 10 points
            - 1-2 transactions: 5 points
        """
        cluster_count = temporal_output.cluster_count
        txn_count = len(transactions)
        
        if cluster_count >= 5 or txn_count >= 10:
            return 25.0
        elif cluster_count >= 3 or txn_count >= 7:
            return 20.0
        elif cluster_count >= 2 or txn_count >= 5:
            return 15.0
        elif txn_count >= 3:
            return 10.0
        else:
            return 5.0
    
    def _calculate_timing_score(self, event_flags: List[EventProximityFlag]) -> float:
        """
        Calculate timing score (0-20 points) based on event proximity.
        
        Scoring:
            - 5+ MNPI events: 20 points
            - 3-4 MNPI events: 15 points
            - 2 MNPI events: 10 points
            - 1 MNPI event: 5 points
            - 0 MNPI events: 0 points
        """
        event_count = len(event_flags)
        
        if event_count >= 5:
            return 20.0
        elif event_count >= 3:
            return 15.0
        elif event_count >= 2:
            return 10.0
        elif event_count >= 1:
            return 5.0
        else:
            return 0.0
    
    def _calculate_filing_compliance_score(self, transactions: List[Transaction]) -> float:
        """
        Calculate filing compliance score (0-15 points) based on late filings.
        
        Note: This component is referred to as "price_variance_score" in the 
        specification but implemented as "filing_compliance_score" in the codebase.
        Both names describe the same scoring logic and have equivalent semantic meaning.
        
        Scoring:
            - 50%+ late filings: 15 points
            - 25-49% late filings: 10 points
            - 10-24% late filings: 5 points
            - <10% late filings: 0 points
        """
        if not transactions:
            return 0.0
        
        late_count = sum(1 for t in transactions if t.is_late_filing)
        late_percentage = (late_count / len(transactions)) * 100
        
        if late_percentage >= 50:
            return 15.0
        elif late_percentage >= 25:
            return 10.0
        elif late_percentage >= 10:
            return 5.0
        else:
            return 0.0
    
    def _calculate_entity_complexity_score(self, ownership_chain: OwnershipChain) -> float:
        """
        Calculate entity complexity score (0-15 points) based on ownership structure.
        
        Scoring:
            - 4+ entities or high control probability: 15 points
            - 3 entities or moderate control: 10 points
            - 2 entities: 5 points
            - 1 entity (direct ownership): 0 points
        """
        entity_count = len(ownership_chain.entities)
        
        # Check control assessment
        has_high_control = any(
            a.control_probability >= 0.8
            for a in ownership_chain.control_assessments
        )
        
        if entity_count >= 4 or has_high_control:
            return 15.0
        elif entity_count >= 3:
            return 10.0
        elif entity_count >= 2:
            return 5.0
        else:
            return 0.0
    
    def _determine_prosecutorial_priority(self, total_score: float) -> int:
        """
        Determine prosecutorial priority ranking (1-5, 1=highest).
        
        Priority Mapping:
            - 1 (CRITICAL): 80-100 points
            - 2 (HIGH): 60-79 points
            - 3 (MODERATE): 40-59 points
            - 4 (LOW): 20-39 points
            - 5 (MINIMAL): 0-19 points
        """
        if total_score >= 80:  # Changed from 75 to match specification
            return 1
        elif total_score >= 60:
            return 2
        elif total_score >= 40:
            return 3
        elif total_score >= 20:
            return 4
        else:
            return 5
    
    def _generate_recommendation(
        self,
        total_score: float,
        zero_dollar_count: int,
        cluster_count: int,
        event_count: int,
        ownership_chain: OwnershipChain,
    ) -> str:
        """Generate human-readable recommendation based on risk score."""
        if total_score >= 80:  # Changed from 75 to match specification
            return (
                f"CRITICAL RISK: Immediate referral to SEC Enforcement Division recommended. "
                f"Subject exhibits {zero_dollar_count} zero-dollar transactions across "
                f"{cluster_count} temporal clusters with {event_count} MNPI event proximities. "
                f"Ownership structure involves {len(ownership_chain.entities)} entities. "
                f"Pattern consistent with coordinated disposition structuring and potential "
                f"Rule 10b-5 violations."
            )
        elif total_score >= 60:
            return (
                f"HIGH RISK: Enhanced investigation and documentation recommended. "
                f"Subject shows {zero_dollar_count} zero-dollar transactions with "
                f"{cluster_count} clustering patterns and {event_count} event proximities. "
                f"Warrants detailed forensic review and possible subpoena authority."
            )
        elif total_score >= 40:
            return (
                f"MODERATE RISK: Continued monitoring and periodic review recommended. "
                f"Subject has {zero_dollar_count} zero-dollar transactions with some "
                f"temporal clustering ({cluster_count} clusters). Maintain surveillance "
                f"for escalating patterns."
            )
        else:
            return (
                f"LOW RISK: Routine surveillance appropriate. "
                f"Subject has {zero_dollar_count} zero-dollar transactions with limited "
                f"clustering or event proximity. Pattern does not currently warrant "
                f"escalated investigation."
            )
    
    def _generate_next_steps(
        self,
        total_score: float,
        temporal_output: TemporalClusteringOutput,
        event_flags: List[EventProximityFlag],
        ownership_chain: OwnershipChain,
    ) -> List[str]:
        """Generate suggested next steps based on assessment."""
        steps = []
        
        if total_score >= 80:  # Changed from 75 to match specification
            steps.extend([
                "Prepare SEC Enforcement Division referral memorandum",
                "Compile complete evidence package with Merkle tree attestation",
                "Request Form 4 amendment explanation via Section 16(a) inquiry",
                "Subpoena beneficial ownership documentation",
                "Coordinate with DOJ Criminal Division for potential parallel investigation",
            ])
        elif total_score >= 60:
            steps.extend([
                "Conduct detailed Form 4 footnote analysis",
                "Cross-reference with Schedule 13D/13G beneficial ownership filings",
                "Review corporate governance documents for related party transactions",
                "Monitor for continued zero-dollar transaction activity",
            ])
        elif total_score >= 40:
            steps.extend([
                "Maintain quarterly surveillance of Form 4 filings",
                "Document any new zero-dollar transactions",
                "Review annual proxy statements (DEF 14A) for compensation disclosures",
            ])
        else:
            steps.extend([
                "Continue routine Form 4 monitoring",
                "Flag for review if transaction patterns change",
            ])
        
        # Add specific steps based on findings
        if temporal_output.cluster_count >= 3:
            steps.append("Investigate rationale for temporal transaction clustering")
        
        if event_flags:
            steps.append("Analyze relationship between transactions and material events")
        
        if len(ownership_chain.entities) >= 3:
            steps.append("Map complete beneficial ownership network and control relationships")
        
        return steps
    
    def _calculate_compound_multiplier(
        self,
        magnitude_score: float,
        frequency_score: float,
        timing_score: float,
        filing_score: float,
        entity_score: float,
    ) -> float:
        """
        Calculate compound multiplier for multi-anomaly patterns.
        
        Per specification Section 8.2: When multiple anomaly types are detected
        concurrently, the risk score is amplified through compound multipliers:
        
        - 1.5x multiplier for 2 concurrent anomaly types
        - 1.75x multiplier for 3 concurrent anomaly types
        - 2.0x multiplier for 4+ concurrent anomaly types
        
        An anomaly type is considered "active" if its score exceeds 50% of its
        maximum possible value:
        - Magnitude: >12.5 (of 25 max)
        - Frequency: >12.5 (of 25 max)
        - Timing: >10 (of 20 max)
        - Filing: >7.5 (of 15 max)
        - Entity: >7.5 (of 15 max)
        
        Args:
            magnitude_score: Magnitude component score (0-25)
            frequency_score: Frequency component score (0-25)
            timing_score: Timing component score (0-20)
            filing_score: Filing compliance score (0-15)
            entity_score: Entity complexity score (0-15)
            
        Returns:
            Compound multiplier (1.0, 1.5, 1.75, or 2.0)
        """
        # Count active anomaly types (those exceeding 50% of their maximum)
        active_anomalies = 0
        
        if magnitude_score > 12.5:  # >50% of 25 max
            active_anomalies += 1
        if frequency_score > 12.5:  # >50% of 25 max
            active_anomalies += 1
        if timing_score > 10.0:  # >50% of 20 max
            active_anomalies += 1
        if filing_score > 7.5:  # >50% of 15 max
            active_anomalies += 1
        if entity_score > 7.5:  # >50% of 15 max
            active_anomalies += 1
        
        # Apply compound multiplier per specification
        if active_anomalies >= 4:
            logger.info(f"Compound multiplier: 2.0x ({active_anomalies} concurrent anomaly types)")
            return 2.0
        elif active_anomalies == 3:
            logger.info(f"Compound multiplier: 1.75x ({active_anomalies} concurrent anomaly types)")
            return 1.75
        elif active_anomalies == 2:
            logger.info(f"Compound multiplier: 1.5x ({active_anomalies} concurrent anomaly types)")
            return 1.5
        else:
            # 0 or 1 active anomaly - no multiplier
            return 1.0
    
    def _generate_assessment_id(self, reporting_person_cik: str, issuer_cik: str) -> str:
        """Generate unique assessment ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"ASSESS-{reporting_person_cik}-{issuer_cik}-{timestamp}"
