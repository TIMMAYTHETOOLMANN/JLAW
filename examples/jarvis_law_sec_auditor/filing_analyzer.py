"""
JARVIS:LAW Black Site Protocol - SEC Filing Analyzer
Multi-document correlation and fraud pattern detection
Integrated with forensic core for statute mapping
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

from forensic_core import (
    ViolationType, ChainOfCustody, StatuteReference,
    StatuteMapper, HardFailureException, logger
)

@dataclass
class FilingMetadata:
    """SEC filing metadata with fraud indicators"""
    cik: str
    form_type: str
    filing_date: datetime
    period_end: datetime
    accession_number: str
    file_number: Optional[str]
    amendments: int = 0
    late_filing: bool = False
    restatement: bool = False
    going_concern: bool = False
    material_weakness: bool = False
    
    @property
    def filing_delay_days(self) -> int:
        """Calculate delay between period end and filing"""
        return (self.filing_date - self.period_end).days
    
    @property
    def deadline_days(self) -> int:
        """Get filing deadline based on filer status"""
        deadlines = {
            "10-K": {"large": 60, "accelerated": 75, "non-accelerated": 90},
            "10-Q": {"large": 40, "accelerated": 40, "non-accelerated": 45},
            "4": {"all": 2}  # Form 4 deadline
        }
        form_base = self.form_type.replace("/A", "")
        if form_base in deadlines:
            if form_base == "4":
                return deadlines[form_base]["all"]
            return deadlines[form_base]["non-accelerated"]
        return 0
    
    @property
    def is_late(self) -> bool:
        """Determine if filing is late without NT filing"""
        return self.filing_delay_days > self.deadline_days

class FraudPatternDetector:
    """Detect fraud patterns across filings"""
    
    def __init__(self):
        self.patterns = {
            "REVENUE_MANIPULATION": self._detect_revenue_manipulation,
            "CHANNEL_STUFFING": self._detect_channel_stuffing,
            "EARNINGS_MANAGEMENT": self._detect_earnings_management,
            "DISCLOSURE_INCONSISTENCY": self._detect_disclosure_inconsistency,
            "LATE_FILING_PATTERN": self._detect_late_filing_pattern,
            "AMENDMENT_ABUSE": self._detect_amendment_abuse
        }
    
    def analyze_filings(self, filings: List[FilingMetadata]) -> Dict:
        """Comprehensive fraud pattern analysis"""
        results = {
            "total_filings": len(filings),
            "patterns_detected": [],
            "violations": [],
            "risk_score": 0.0,
            "statute_references": []
        }
        
        for pattern_name, detector in self.patterns.items():
            pattern_result = detector(filings)
            
            if pattern_result.get("detected"):
                results["patterns_detected"].append({
                    "pattern": pattern_name,
                    "confidence": pattern_result.get("confidence", 0.5),
                    "indicators": pattern_result.get("indicators", []),
                    "recommendation": pattern_result.get("recommendation")
                })
                
                # Map to violations
                if pattern_result.get("violations"):
                    results["violations"].extend(pattern_result["violations"])
                
                # Update risk score
                results["risk_score"] += pattern_result.get("confidence", 0.5)
        
        # Normalize risk score
        results["risk_score"] = min(1.0, results["risk_score"] / len(self.patterns))
        
        # Map violations to statutes
        if results["violations"]:
            results["statute_references"] = self._map_to_statutes(results["violations"])
        
        return results
    
    def _detect_revenue_manipulation(self, filings: List[FilingMetadata]) -> Dict:
        """Detect revenue recognition timing manipulation"""
        quarters = [f for f in filings if "10-Q" in f.form_type]
        
        if len(quarters) < 4:
            return {"detected": False, "reason": "Insufficient quarterly data"}
        
        quarters.sort(key=lambda x: x.period_end)
        
        indicators = []
        
        # Check for increasing delays
        delays = [q.filing_delay_days for q in quarters[-4:]]
        if all(delays[i] <= delays[i+1] for i in range(3)):
            indicators.append("INCREASING_FILING_DELAYS")
        
        # Check for amendments
        amendments = sum(1 for q in quarters if "/A" in q.form_type)
        if amendments > 2:
            indicators.append("MULTIPLE_AMENDMENTS")
        
        # Check for restatements
        restatements = sum(1 for q in quarters if q.restatement)
        if restatements > 0:
            indicators.append("RESTATEMENTS_PRESENT")
        
        detected = len(indicators) >= 2
        
        return {
            "detected": detected,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.3),
            "recommendation": "Deep dive into quarter-end transactions" if detected else None,
            "violations": [ViolationType.CFR_17_229_303, ViolationType.USC_15_78m] if detected else []
        }
    
    def _detect_channel_stuffing(self, filings: List[FilingMetadata]) -> Dict:
        """Detect channel stuffing patterns"""
        indicators = []
        
        # Would analyze revenue growth vs. receivables
        # This is simplified detection
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.4),
            "violations": [ViolationType.USC_15_78j_b] if indicators else []
        }
    
    def _detect_earnings_management(self, filings: List[FilingMetadata]) -> Dict:
        """Detect earnings management through filing patterns"""
        annuals = [f for f in filings if "10-K" in f.form_type]
        
        if len(annuals) < 2:
            return {"detected": False, "reason": "Insufficient annual data"}
        
        indicators = []
        
        # Check for material weaknesses
        material_weaknesses = sum(1 for a in annuals if a.material_weakness)
        if material_weaknesses > 0:
            indicators.append("MATERIAL_WEAKNESSES")
        
        # Check for going concern warnings
        going_concerns = sum(1 for a in annuals if a.going_concern)
        if going_concerns > 0:
            indicators.append("GOING_CONCERN_WARNINGS")
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.5),
            "violations": [ViolationType.USC_15_78m, ViolationType.CFR_17_210] if indicators else []
        }
    
    def _detect_disclosure_inconsistency(self, filings: List[FilingMetadata]) -> Dict:
        """Detect inconsistencies across document types"""
        indicators = []
        
        # Would compare 8-K to 10-K/Q
        # Simplified for now
        
        return {
            "detected": len(indicators) > 0,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.3)
        }
    
    def _detect_late_filing_pattern(self, filings: List[FilingMetadata]) -> Dict:
        """Detect systematic late filing patterns"""
        late_filings = [f for f in filings if f.is_late]
        
        if len(late_filings) == 0:
            return {"detected": False}
        
        indicators = []
        
        # Check if late filings lack NT notifications
        late_without_nt = [f for f in late_filings if "NT" not in f.form_type]
        if late_without_nt:
            indicators.append(f"LATE_WITHOUT_NOTIFICATION ({len(late_without_nt)} filings)")
        
        # Check if pattern is increasing
        if len(late_filings) >= 3:
            # Check last 3 filings
            recent = sorted(filings, key=lambda x: x.filing_date)[-3:]
            late_recent = [f for f in recent if f.is_late]
            if len(late_recent) >= 2:
                indicators.append("INCREASING_LATE_PATTERN")
        
        detected = len(indicators) > 0
        
        return {
            "detected": detected,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.4),
            "violations": [ViolationType.CFR_17_240_12b25, ViolationType.USC_15_78m] if detected else []
        }
    
    def _detect_amendment_abuse(self, filings: List[FilingMetadata]) -> Dict:
        """Detect excessive amendments"""
        amendments = [f for f in filings if "/A" in f.form_type]
        
        if len(amendments) == 0:
            return {"detected": False}
        
        indicators = []
        
        # Calculate amendment rate
        amendment_rate = len(amendments) / len(filings)
        if amendment_rate > 0.3:  # More than 30% amendments
            indicators.append(f"HIGH_AMENDMENT_RATE ({amendment_rate:.1%})")
        
        # Check for multiple amendments of same filing
        accession_counts = {}
        for filing in filings:
            base_acc = filing.accession_number.split("/")[0]
            accession_counts[base_acc] = accession_counts.get(base_acc, 0) + 1
        
        multiple_amendments = [acc for acc, count in accession_counts.items() if count > 2]
        if multiple_amendments:
            indicators.append(f"MULTIPLE_AMENDMENTS_SAME_FILING ({len(multiple_amendments)})")
        
        detected = len(indicators) > 0
        
        return {
            "detected": detected,
            "indicators": indicators,
            "confidence": min(1.0, len(indicators) * 0.3),
            "violations": [ViolationType.USC_15_78m] if detected else []
        }
    
    def _map_to_statutes(self, violations: List[ViolationType]) -> List[Dict]:
        """Map violations to statute references"""
        statute_refs = []
        
        for violation in violations:
            statute = StatuteMapper.get_statute(violation)
            if statute:
                statute_refs.append({
                    "violation": violation.value,
                    "citation": statute.citation,
                    "description": statute.description,
                    "criminal_penalty": statute.criminal_penalty,
                    "civil_penalty": statute.civil_penalty,
                    "priority": statute.enforcement_priority
                })
        
        # Sort by priority
        statute_refs.sort(key=lambda x: x["priority"])
        
        return statute_refs

class ContentAnalyzer:
    """Analyze filing content for semantic violations"""
    
    def __init__(self):
        self.boilerplate_phrases = [
            "may be adversely affected",
            "could have a material adverse effect",
            "we cannot assure",
            "factors beyond our control",
            "uncertainties and risks",
            "forward-looking statements"
        ]
        
        self.red_flag_phrases = [
            "material weakness",
            "going concern",
            "restatement",
            "SEC investigation",
            "received subpoena",
            "internal investigation",
            "accounting irregularities"
        ]
    
    def analyze_content(self, content: str) -> Dict:
        """Comprehensive content analysis"""
        analysis = {
            "boilerplate_score": self._calculate_boilerplate_score(content),
            "red_flags": self._detect_red_flags(content),
            "disclosure_quality": self._assess_disclosure_quality(content),
            "violations": []
        }
        
        # Determine violations
        if analysis["boilerplate_score"] > 0.7:
            analysis["violations"].append({
                "type": ViolationType.CFR_17_229_303,
                "reason": "Excessive boilerplate language in MD&A",
                "confidence": analysis["boilerplate_score"]
            })
        
        if analysis["red_flags"]:
            analysis["violations"].append({
                "type": ViolationType.USC_15_78m,
                "reason": f"Red flags detected: {', '.join(analysis['red_flags'])}",
                "confidence": 0.8
            })
        
        return analysis
    
    def _calculate_boilerplate_score(self, content: str) -> float:
        """Calculate percentage of boilerplate language"""
        content_lower = content.lower()
        count = sum(1 for phrase in self.boilerplate_phrases if phrase in content_lower)
        return min(1.0, count / len(self.boilerplate_phrases))
    
    def _detect_red_flags(self, content: str) -> List[str]:
        """Detect red flag phrases"""
        content_lower = content.lower()
        return [phrase for phrase in self.red_flag_phrases if phrase in content_lower]
    
    def _assess_disclosure_quality(self, content: str) -> Dict:
        """Assess quality of disclosures"""
        # Check for required sections
        required_sections = [
            "liquidity",
            "capital resources",
            "results of operations",
            "critical accounting"
        ]
        
        content_lower = content.lower()
        missing = [sec for sec in required_sections if sec not in content_lower]
        
        return {
            "required_sections_present": len(required_sections) - len(missing),
            "missing_sections": missing,
            "completeness_score": (len(required_sections) - len(missing)) / len(required_sections)
        }

# Export components
__all__ = [
    'FilingMetadata',
    'FraudPatternDetector',
    'ContentAnalyzer'
]

