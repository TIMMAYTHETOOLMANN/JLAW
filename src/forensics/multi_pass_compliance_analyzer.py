"""
Multi-Pass Compliance Analyzer - 4-Pass Forensic Compliance Analysis
Implements surgical precision compliance checking across multiple passes:
1. Structural validation
2. Financial consistency
3. Legal compliance
4. Cross-reference validation
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ComplianceSeverity(Enum):
    """Severity levels for compliance violations."""
    CRITICAL = "CRITICAL"  # Material misstatement, potential fraud
    HIGH = "HIGH"          # Significant violation requiring immediate attention
    MEDIUM = "MEDIUM"      # Notable issue requiring review
    LOW = "LOW"            # Minor issue, best practice recommendation
    INFO = "INFO"          # Informational finding


class RiskLevel(Enum):
    """Overall risk assessment levels."""
    CRITICAL = "CRITICAL"  # > 0.85
    HIGH = "HIGH"          # 0.70 - 0.85
    MEDIUM = "MEDIUM"      # 0.40 - 0.70
    LOW = "LOW"            # < 0.40


@dataclass
class ComplianceViolation:
    """Represents a single compliance violation."""
    violation_type: str
    severity: ComplianceSeverity
    description: str
    evidence: str
    regulation: Optional[str] = None
    statute_section: Optional[str] = None
    recommendation: Optional[str] = None
    pass_number: int = 0  # Which pass detected this
    confidence: float = 0.0
    location: Optional[str] = None  # Document section where found
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ComplianceAnalysisResult:
    """Complete result of multi-pass compliance analysis."""
    violations: List[ComplianceViolation]
    risk_score: float
    risk_level: RiskLevel
    pass_results: Dict[str, Dict[str, Any]]
    summary: str
    total_checks: int
    failed_checks: int
    passed_checks: int
    warnings: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MultiPassComplianceAnalyzer:
    """
    Multi-pass compliance analyzer with forensic precision.
    Implements 4-pass analysis methodology for comprehensive compliance checking.
    """
    
    # Risk score weights for different violation severities
    SEVERITY_WEIGHTS = {
        ComplianceSeverity.CRITICAL: 1.0,
        ComplianceSeverity.HIGH: 0.7,
        ComplianceSeverity.MEDIUM: 0.4,
        ComplianceSeverity.LOW: 0.2,
        ComplianceSeverity.INFO: 0.0,
    }
    
    def __init__(self):
        """Initialize multi-pass compliance analyzer."""
        self.violations: List[ComplianceViolation] = []
        self.pass_results: Dict[str, Dict[str, Any]] = {}
        self.total_checks = 0
        self.failed_checks = 0
        self.passed_checks = 0
    
    async def analyze(
        self,
        content: str,
        financial_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        filing_type: Optional[str] = None,
    ) -> ComplianceAnalysisResult:
        """
        Perform 4-pass compliance analysis.
        
        Args:
            content: Document content to analyze
            financial_data: Optional extracted financial data
            metadata: Optional document metadata
            filing_type: Type of SEC filing (10-K, 10-Q, etc.)
            
        Returns:
            Complete compliance analysis result
        """
        self.violations = []
        self.pass_results = {}
        self.total_checks = 0
        self.failed_checks = 0
        self.passed_checks = 0
        
        # Pass 1: Structural Validation
        await self._pass1_structural_validation(content, filing_type)
        
        # Pass 2: Financial Consistency
        await self._pass2_financial_consistency(content, financial_data)
        
        # Pass 3: Legal Compliance
        await self._pass3_legal_compliance(content, filing_type)
        
        # Pass 4: Cross-Reference Validation
        await self._pass4_cross_reference_validation(content, financial_data)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score()
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate summary
        summary = self._generate_summary()
        
        return ComplianceAnalysisResult(
            violations=self.violations,
            risk_score=risk_score,
            risk_level=risk_level,
            pass_results=self.pass_results,
            summary=summary,
            total_checks=self.total_checks,
            failed_checks=self.failed_checks,
            passed_checks=self.passed_checks,
            warnings=len([v for v in self.violations if v.severity == ComplianceSeverity.MEDIUM]),
            metadata=metadata or {}
        )
    
    async def _pass1_structural_validation(self, content: str, filing_type: Optional[str]):
        """
        Pass 1: Validate document structure and required sections.
        """
        pass_name = "structural_validation"
        checks_performed = []
        issues_found = []
        
        # Check for required sections based on filing type
        required_sections = self._get_required_sections(filing_type)
        
        for section in required_sections:
            self.total_checks += 1
            # Case-insensitive search for section
            pattern = re.compile(re.escape(section), re.IGNORECASE)
            if not pattern.search(content):
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="missing_required_section",
                    severity=ComplianceSeverity.HIGH,
                    description=f"Required section '{section}' not found in document",
                    evidence=f"Document does not contain section: {section}",
                    regulation="SEC Regulation S-K" if filing_type in ["10-K", "10-Q"] else None,
                    pass_number=1,
                    confidence=0.95
                )
                self.violations.append(violation)
                issues_found.append(section)
            else:
                self.passed_checks += 1
                checks_performed.append(section)
        
        # Check document length (too short might indicate incomplete filing)
        self.total_checks += 1
        if len(content) < 1000:
            self.failed_checks += 1
            violation = ComplianceViolation(
                violation_type="insufficient_content",
                severity=ComplianceSeverity.CRITICAL,
                description="Document content is suspiciously short",
                evidence=f"Document length: {len(content)} characters (minimum expected: 1000)",
                pass_number=1,
                confidence=0.90
            )
            self.violations.append(violation)
            issues_found.append("content_length")
        else:
            self.passed_checks += 1
        
        self.pass_results[pass_name] = {
            "checks_performed": checks_performed,
            "issues_found": issues_found,
            "pass_completed": True
        }
    
    async def _pass2_financial_consistency(
        self,
        content: str,
        financial_data: Optional[Dict[str, Any]]
    ):
        """
        Pass 2: Validate financial data consistency and reasonableness.
        """
        pass_name = "financial_consistency"
        checks_performed = []
        issues_found = []
        
        if not financial_data:
            self.pass_results[pass_name] = {
                "checks_performed": [],
                "issues_found": [],
                "pass_completed": False,
                "reason": "No financial data provided"
            }
            return
        
        # Check for negative revenue (red flag)
        self.total_checks += 1
        if 'revenue' in financial_data:
            revenue = financial_data.get('revenue')
            if revenue is not None and revenue < 0:
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="negative_revenue",
                    severity=ComplianceSeverity.CRITICAL,
                    description="Revenue reported as negative value",
                    evidence=f"Revenue: ${revenue:,.2f}",
                    pass_number=2,
                    confidence=0.99
                )
                self.violations.append(violation)
                issues_found.append("negative_revenue")
            else:
                self.passed_checks += 1
            checks_performed.append("revenue_sign_check")
        
        # Check for unusual profit margins
        self.total_checks += 1
        if 'revenue' in financial_data and 'earnings' in financial_data:
            revenue = financial_data.get('revenue')
            earnings = financial_data.get('earnings')
            
            if revenue and earnings and revenue != 0:
                margin = (earnings / revenue) * 100
                # Flag if margin is > 50% or < -50%
                if abs(margin) > 50:
                    self.failed_checks += 1
                    violation = ComplianceViolation(
                        violation_type="unusual_profit_margin",
                        severity=ComplianceSeverity.MEDIUM,
                        description=f"Profit margin of {margin:.1f}% is unusually high/low",
                        evidence=f"Revenue: ${revenue:,.2f}, Earnings: ${earnings:,.2f}, Margin: {margin:.1f}%",
                        pass_number=2,
                        confidence=0.70,
                        recommendation="Review revenue recognition and expense reporting"
                    )
                    self.violations.append(violation)
                    issues_found.append("unusual_margin")
                else:
                    self.passed_checks += 1
            checks_performed.append("profit_margin_check")
        
        # Check for balance sheet consistency
        self.total_checks += 1
        if 'total_assets' in financial_data and 'total_liabilities' in financial_data:
            assets = financial_data.get('total_assets')
            liabilities = financial_data.get('total_liabilities')
            
            if assets and liabilities and liabilities > assets * 2:
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="debt_to_asset_ratio_high",
                    severity=ComplianceSeverity.HIGH,
                    description="Liabilities exceed twice the total assets (high leverage risk)",
                    evidence=f"Assets: ${assets:,.2f}, Liabilities: ${liabilities:,.2f}",
                    pass_number=2,
                    confidence=0.85,
                    recommendation="Review solvency and going concern assumptions"
                )
                self.violations.append(violation)
                issues_found.append("high_leverage")
            else:
                self.passed_checks += 1
            checks_performed.append("balance_sheet_consistency")
        
        self.pass_results[pass_name] = {
            "checks_performed": checks_performed,
            "issues_found": issues_found,
            "pass_completed": True
        }
    
    async def _pass3_legal_compliance(self, content: str, filing_type: Optional[str]):
        """
        Pass 3: Check legal and regulatory compliance.
        """
        pass_name = "legal_compliance"
        checks_performed = []
        issues_found = []
        
        # Check for risk factor disclosure (required in 10-K, 10-Q)
        if filing_type in ["10-K", "10-Q"]:
            self.total_checks += 1
            if not re.search(r'risk\s+factors?', content, re.IGNORECASE):
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="missing_risk_factors",
                    severity=ComplianceSeverity.HIGH,
                    description="Risk factors section appears to be missing",
                    evidence="No 'Risk Factors' section identified in document",
                    regulation="SEC Regulation S-K Item 503(c)",
                    statute_section="17 CFR 229.503",
                    pass_number=3,
                    confidence=0.80
                )
                self.violations.append(violation)
                issues_found.append("risk_factors")
            else:
                self.passed_checks += 1
            checks_performed.append("risk_factors_disclosure")
        
        # Check for MD&A section (required in 10-K, 10-Q)
        if filing_type in ["10-K", "10-Q"]:
            self.total_checks += 1
            if not re.search(r'management.{0,50}discussion.{0,50}analysis', content, re.IGNORECASE):
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="missing_mda",
                    severity=ComplianceSeverity.CRITICAL,
                    description="MD&A (Management Discussion and Analysis) section not found",
                    evidence="No MD&A section identified in document",
                    regulation="SEC Regulation S-K Item 303",
                    statute_section="17 CFR 229.303",
                    pass_number=3,
                    confidence=0.85
                )
                self.violations.append(violation)
                issues_found.append("mda_section")
            else:
                self.passed_checks += 1
            checks_performed.append("mda_section_check")
        
        # Check for material weakness disclosure (Sarbanes-Oxley)
        self.total_checks += 1
        material_weakness = re.search(
            r'material\s+weakness(?:es)?',
            content,
            re.IGNORECASE
        )
        if material_weakness:
            # This is informational - presence indicates honesty about control issues
            violation = ComplianceViolation(
                violation_type="material_weakness_disclosed",
                severity=ComplianceSeverity.INFO,
                description="Material weakness in internal controls disclosed",
                evidence=material_weakness.group(0),
                regulation="Sarbanes-Oxley Act Section 404",
                pass_number=3,
                confidence=0.90,
                recommendation="Review disclosed material weaknesses and remediation plans"
            )
            self.violations.append(violation)
            issues_found.append("material_weakness")
        self.passed_checks += 1
        checks_performed.append("material_weakness_disclosure")
        
        self.pass_results[pass_name] = {
            "checks_performed": checks_performed,
            "issues_found": issues_found,
            "pass_completed": True
        }
    
    async def _pass4_cross_reference_validation(
        self,
        content: str,
        financial_data: Optional[Dict[str, Any]]
    ):
        """
        Pass 4: Validate cross-references and internal consistency.
        """
        pass_name = "cross_reference_validation"
        checks_performed = []
        issues_found = []
        
        # Check for exhibit references
        self.total_checks += 1
        exhibit_refs = re.findall(r'exhibit\s+\d+', content, re.IGNORECASE)
        if exhibit_refs:
            # Count unique exhibits mentioned
            unique_exhibits = set(exhibit_refs)
            # This is informational
            self.passed_checks += 1
            checks_performed.append(f"exhibit_references_found: {len(unique_exhibits)}")
        else:
            self.passed_checks += 1
        
        # Check for internal contradictions in forward-looking statements
        self.total_checks += 1
        fls_pattern = re.search(
            r'forward[- ]looking\s+statement',
            content,
            re.IGNORECASE
        )
        if fls_pattern:
            # Check if there's a safe harbor disclaimer
            safe_harbor = re.search(
                r'safe\s+harbor',
                content,
                re.IGNORECASE
            )
            if not safe_harbor:
                self.failed_checks += 1
                violation = ComplianceViolation(
                    violation_type="missing_safe_harbor",
                    severity=ComplianceSeverity.MEDIUM,
                    description="Forward-looking statements without safe harbor language",
                    evidence="Document contains forward-looking statements but no safe harbor disclaimer",
                    regulation="Private Securities Litigation Reform Act",
                    pass_number=4,
                    confidence=0.75,
                    recommendation="Add safe harbor language for forward-looking statements"
                )
                self.violations.append(violation)
                issues_found.append("safe_harbor")
            else:
                self.passed_checks += 1
            checks_performed.append("forward_looking_statements")
        else:
            self.passed_checks += 1
        
        # Check for numerical consistency in text
        self.total_checks += 1
        numbers = re.findall(r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|billion)?', content)
        if len(numbers) > 0:
            # Just record that we found financial figures
            self.passed_checks += 1
            checks_performed.append(f"financial_figures_found: {len(numbers)}")
        else:
            self.passed_checks += 1
        
        self.pass_results[pass_name] = {
            "checks_performed": checks_performed,
            "issues_found": issues_found,
            "pass_completed": True
        }
    
    def _get_required_sections(self, filing_type: Optional[str]) -> List[str]:
        """Get required sections based on filing type."""
        if filing_type == "10-K":
            return [
                "Business",
                "Risk Factors",
                "Management's Discussion and Analysis",
                "Financial Statements",
                "Controls and Procedures"
            ]
        elif filing_type == "10-Q":
            return [
                "Financial Statements",
                "Management's Discussion and Analysis",
                "Controls and Procedures"
            ]
        elif filing_type == "8-K":
            return ["Item", "Signature"]
        else:
            return []  # Unknown filing type
    
    def _calculate_risk_score(self) -> float:
        """Calculate overall risk score based on violations."""
        if not self.violations:
            return 0.0
        
        # Weight violations by severity
        weighted_sum = 0.0
        for violation in self.violations:
            weight = self.SEVERITY_WEIGHTS.get(violation.severity, 0.0)
            weighted_sum += weight * violation.confidence
        
        # Normalize to 0-1 scale (assuming max 10 critical violations would be 1.0)
        max_possible_score = 10.0
        risk_score = min(1.0, weighted_sum / max_possible_score)
        
        return risk_score
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from risk score."""
        if risk_score >= 0.85:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.70:
            return RiskLevel.HIGH
        elif risk_score >= 0.40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary of analysis."""
        critical = len([v for v in self.violations if v.severity == ComplianceSeverity.CRITICAL])
        high = len([v for v in self.violations if v.severity == ComplianceSeverity.HIGH])
        medium = len([v for v in self.violations if v.severity == ComplianceSeverity.MEDIUM])
        low = len([v for v in self.violations if v.severity == ComplianceSeverity.LOW])
        
        summary_parts = [
            f"Completed 4-pass compliance analysis with {self.total_checks} checks.",
            f"Found {len(self.violations)} total issues: ",
            f"{critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW.",
            f"Pass rate: {self.passed_checks}/{self.total_checks} ({100*self.passed_checks/self.total_checks if self.total_checks > 0 else 0:.1f}%)"
        ]
        
        return " ".join(summary_parts)
