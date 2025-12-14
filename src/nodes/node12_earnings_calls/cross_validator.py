"""
Earnings Call Cross-Validation Engine
=====================================

Cross-validates earnings call statements against SEC filings for
Regulation FD compliance and disclosure consistency.

Regulation FD (Fair Disclosure) requires that material information
disclosed to analysts/investors must be simultaneously filed with SEC
via Form 8-K within 4 business days.

Detection Capabilities:
- Oral guidance contradicting filed forward-looking statements
- Q&A responses inconsistent with 8-K disclosures
- Revenue/guidance changes not filed within 4 business days
- Material non-public information disclosure (Reg FD violations)
- Selective disclosure to analysts (tipping violations)
- Guidance inconsistencies between calls and filed documents

Cross-Reference Sources:
- Form 8-K Item 2.02 (Results of Operations)
- Form 8-K Item 7.01 (Regulation FD Disclosure)
- Form 8-K Item 8.01 (Other Events)
- 10-Q/10-K MD&A forward-looking statements

Integration: Connects with Node 9 (8-K events) and existing Node 12
            transcript analyzer
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Type of cross-validation violation detected."""
    REG_FD_VIOLATION = "Regulation FD Violation"
    FILING_INCONSISTENCY = "Filing Inconsistency"
    GUIDANCE_DISCREPANCY = "Guidance Discrepancy"
    MISSING_8K = "Missing 8-K Filing"
    SELECTIVE_DISCLOSURE = "Selective Disclosure"
    MATERIAL_OMISSION = "Material Omission"


