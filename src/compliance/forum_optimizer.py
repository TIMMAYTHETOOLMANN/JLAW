"""
Forum Shopping Optimizer
========================

Prosecution venue optimization and forum selection strategy.

Implements multi-factor venue scoring algorithm to determine optimal
prosecution forums across federal, state, and international jurisdictions.

Scoring Factors (0-100 scale):
1. Penalty Severity (25%): Criminal years + civil damages
2. Evidentiary Advantages (20%): Scienter requirements, burden of proof
3. Statute of Limitations (15%): Time remaining
4. Precedent Favorability (15%): Case law strength
5. Prosecutorial Resources (10%): Experienced prosecutors available
6. Political Will (10%): Regulatory enforcement priorities
7. Victim Impact (5%): Local victim concentration

Strategy Output:
- Primary Forum: Highest venue score (typically federal)
- Secondary Forums: State AGs (coordinated timing)
- Tertiary Forums: International regulators (MLAT requests)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ForumAnalysis:
    """
    Prosecution venue analysis with scoring.
    
    Attributes:
        jurisdiction: Jurisdiction name
        jurisdiction_type: Type of jurisdiction
        prosecutorial_advantages: List of advantages for this forum
        prosecutorial_disadvantages: List of disadvantages
        estimated_penalties: Estimated penalties by type
        statute_of_limitations_remaining: Days until statute expires
        venue_score: Overall venue score (0-100)
        recommended_priority: Priority level
    """
    jurisdiction: str
    jurisdiction_type: str
    prosecutorial_advantages: List[str] = field(default_factory=list)
    prosecutorial_disadvantages: List[str] = field(default_factory=list)
    estimated_penalties: Dict[str, float] = field(default_factory=dict)
    statute_of_limitations_remaining: int = 0
    venue_score: float = 0.0
    recommended_priority: str = "TERTIARY"  # "PRIMARY" | "SECONDARY" | "TERTIARY"
    
    # Detailed scoring breakdown
    penalty_score: float = 0.0
    evidentiary_score: float = 0.0
    limitations_score: float = 0.0
    precedent_score: float = 0.0
    resources_score: float = 0.0
    political_will_score: float = 0.0
    victim_impact_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'jurisdiction': self.jurisdiction,
            'jurisdiction_type': self.jurisdiction_type,
            'prosecutorial_advantages': self.prosecutorial_advantages,
            'prosecutorial_disadvantages': self.prosecutorial_disadvantages,
            'estimated_penalties': self.estimated_penalties,
            'statute_of_limitations_remaining': self.statute_of_limitations_remaining,
            'venue_score': self.venue_score,
            'recommended_priority': self.recommended_priority,
            'score_breakdown': {
                'penalty_score': self.penalty_score,
                'evidentiary_score': self.evidentiary_score,
                'limitations_score': self.limitations_score,
                'precedent_score': self.precedent_score,
                'resources_score': self.resources_score,
                'political_will_score': self.political_will_score,
                'victim_impact_score': self.victim_impact_score
            }
        }


class ForumShoppingOptimizer:
    """
    Prosecution venue optimization engine.
    
    Analyzes all jurisdictions with authority and recommends optimal
    prosecution strategy across federal, state, and international forums.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_prosecution_venues(
        self,
        jurisdictions: List[Any],
        violations: List[Dict[str, Any]],
        state_violations: List[Dict[str, Any]],
        international_violations: List[Dict[str, Any]]
    ) -> List[ForumAnalysis]:
        """
        Score all prosecution venues and rank by optimality.
        
        Args:
            jurisdictions: List of JurisdictionProfile objects
            violations: Federal violations
            state_violations: State-specific violations
            international_violations: International violations
        
        Returns:
            List of ForumAnalysis objects ranked by venue_score
        """
        self.logger.info("Starting prosecution venue analysis...")
        
        forum_analyses = []
        
        for jurisdiction in jurisdictions:
            # Get jurisdiction details
            jurisdiction_name = jurisdiction.jurisdiction_name if hasattr(jurisdiction, 'jurisdiction_name') else str(jurisdiction)
            jurisdiction_type = jurisdiction.jurisdiction_type if hasattr(jurisdiction, 'jurisdiction_type') else 'UNKNOWN'
            
            # Create forum analysis
            analysis = ForumAnalysis(
                jurisdiction=jurisdiction_name,
                jurisdiction_type=jurisdiction_type
            )
            
            # Get relevant violations for this jurisdiction
            relevant_violations = self._get_relevant_violations(
                jurisdiction_name, jurisdiction_type, violations, state_violations, international_violations
            )
            
            if not relevant_violations:
                self.logger.debug(f"No violations for {jurisdiction_name}, skipping")
                continue
            
            # Score each factor
            analysis.penalty_score = self.calculate_penalty_advantage(
                jurisdiction_name, jurisdiction_type, relevant_violations
            )
            
            analysis.evidentiary_score = self.calculate_evidentiary_advantage(
                jurisdiction_name, jurisdiction_type, relevant_violations
            )
            
            analysis.limitations_score = self._calculate_limitations_score(
                jurisdiction_name, jurisdiction_type, relevant_violations
            )
            
            analysis.precedent_score = self._calculate_precedent_score(
                jurisdiction_name, jurisdiction_type
            )
            
            analysis.resources_score = self._calculate_resources_score(
                jurisdiction_name, jurisdiction_type
            )
            
            analysis.political_will_score = self._calculate_political_will_score(
                jurisdiction_name, jurisdiction_type
            )
            
            analysis.victim_impact_score = self._calculate_victim_impact_score(
                jurisdiction_name, violations
            )
            
            # Calculate overall venue score (weighted average)
            analysis.venue_score = (
                analysis.penalty_score * 0.25 +
                analysis.evidentiary_score * 0.20 +
                analysis.limitations_score * 0.15 +
                analysis.precedent_score * 0.15 +
                analysis.resources_score * 0.10 +
                analysis.political_will_score * 0.10 +
                analysis.victim_impact_score * 0.05
            )
            
            # Determine advantages/disadvantages
            analysis.prosecutorial_advantages = self._identify_advantages(
                jurisdiction_name, jurisdiction_type, analysis
            )
            analysis.prosecutorial_disadvantages = self._identify_disadvantages(
                jurisdiction_name, jurisdiction_type, analysis
            )
            
            # Estimate penalties
            analysis.estimated_penalties = self._estimate_penalties(
                jurisdiction_name, jurisdiction_type, relevant_violations
            )
            
            # Calculate statute of limitations remaining
            analysis.statute_of_limitations_remaining = self._calculate_sol_remaining(
                jurisdiction_name, jurisdiction_type, relevant_violations
            )
            
            forum_analyses.append(analysis)
        
        # Sort by venue score (descending)
        forum_analyses.sort(key=lambda x: x.venue_score, reverse=True)
        
        # Assign priority levels
        if forum_analyses:
            forum_analyses[0].recommended_priority = "PRIMARY"
            for analysis in forum_analyses[1:4]:  # Next 3
                analysis.recommended_priority = "SECONDARY"
            for analysis in forum_analyses[4:]:
                analysis.recommended_priority = "TERTIARY"
        
        self.logger.info(f"✓ Analyzed {len(forum_analyses)} prosecution venues")
        return forum_analyses
    
    def calculate_penalty_advantage(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate penalty severity score (0-100).
        
        Higher score = More severe penalties available.
        
        Args:
            jurisdiction: Jurisdiction name
            jurisdiction_type: Type of jurisdiction
            violations: Relevant violations
        
        Returns:
            Penalty score (0-100)
        """
        # Base scores by jurisdiction type
        if jurisdiction_type == "FEDERAL":
            base_score = 85.0  # Federal typically has strong penalties
        elif jurisdiction_type == "STATE":
            # State-specific scoring
            if jurisdiction == "TX":
                base_score = 95.0  # Texas: up to 99 years
            elif jurisdiction == "NY":
                base_score = 80.0  # New York: strong penalties
            elif jurisdiction == "CA":
                base_score = 75.0  # California: moderate penalties
            else:
                base_score = 60.0  # Other states
        elif jurisdiction_type == "INTERNATIONAL":
            base_score = 70.0  # International varies
        else:
            base_score = 50.0
        
        # Adjust based on violation severity
        critical_violations = sum(1 for v in violations if v.get('severity') == 'CRITICAL')
        if critical_violations > 0:
            base_score += min(15, critical_violations * 3)
        
        return min(100.0, base_score)
    
    def calculate_evidentiary_advantage(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate evidentiary advantage score (0-100).
        
        Higher score = Lower burden of proof, favorable evidentiary rules.
        
        Args:
            jurisdiction: Jurisdiction name
            jurisdiction_type: Type of jurisdiction
            violations: Relevant violations
        
        Returns:
            Evidentiary advantage score (0-100)
        """
        score = 50.0  # Base score
        
        # New York Martin Act: No scienter requirement (huge advantage)
        if jurisdiction == "NY":
            score = 95.0
            self.logger.debug(f"{jurisdiction}: Martin Act strict liability advantage")
        
        # Federal: Strong precedent, clear standards
        elif jurisdiction_type == "FEDERAL":
            score = 80.0
        
        # California: Scienter required but strong case law
        elif jurisdiction == "CA":
            score = 70.0
        
        # Other states: Varies
        elif jurisdiction_type == "STATE":
            score = 65.0
        
        # International: Varies widely
        elif jurisdiction_type == "INTERNATIONAL":
            if jurisdiction == "United Kingdom":
                score = 75.0  # UK FCA has strong powers
            else:
                score = 60.0
        
        return min(100.0, score)
    
    def _calculate_limitations_score(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate statute of limitations score (0-100).
        
        Higher score = More time remaining before statute expires.
        """
        # Default statute of limitations (years)
        if jurisdiction == "NY":
            sol_years = 6  # New York: 6 years
        elif jurisdiction_type == "FEDERAL":
            sol_years = 5  # Federal: 5 years
        elif jurisdiction_type == "STATE":
            sol_years = 3  # Most states: 3 years
        else:
            sol_years = 3
        
        # Assume oldest violation is 1 year old (conservative)
        years_remaining = sol_years - 1
        
        # Score: 100% if 5+ years, degrading to 0% at 0 years
        score = min(100.0, (years_remaining / 5.0) * 100)
        
        return max(0.0, score)
    
    def _calculate_precedent_score(
        self,
        jurisdiction: str,
        jurisdiction_type: str
    ) -> float:
        """
        Calculate precedent favorability score (0-100).
        
        Higher score = More favorable case law for prosecution.
        """
        # Federal has extensive securities fraud case law
        if jurisdiction_type == "FEDERAL":
            return 90.0
        
        # Major state jurisdictions
        if jurisdiction in ["NY", "CA", "TX", "FL", "MA"]:
            return 75.0
        
        # Other states
        if jurisdiction_type == "STATE":
            return 60.0
        
        # International
        if jurisdiction_type == "INTERNATIONAL":
            return 65.0
        
        return 50.0
    
    def _calculate_resources_score(
        self,
        jurisdiction: str,
        jurisdiction_type: str
    ) -> float:
        """
        Calculate prosecutorial resources score (0-100).
        
        Higher score = More experienced prosecutors, better resources.
        """
        # Federal: SEC Enforcement + DOJ Fraud Section (best resources)
        if jurisdiction == "Federal (SEC)" or jurisdiction == "Federal (DOJ)":
            return 95.0
        
        # Major state AGs with securities divisions
        if jurisdiction in ["NY", "CA", "TX", "MA"]:
            return 85.0
        
        # Other states
        if jurisdiction_type == "STATE":
            return 65.0
        
        # International
        if jurisdiction_type == "INTERNATIONAL":
            return 70.0
        
        return 50.0
    
    def _calculate_political_will_score(
        self,
        jurisdiction: str,
        jurisdiction_type: str
    ) -> float:
        """
        Calculate political will score (0-100).
        
        Higher score = More aggressive enforcement priorities.
        """
        # Federal: Consistent enforcement priorities
        if jurisdiction_type == "FEDERAL":
            return 85.0
        
        # State AGs with strong enforcement reputations
        if jurisdiction in ["NY", "CA", "MA"]:
            return 90.0
        
        # Texas: Very aggressive
        if jurisdiction == "TX":
            return 95.0
        
        # Other states
        if jurisdiction_type == "STATE":
            return 70.0
        
        # International
        if jurisdiction_type == "INTERNATIONAL":
            return 75.0
        
        return 60.0
    
    def _calculate_victim_impact_score(
        self,
        jurisdiction: str,
        violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate victim impact score (0-100).
        
        Higher score = More victims concentrated in jurisdiction.
        """
        # Count victims in this jurisdiction (simplified)
        # In real implementation, would analyze investor locations
        
        # Federal always has interstate victims
        if "Federal" in jurisdiction:
            return 80.0
        
        # States: assume some local victims
        return 60.0
    
    def _identify_advantages(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        analysis: ForumAnalysis
    ) -> List[str]:
        """Identify prosecutorial advantages for this jurisdiction."""
        advantages = []
        
        if jurisdiction == "Federal (SEC)":
            advantages.extend([
                "National reach and uniformity",
                "SEC civil enforcement + DOJ criminal prosecution",
                "Extensive case law and precedent",
                "Sophisticated enforcement resources"
            ])
        
        elif jurisdiction == "Federal (DOJ)":
            advantages.extend([
                "Criminal prosecution authority",
                "Wire/mail fraud predicates available",
                "Federal sentencing guidelines",
                "Interstate commerce jurisdiction"
            ])
        
        elif jurisdiction == "NY":
            advantages.extend([
                "Martin Act: No scienter requirement (strict liability)",
                "6-year statute of limitations (longest)",
                "Strong AG enforcement reputation",
                "Extensive securities fraud case law"
            ])
        
        elif jurisdiction == "TX":
            advantages.extend([
                "Highest criminal penalties (up to 99 years)",
                "Aggressive enforcement",
                "Strong jury verdicts"
            ])
        
        elif jurisdiction == "CA":
            advantages.extend([
                "Extraterritorial reach",
                "DFPI enforcement powers",
                "Strong civil remedies"
            ])
        
        if analysis.penalty_score > 80:
            advantages.append("Severe penalty exposure")
        
        if analysis.evidentiary_score > 80:
            advantages.append("Favorable evidentiary standards")
        
        return advantages
    
    def _identify_disadvantages(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        analysis: ForumAnalysis
    ) -> List[str]:
        """Identify prosecutorial disadvantages for this jurisdiction."""
        disadvantages = []
        
        if jurisdiction_type == "STATE" and jurisdiction not in ["NY", "CA", "TX"]:
            disadvantages.append("Limited resources compared to federal")
        
        if jurisdiction_type == "INTERNATIONAL":
            disadvantages.extend([
                "MLAT process time-consuming",
                "Extraterritorial enforcement challenges",
                "Diplomatic considerations"
            ])
        
        if analysis.limitations_score < 50:
            disadvantages.append("Limited time before statute of limitations expires")
        
        if analysis.evidentiary_score < 60:
            disadvantages.append("Higher burden of proof requirements")
        
        return disadvantages
    
    def _estimate_penalties(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Estimate potential penalties in this jurisdiction."""
        penalties = {
            'criminal_years': 0.0,
            'criminal_fine': 0.0,
            'civil_damages': 0.0
        }
        
        violation_count = len(violations)
        
        if jurisdiction == "Federal (SEC)" or jurisdiction == "Federal (DOJ)":
            penalties['criminal_years'] = min(25, violation_count * 5)
            penalties['criminal_fine'] = violation_count * 5_000_000
            penalties['civil_damages'] = violation_count * 10_000_000
        
        elif jurisdiction == "TX":
            penalties['criminal_years'] = min(99, violation_count * 10)
            penalties['criminal_fine'] = violation_count * 10_000
            penalties['civil_damages'] = violation_count * 1_000_000
        
        elif jurisdiction == "NY":
            penalties['criminal_years'] = min(4, violation_count * 2)
            penalties['criminal_fine'] = violation_count * 5_000
            penalties['civil_damages'] = violation_count * 5_000_000
        
        elif jurisdiction == "CA":
            penalties['criminal_years'] = min(5, violation_count * 2)
            penalties['criminal_fine'] = violation_count * 10_000_000
            penalties['civil_damages'] = violation_count * 5_000_000
        
        else:
            penalties['criminal_years'] = min(5, violation_count * 2)
            penalties['criminal_fine'] = violation_count * 100_000
            penalties['civil_damages'] = violation_count * 1_000_000
        
        return penalties
    
    def _calculate_sol_remaining(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]]
    ) -> int:
        """Calculate days remaining before statute of limitations expires."""
        # Default statute of limitations
        if jurisdiction == "NY":
            sol_years = 6
        elif jurisdiction_type == "FEDERAL":
            sol_years = 5
        else:
            sol_years = 3
        
        # Assume oldest violation occurred 1 year ago (conservative)
        years_remaining = sol_years - 1
        days_remaining = years_remaining * 365
        
        return max(0, days_remaining)
    
    def _get_relevant_violations(
        self,
        jurisdiction: str,
        jurisdiction_type: str,
        violations: List[Dict[str, Any]],
        state_violations: List[Dict[str, Any]],
        international_violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get violations relevant to this jurisdiction."""
        relevant = []
        
        if jurisdiction_type == "FEDERAL":
            relevant.extend(violations)
        
        elif jurisdiction_type == "STATE":
            relevant.extend([
                v for v in state_violations 
                if v.get('state') == jurisdiction
            ])
        
        elif jurisdiction_type == "INTERNATIONAL":
            relevant.extend([
                v for v in international_violations 
                if v.get('jurisdiction') == jurisdiction
            ])
        
        return relevant
    
    def generate_prosecution_strategy(
        self,
        forum_analyses: List[ForumAnalysis]
    ) -> Dict[str, Any]:
        """
        Generate coordinated prosecution strategy.
        
        Args:
            forum_analyses: Ranked forum analyses
        
        Returns:
            Prosecution strategy dictionary
        """
        if not forum_analyses:
            return {
                'status': 'ERROR',
                'message': 'No forums available for prosecution'
            }
        
        # Get primary, secondary, tertiary venues
        primary = [f for f in forum_analyses if f.recommended_priority == "PRIMARY"]
        secondary = [f for f in forum_analyses if f.recommended_priority == "SECONDARY"]
        tertiary = [f for f in forum_analyses if f.recommended_priority == "TERTIARY"]
        
        strategy = {
            'primary_venue': primary[0].to_dict() if primary else None,
            'secondary_venues': [f.to_dict() for f in secondary],
            'tertiary_venues': [f.to_dict() for f in tertiary],
            'recommended_sequence': [],
            'timing_strategy': {},
            'coordination_notes': []
        }
        
        # Generate recommended filing sequence
        if primary:
            strategy['recommended_sequence'].append({
                'step': 1,
                'action': f"File primary action in {primary[0].jurisdiction}",
                'timing': 'IMMEDIATE',
                'rationale': f"Highest venue score ({primary[0].venue_score:.1f})"
            })
        
        if secondary:
            strategy['recommended_sequence'].append({
                'step': 2,
                'action': f"Coordinate with {len(secondary)} secondary jurisdictions",
                'timing': '30-60 days after primary filing',
                'rationale': 'Allow primary action to establish narrative'
            })
        
        if tertiary:
            strategy['recommended_sequence'].append({
                'step': 3,
                'action': f"File MLAT requests with {len(tertiary)} international jurisdictions",
                'timing': '60-90 days after primary filing',
                'rationale': 'MLAT process requires time; coordinate with primary action'
            })
        
        # Timing strategy
        strategy['timing_strategy'] = {
            'avoid_stays': 'File civil actions first to avoid criminal stay',
            'avoid_double_jeopardy': 'Coordinate state/federal to prevent double jeopardy claims',
            'media_strategy': 'Announce primary action first for maximum impact'
        }
        
        # Coordination notes
        if primary and any(f.jurisdiction_type == "STATE" for f in secondary):
            strategy['coordination_notes'].append(
                "Coordinate federal-state enforcement through SEC-State Liaison program"
            )
        
        if tertiary:
            strategy['coordination_notes'].append(
                "International coordination through IOSCO (International Organization of Securities Commissions)"
            )
        
        strategy['coordination_notes'].append(
            "Establish information sharing protocols between prosecutors"
        )
        
        self.logger.info("✓ Generated coordinated prosecution strategy")
        return strategy