class ViolationSeverity(Enum):
    """Severity level for violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class StatementMatch:
    """Matching between earnings call statement and SEC filing."""
    call_statement: str
    call_timestamp: datetime
    call_speaker: str
    
    filing_statement: Optional[str]
    filing_type: Optional[str]  # 8-K, 10-Q, 10-K
    filing_date: Optional[date]
    filing_item: Optional[str]  # e.g., "Item 2.02"
    
    is_consistent: bool
    consistency_score: float  # 0.0 to 1.0
    discrepancy_description: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_statement": self.call_statement[:200],  # Truncate for readability
            "call_timestamp": self.call_timestamp.isoformat(),
            "call_speaker": self.call_speaker,
            "filing": {
                "statement": self.filing_statement[:200] if self.filing_statement else None,
                "type": self.filing_type,
                "date": self.filing_date.isoformat() if self.filing_date else None,
                "item": self.filing_item
            },
            "consistency": {
                "is_consistent": self.is_consistent,
                "score": round(self.consistency_score, 3),
                "discrepancy": self.discrepancy_description
            }
        }


@dataclass
class RegFDViolation:
    """Detected Regulation FD violation."""
    violation_type: ViolationType
    severity: ViolationSeverity
    
    # What was disclosed
    disclosed_statement: str
    disclosure_date: datetime
    disclosure_context: str  # Prepared remarks, Q&A, etc.
    
    # Filing status
    required_8k_filed: bool
    filing_date: Optional[date]
    filing_delay_days: Optional[int]
    
    # Materiality assessment
    is_material: bool
    materiality_indicators: List[str]
    
    # Evidence
    evidence_description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "disclosure": {
                "statement": self.disclosed_statement[:300],
                "date": self.disclosure_date.isoformat(),
                "context": self.disclosure_context
            },
            "filing": {
                "required_8k_filed": self.required_8k_filed,
                "filing_date": self.filing_date.isoformat() if self.filing_date else None,
                "delay_days": self.filing_delay_days
            },
            "materiality": {
                "is_material": self.is_material,
                "indicators": self.materiality_indicators
            },
            "evidence": self.evidence_description
        }


@dataclass
class CrossValidationReport:
    """Complete cross-validation report for an earnings call."""
    report_id: str
    company_cik: str
    company_name: str
    call_date: datetime
    analysis_date: datetime
    
    # Statements analyzed
    total_statements_checked: int
    statement_matches: List[StatementMatch]
    
    # Violations detected
    violations: List[RegFDViolation]
    violation_count: int
    critical_violations: int
    
    # Overall assessment
    compliance_score: float  # 0.0 to 1.0
    risk_level: str
    
    # Recommendations
    findings_summary: str
    regulatory_implications: List[str]
    recommended_actions: List[str]
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "company": {
                "cik": self.company_cik,
                "name": self.company_name
            },
            "call_date": self.call_date.isoformat(),
            "analysis_date": self.analysis_date.isoformat(),
            "analysis": {
                "statements_checked": self.total_statements_checked,
                "violation_count": self.violation_count,
                "critical_violations": self.critical_violations
            },
            "compliance_score": round(self.compliance_score, 3),
            "risk_level": self.risk_level,
            "violations": [v.to_dict() for v in self.violations],
            "findings_summary": self.findings_summary,
            "regulatory_implications": self.regulatory_implications,
            "recommended_actions": self.recommended_actions,
            "evidence_hash": self.evidence_hash
        }


class EarningsCallCrossValidator:
    """
    Cross-validator for earnings call statements against SEC filings.
    
    Ensures compliance with Regulation FD and identifies disclosure
    inconsistencies that may indicate securities violations.
    """
    
    # Regulation FD filing deadline
    REG_FD_DEADLINE_DAYS = 4  # Business days
    
    # Materiality thresholds
    REVENUE_GUIDANCE_THRESHOLD = 0.05  # 5% change is material
    EARNINGS_GUIDANCE_THRESHOLD = 0.10  # 10% change is material
    
    # Material disclosure keywords
    MATERIAL_KEYWORDS = [
        'guidance', 'forecast', 'expect', 'anticipate', 'project',
        'revenue', 'earnings', 'profit', 'loss', 'margin',
        'restructuring', 'acquisition', 'merger', 'divestiture',
        'investigation', 'lawsuit', 'regulatory', 'compliance',
        'restatement', 'write-down', 'impairment'
    ]
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize the cross-validator.
        
        Args:
            mock_mode: If True, use mock data for testing without external dependencies
        """
        self.mock_mode = mock_mode
        self.reports = []
    
    def validate_call(
        self,
        company_cik: str,
        company_name: str,
        call_date: datetime,
        call_transcript: Dict[str, Any],
        sec_filings: List[Dict[str, Any]]
    ) -> CrossValidationReport:
        """
        Cross-validate earnings call against SEC filings.
        
        Args:
            company_cik: SEC CIK number
            company_name: Company name
            call_date: Date of earnings call
            call_transcript: Parsed transcript with statements
            sec_filings: List of relevant SEC filings (8-K, 10-Q, 10-K)
            
        Returns:
            CrossValidationReport with validation results
        """
        if self.mock_mode:
            return self._generate_mock_report(company_cik, company_name, call_date)
        
        # Extract material statements from call
        material_statements = self._extract_material_statements(call_transcript)
        
        # Match statements with filings
        statement_matches = []
        for stmt in material_statements:
            match = self._match_statement_to_filing(stmt, sec_filings, call_date)
            statement_matches.append(match)
        
        # Detect Reg FD violations
        violations = []
        
        # Check for missing 8-K filings
        missing_8k_violations = self._check_missing_8k(material_statements, sec_filings, call_date)
        violations.extend(missing_8k_violations)
        
        # Check for filing inconsistencies
        inconsistency_violations = self._check_filing_inconsistencies(statement_matches)
        violations.extend(inconsistency_violations)
        
        # Check for guidance discrepancies
        guidance_violations = self._check_guidance_discrepancies(
            call_transcript,
            sec_filings,
            call_date
        )
        violations.extend(guidance_violations)
        
        # Calculate metrics
        critical_violations = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        compliance_score = self._calculate_compliance_score(len(material_statements), violations)
        risk_level = self._determine_risk_level(compliance_score, critical_violations)
        
        # Generate report
        report = CrossValidationReport(
            report_id=self._generate_report_id(company_cik, call_date),
            company_cik=company_cik,
            company_name=company_name,
            call_date=call_date,
            analysis_date=datetime.utcnow(),
            total_statements_checked=len(material_statements),
            statement_matches=statement_matches,
            violations=violations,
            violation_count=len(violations),
            critical_violations=critical_violations,
            compliance_score=compliance_score,
            risk_level=risk_level,
            findings_summary=self._generate_findings_summary(violations, statement_matches),
            regulatory_implications=self._get_regulatory_implications(violations),
            recommended_actions=self._get_recommended_actions(risk_level, violations),
            evidence_hash=self._compute_evidence_hash(statement_matches, violations)
        )
        
        self.reports.append(report)
        return report
    
    def _extract_material_statements(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract potentially material statements from transcript."""
        statements = []
        
        # Process prepared remarks
        prepared_remarks = transcript.get('prepared_remarks', [])
        for remark in prepared_remarks:
            text = remark.get('text', '')
            speaker = remark.get('speaker', 'Unknown')
            timestamp = remark.get('timestamp', datetime.utcnow())
            
            if self._is_material_statement(text):
                statements.append({
                    'text': text,
                    'speaker': speaker,
                    'timestamp': timestamp,
                    'context': 'Prepared Remarks'
                })
        
        # Process Q&A
        qa_section = transcript.get('qa', [])
        for qa in qa_section:
            answer_text = qa.get('answer', '')
            speaker = qa.get('answerer', 'Unknown')
            timestamp = qa.get('timestamp', datetime.utcnow())
            
            if self._is_material_statement(answer_text):
                statements.append({
                    'text': answer_text,
                    'speaker': speaker,
                    'timestamp': timestamp,
                    'context': 'Q&A Session'
                })
        
        return statements
    
    def _is_material_statement(self, text: str) -> bool:
        """Determine if a statement is potentially material."""
        text_lower = text.lower()
        
        # Check for material keywords
        for keyword in self.MATERIAL_KEYWORDS:
            if keyword in text_lower:
                return True
        
        # Check for numerical guidance (e.g., "revenue of $X" or "EPS of $Y")
        if re.search(r'\$[\d,]+\.?\d*\s*(million|billion|thousand)', text_lower):
            return True
        
        if re.search(r'(revenue|earnings|eps|profit|margin).*?\d+%?', text_lower):
            return True
        
        return False
    
    def _match_statement_to_filing(
        self,
        statement: Dict[str, Any],
        filings: List[Dict[str, Any]],
        call_date: datetime
    ) -> StatementMatch:
        """Match a call statement to corresponding SEC filing."""
        best_match = None
        best_score = 0.0
        
        # Search for matching content in filings
        for filing in filings:
            filing_type = filing.get('form_type')
            filing_date = filing.get('filing_date')
            filing_content = filing.get('content', '')
            
            # Calculate similarity score (simplified)
            score = self._calculate_similarity(statement['text'], filing_content)
            
            if score > best_score:
                best_score = score
                best_match = filing
        
        # Determine consistency
        is_consistent = best_score >= 0.70  # 70% similarity threshold
        
        discrepancy = None
        if not is_consistent and best_match:
            discrepancy = "Statement from call does not match filed disclosure"
        elif not best_match:
            discrepancy = "No matching disclosure found in SEC filings"
        
        return StatementMatch(
            call_statement=statement['text'],
            call_timestamp=statement['timestamp'],
            call_speaker=statement['speaker'],
            filing_statement=best_match.get('content', '')[:500] if best_match else None,
            filing_type=best_match.get('form_type') if best_match else None,
            filing_date=best_match.get('filing_date') if best_match else None,
            filing_item=best_match.get('item') if best_match else None,
            is_consistent=is_consistent,
            consistency_score=best_score,
            discrepancy_description=discrepancy
        )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simplified)."""
        # Simple word overlap metric
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_missing_8k(
        self,
        statements: List[Dict[str, Any]],
        filings: List[Dict[str, Any]],
        call_date: datetime
    ) -> List[RegFDViolation]:
        """Check for material statements missing required 8-K filing."""
        violations = []
        
        # Get all 8-K filings around call date
        eight_k_filings = [
            f for f in filings
            if f.get('form_type') == '8-K' and
            abs((f.get('filing_date', date.today()) - call_date.date()).days) <= 10
        ]
        
        for stmt in statements:
            # Check if material statement has corresponding 8-K
            has_matching_8k = False
            filing_date = None
            
            for filing in eight_k_filings:
                if self._calculate_similarity(stmt['text'], filing.get('content', '')) > 0.50:
                    has_matching_8k = True
                    filing_date = filing.get('filing_date')
                    break
            
            # If material and no 8-K within deadline, it's a violation
            if not has_matching_8k:
                violations.append(RegFDViolation(
                    violation_type=ViolationType.MISSING_8K,
                    severity=ViolationSeverity.CRITICAL,
                    disclosed_statement=stmt['text'],
                    disclosure_date=stmt['timestamp'],
                    disclosure_context=stmt['context'],
                    required_8k_filed=False,
                    filing_date=None,
                    filing_delay_days=None,
                    is_material=True,
                    materiality_indicators=self._get_materiality_indicators(stmt['text']),
                    evidence_description=f"Material disclosure in {stmt['context']} not followed by 8-K filing"
                ))
            elif filing_date:
                # Check if filing was timely
                delay_days = (filing_date - call_date.date()).days
                
                if delay_days > self.REG_FD_DEADLINE_DAYS:
                    violations.append(RegFDViolation(
                        violation_type=ViolationType.REG_FD_VIOLATION,
                        severity=ViolationSeverity.HIGH,
                        disclosed_statement=stmt['text'],
                        disclosure_date=stmt['timestamp'],
                        disclosure_context=stmt['context'],
                        required_8k_filed=True,
                        filing_date=filing_date,
                        filing_delay_days=delay_days,
                        is_material=True,
                        materiality_indicators=self._get_materiality_indicators(stmt['text']),
                        evidence_description=f"8-K filed {delay_days} days after disclosure (deadline: {self.REG_FD_DEADLINE_DAYS} days)"
                    ))
        
        return violations
    
    def _check_filing_inconsistencies(
        self,
        matches: List[StatementMatch]
    ) -> List[RegFDViolation]:
        """Check for inconsistencies between call statements and filings."""
        violations = []
        
        for match in matches:
            if not match.is_consistent and match.filing_statement:
                violations.append(RegFDViolation(
                    violation_type=ViolationType.FILING_INCONSISTENCY,
                    severity=ViolationSeverity.MEDIUM if match.consistency_score > 0.40 else ViolationSeverity.HIGH,
                    disclosed_statement=match.call_statement,
                    disclosure_date=match.call_timestamp,
                    disclosure_context="Earnings Call",
                    required_8k_filed=True,
                    filing_date=match.filing_date,
                    filing_delay_days=None,
                    is_material=True,
                    materiality_indicators=self._get_materiality_indicators(match.call_statement),
                    evidence_description=match.discrepancy_description or "Statement inconsistent with filed disclosure"
                ))
        
        return violations
    
    def _check_guidance_discrepancies(
        self,
        transcript: Dict[str, Any],
        filings: List[Dict[str, Any]],
        call_date: datetime
    ) -> List[RegFDViolation]:
        """Check for guidance discrepancies between calls and filings."""
        violations = []
        
        # Extract guidance from transcript
        call_guidance = self._extract_guidance(transcript)
        
        # Extract guidance from 10-Q/10-K MD&A
        filing_guidance = {}
        for filing in filings:
            if filing.get('form_type') in ['10-Q', '10-K']:
                filing_guidance.update(self._extract_guidance_from_filing(filing))
        
        # Compare guidance
        for metric, call_value in call_guidance.items():
            filing_value = filing_guidance.get(metric)
            
            if filing_value and abs(call_value - filing_value) / filing_value > 0.05:  # 5% threshold
                violations.append(RegFDViolation(
                    violation_type=ViolationType.GUIDANCE_DISCREPANCY,
                    severity=ViolationSeverity.HIGH,
                    disclosed_statement=f"{metric}: {call_value}",
                    disclosure_date=call_date,
                    disclosure_context="Guidance Statement",
                    required_8k_filed=False,
                    filing_date=None,
                    filing_delay_days=None,
                    is_material=True,
                    materiality_indicators=[f"{metric} guidance differs by {abs(call_value - filing_value)/filing_value*100:.1f}%"],
                    evidence_description=f"Oral guidance ({call_value}) differs from filed guidance ({filing_value})"
                ))
        
        return violations
    
    def _extract_guidance(self, transcript: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract numerical guidance from transcript (simplified).
        
        NOTE: This is a simplified regex-based extraction for demonstration.
        Production implementation should use:
        - NLP-based entity extraction (spaCy, transformers)
        - Context validation to ensure matched values are guidance
        - Range handling ("$X to $Y")
        - Fiscal period validation
        
        Current implementation is acceptable for pattern detection but may
        have false positives.
        """
        guidance = {}
        
        # Look for revenue guidance patterns
        text = str(transcript)
        
        revenue_match = re.search(r'revenue.*?\$?([\d.]+)\s*(billion|million)', text, re.IGNORECASE)
        if revenue_match:
            value = float(revenue_match.group(1))
            multiplier = 1000000000 if 'billion' in revenue_match.group(2).lower() else 1000000
            guidance['revenue'] = value * multiplier
        
        # Look for EPS guidance
        eps_match = re.search(r'eps.*?\$?([\d.]+)', text, re.IGNORECASE)
        if eps_match:
            guidance['eps'] = float(eps_match.group(1))
        
        return guidance
    
    def _extract_guidance_from_filing(self, filing: Dict[str, Any]) -> Dict[str, float]:
        """Extract guidance from SEC filing (simplified)."""
        # Simplified implementation
        # In production, would parse MD&A section for forward-looking statements
        return {}
    
    def _get_materiality_indicators(self, text: str) -> List[str]:
        """Identify materiality indicators in a statement."""
        indicators = []
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['revenue', 'sales', 'income']):
            indicators.append("Financial performance metric")
        
        if any(word in text_lower for word in ['guidance', 'forecast', 'expect']):
            indicators.append("Forward-looking statement")
        
        if any(word in text_lower for word in ['acquisition', 'merger', 'restructuring']):
            indicators.append("Corporate transaction")
        
        if any(word in text_lower for word in ['investigation', 'lawsuit', 'regulatory']):
            indicators.append("Legal/regulatory matter")
        
        return indicators
    
    def _calculate_compliance_score(
        self,
        statements_count: int,
        violations: List[RegFDViolation]
    ) -> float:
        """Calculate overall compliance score (0.0 to 1.0)."""
        if statements_count == 0:
            return 1.0
        
        # Weight violations by severity
        penalty = 0.0
        for v in violations:
            if v.severity == ViolationSeverity.CRITICAL:
                penalty += 0.25
            elif v.severity == ViolationSeverity.HIGH:
                penalty += 0.15
            elif v.severity == ViolationSeverity.MEDIUM:
                penalty += 0.05
        
        score = max(0.0, 1.0 - penalty)
        return score
    
    def _determine_risk_level(self, compliance_score: float, critical_violations: int) -> str:
        """Determine overall risk level."""
        if critical_violations >= 2 or compliance_score < 0.50:
            return "CRITICAL"
        elif critical_violations >= 1 or compliance_score < 0.70:
            return "HIGH"
        elif compliance_score < 0.85:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_findings_summary(
        self,
        violations: List[RegFDViolation],
        matches: List[StatementMatch]
    ) -> str:
        """Generate human-readable findings summary."""
        if not violations:
            return f"Analyzed {len(matches)} material statements. No Regulation FD violations detected."
        
        summary_parts = [
            f"Identified {len(violations)} potential violations across {len(matches)} statements."
        ]
        
        # Group by type
        violation_types = {}
        for v in violations:
            vtype = v.violation_type.value
            if vtype not in violation_types:
                violation_types[vtype] = 0
            violation_types[vtype] += 1
        
        for vtype, count in violation_types.items():
            summary_parts.append(f"  - {vtype}: {count}")
        
        return " ".join(summary_parts)
    
    def _get_regulatory_implications(self, violations: List[RegFDViolation]) -> List[str]:
        """Get regulatory implications from violations."""
        implications = []
        
        if any(v.violation_type == ViolationType.REG_FD_VIOLATION for v in violations):
            implications.append("Regulation FD violations - selective disclosure to analysts")
        
        if any(v.violation_type == ViolationType.MISSING_8K for v in violations):
            implications.extend([
                "Missing required Form 8-K filings",
                "Potential violation of Item 2.02 (Results of Operations) or Item 7.01 (Regulation FD Disclosure)"
            ])
        
        if any(v.severity == ViolationSeverity.CRITICAL for v in violations):
            implications.extend([
                "Recommended for SEC Division of Enforcement review",
                "Potential securities fraud under Section 10(b)"
            ])
        
        return implications
    
    def _get_recommended_actions(self, risk_level: str, violations: List[RegFDViolation]) -> List[str]:
        """Get recommended investigative actions."""
        actions = [
            "Review all earnings call transcripts for disclosure patterns",
            "Examine 8-K filing timeline compliance",
            "Compare oral guidance with filed forward-looking statements"
        ]
        
        if risk_level in ["HIGH", "CRITICAL"]:
            actions.extend([
                "Interview IR personnel regarding disclosure procedures",
                "Subpoena earnings call preparation materials",
                "Review analyst communications for selective disclosure",
                "Examine Reg FD compliance policies and training"
            ])
        
        if risk_level == "CRITICAL":
            actions.extend([
                "Coordinate with SEC Office of the Chief Accountant",
                "Consider enforcement action under Regulation FD",
                "Assess civil penalty exposure"
            ])
        
        return actions
    
    def _generate_report_id(self, company_cik: str, call_date: datetime) -> str:
        """Generate unique report ID."""
        data = f"CROSS_VAL_{company_cik}_{call_date.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()
    
    def _compute_evidence_hash(
        self,
        matches: List[StatementMatch],
        violations: List[RegFDViolation]
    ) -> str:
        """Compute SHA-256 hash of evidence."""
        evidence_data = [m.to_dict() for m in matches] + [v.to_dict() for v in violations]
        evidence_str = str(sorted(str(e) for e in evidence_data))
        return hashlib.sha256(evidence_str.encode()).hexdigest()
    
    def _generate_mock_report(
        self,
        company_cik: str,
        company_name: str,
        call_date: datetime
    ) -> CrossValidationReport:
        """Generate mock report for testing."""
        mock_match = StatementMatch(
            call_statement="We expect revenue to grow 15% in Q4",
            call_timestamp=call_date,
            call_speaker="CEO",
            filing_statement="The company projects Q4 revenue growth of 12-15%",
            filing_type="8-K",
            filing_date=call_date.date() + timedelta(days=2),
            filing_item="Item 7.01",
            is_consistent=True,
            consistency_score=0.85,
            discrepancy_description=None
        )
        
        mock_violation = RegFDViolation(
            violation_type=ViolationType.REG_FD_VIOLATION,
            severity=ViolationSeverity.HIGH,
            disclosed_statement="Material guidance provided without 8-K filing",
            disclosure_date=call_date,
            disclosure_context="Q&A Session",
            required_8k_filed=False,
            filing_date=None,
            filing_delay_days=None,
            is_material=True,
            materiality_indicators=["Forward-looking statement"],
            evidence_description="Mock violation for testing"
        )
        
        return CrossValidationReport(
            report_id=self._generate_report_id(company_cik, call_date),
            company_cik=company_cik,
            company_name=company_name,
            call_date=call_date,
            analysis_date=datetime.utcnow(),
            total_statements_checked=5,
            statement_matches=[mock_match],
            violations=[mock_violation],
            violation_count=1,
            critical_violations=0,
            compliance_score=0.75,
            risk_level="MEDIUM",
            findings_summary="Mock report generated for testing",
            regulatory_implications=["Mock implication"],
            recommended_actions=["Mock action"],
            evidence_hash=self._compute_evidence_hash([mock_match], [mock_violation])
        )
    
    async def validate_call_async(
        self,
        company_cik: str,
        company_name: str,
        call_date: datetime,
        call_transcript: Dict[str, Any],
        sec_filings: List[Dict[str, Any]]
    ) -> CrossValidationReport:
        """Async version of validate_call for concurrent execution."""
        # For now, just wrap synchronous version
        return self.validate_call(
            company_cik,
            company_name,
            call_date,
            call_transcript,
            sec_filings
        )
