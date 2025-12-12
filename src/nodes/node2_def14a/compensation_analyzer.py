#!/usr/bin/env python3
"""
NODE 2: DEF 14A Executive Compensation Reconciliation Engine
Parses proxy statements to extract and validate executive compensation disclosures.
Detects: Say-on-Pay failures, compensation-performance misalignment, undisclosed perks,
related party transactions, golden parachute triggers.

Legal Basis: SEC Regulation S-K Item 402, Exchange Act Section 14A
"""

import re
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timezone
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompensationViolationType(Enum):
    """Classification of DEF 14A compensation violations"""
    SAY_ON_PAY_FAILURE = "say_on_pay_failure"
    PERFORMANCE_MISALIGNMENT = "compensation_performance_misalignment"
    UNDISCLOSED_PERKS = "undisclosed_perquisites"
    RELATED_PARTY_TRANSACTION = "related_party_transaction"
    GOLDEN_PARACHUTE_UNDISCLOSED = "golden_parachute_undisclosed"
    EXCESSIVE_SEVERANCE = "excessive_severance"
    BACKDATED_GRANTS = "backdated_option_grants"
    CLAWBACK_VIOLATION = "clawback_policy_violation"
    PEER_GROUP_MANIPULATION = "peer_group_manipulation"
    CD_A_MATERIAL_OMISSION = "cd_a_material_omission"


@dataclass
class ExecutiveCompensation:
    """Individual executive compensation record per Item 402(c)"""
    name: str
    title: str
    fiscal_year: int
    base_salary: Decimal
    bonus: Decimal
    stock_awards: Decimal  # Grant date fair value
    option_awards: Decimal  # Grant date fair value
    non_equity_incentive: Decimal
    change_in_pension: Decimal
    all_other_compensation: Decimal
    total_compensation: Decimal
    
    # Supplementary disclosure
    perquisites_detail: Dict[str, Decimal] = field(default_factory=dict)
    severance_provisions: Optional[Dict] = None
    equity_holdings: Optional[Dict] = None
    
    def validate_total(self) -> bool:
        """Verify reported total matches component sum"""
        calculated = (
            self.base_salary + self.bonus + self.stock_awards +
            self.option_awards + self.non_equity_incentive +
            self.change_in_pension + self.all_other_compensation
        )
        tolerance = Decimal("1000")  # Allow $1000 rounding variance
        return abs(calculated - self.total_compensation) <= tolerance
    
    def perks_exceed_threshold(self, threshold: Decimal = Decimal("10000")) -> bool:
        """Check if perquisites exceed disclosure threshold per Item 402(c)(2)(ix)"""
        total_perks = sum(self.perquisites_detail.values())
        return total_perks > threshold


@dataclass
class SayOnPayResult:
    """Say-on-Pay voting results per Exchange Act Rule 14a-21"""
    fiscal_year: int
    votes_for: int
    votes_against: int
    votes_abstain: int
    broker_non_votes: int
    approval_percentage: float
    passed: bool  # Generally requires >50%
    is_binding: bool = False  # Advisory unless company policy states binding


@dataclass
class PeerGroupAnalysis:
    """Compensation peer group analysis for manipulation detection"""
    reported_peers: List[str]
    peer_median_ceo_comp: Decimal
    peer_75th_percentile: Decimal
    company_ceo_comp: Decimal
    percentile_rank: float
    
    # Manipulation indicators
    peers_removed_this_year: List[str] = field(default_factory=list)
    peers_added_this_year: List[str] = field(default_factory=list)
    peer_revenue_range: Tuple[Decimal, Decimal] = (Decimal("0"), Decimal("0"))
    company_revenue: Decimal = Decimal("0")
    
    def detect_cherry_picking(self) -> bool:
        """Detect peer group manipulation via size mismatch"""
        if self.company_revenue == 0 or self.peer_revenue_range[1] == 0:
            return False
        # Flag if company is outside 50%-200% of peer median revenue
        peer_median_rev = (self.peer_revenue_range[0] + self.peer_revenue_range[1]) / 2
        ratio = self.company_revenue / peer_median_rev
        return ratio < Decimal("0.5") or ratio > Decimal("2.0")


@dataclass
class CompensationViolation:
    """Detected compensation-related violation"""
    violation_type: CompensationViolationType
    severity: int  # 1-10 scale
    description: str
    affected_executives: List[str]
    monetary_impact: Decimal
    regulatory_citations: List[str]
    evidence_text: str
    evidence_hash: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['violation_type'] = self.violation_type.value
        result['monetary_impact'] = str(self.monetary_impact)
        result['detected_at'] = self.detected_at.isoformat()
        return result


class DEF14ACompensationAnalyzer:
    """
    DEF 14A Proxy Statement Executive Compensation Analyzer
    
    Implements Item 402 Regulation S-K compliance validation:
    - Summary Compensation Table verification
    - CD&A narrative analysis
    - Say-on-Pay vote reconciliation
    - Peer group manipulation detection
    - Related party transaction identification
    - Golden parachute disclosure validation
    """
    
    # Perquisite categories requiring disclosure per Item 402(c)(2)(ix)
    PERK_CATEGORIES = [
        "personal_aircraft", "car_allowance", "club_memberships",
        "financial_planning", "security_services", "housing",
        "tax_gross_ups", "personal_travel", "spousal_travel"
    ]
    
    # Red flag phrases indicating potential omissions
    OMISSION_INDICATORS = [
        r"not\s+material",
        r"de\s+minimis",
        r"consistent\s+with\s+prior\s+years?",
        r"in\s+accordance\s+with\s+company\s+policy",
        r"competitive\s+with\s+peer\s+group"
    ]
    
    # Performance metric keywords for alignment analysis
    PERFORMANCE_METRICS = [
        "revenue", "eps", "earnings per share", "ebitda",
        "tsr", "total shareholder return", "roic", "roe",
        "operating income", "free cash flow", "net income"
    ]
    
    def __init__(self, output_dir: str = "./output/node2_def14a"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.violations: List[CompensationViolation] = []
        self.executives: List[ExecutiveCompensation] = []
        self.say_on_pay: Optional[SayOnPayResult] = None
        self.peer_analysis: Optional[PeerGroupAnalysis] = None
    
    def analyze_proxy_statement(
        self,
        proxy_text: str,
        company_financials: Dict[str, Any],
        prior_year_proxy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for DEF 14A analysis
        
        Args:
            proxy_text: Full text of DEF 14A filing
            company_financials: Dict with revenue, net_income, stock_return, etc.
            prior_year_proxy: Optional prior year proxy for trend analysis
            
        Returns:
            Complete analysis results with violations
        """
        logger.info("Beginning DEF 14A compensation analysis")
        
        # Phase 1: Extract Summary Compensation Table
        self.executives = self._extract_summary_compensation_table(proxy_text)
        logger.info(f"Extracted {len(self.executives)} executive compensation records")
        
        # Phase 2: Validate compensation totals
        self._validate_compensation_arithmetic()
        
        # Phase 3: Extract and analyze Say-on-Pay
        self.say_on_pay = self._extract_say_on_pay_results(proxy_text)
        if self.say_on_pay:
            self._analyze_say_on_pay_response(proxy_text)
        
        # Phase 4: Peer group analysis
        self.peer_analysis = self._extract_peer_group(proxy_text)
        if self.peer_analysis:
            self._detect_peer_group_manipulation()
        
        # Phase 5: Performance-compensation alignment
        self._analyze_pay_performance_alignment(company_financials)
        
        # Phase 6: Perquisite disclosure validation
        self._validate_perquisite_disclosures(proxy_text)
        
        # Phase 7: Related party transaction scan
        self._scan_related_party_transactions(proxy_text)
        
        # Phase 8: Golden parachute analysis
        self._analyze_golden_parachute_provisions(proxy_text)
        
        # Phase 9: CD&A material omission detection
        self._detect_cd_a_omissions(proxy_text)
        
        # Phase 10: Year-over-year comparison if prior proxy available
        if prior_year_proxy:
            self._compare_year_over_year(prior_year_proxy)
        
        return self._compile_results()
    
    def _extract_summary_compensation_table(self, text: str) -> List[ExecutiveCompensation]:
        """
        Parse Summary Compensation Table per Item 402(c)
        
        The SCT must include: Name, Principal Position, Year, Salary, Bonus,
        Stock Awards, Option Awards, Non-Equity Incentive Plan Compensation,
        Change in Pension Value and NQDC Earnings, All Other Compensation, Total
        """
        executives = []
        
        # Pattern to find compensation table section
        sct_pattern = r"(?i)summary\s+compensation\s+table"
        sct_match = re.search(sct_pattern, text)
        
        if not sct_match:
            logger.warning("Summary Compensation Table not found in proxy")
            return executives
        
        # Extract table region (next 5000 chars typically contains table)
        table_region = text[sct_match.end():sct_match.end() + 8000]
        
        # Pattern for monetary values with optional negative
        money_pattern = r'\$?\s*([\d,]+(?:\.\d{2})?|\([\d,]+(?:\.\d{2})?\)|-)'
        
        # Named executive officer pattern
        neo_pattern = r'(?P<name>[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)'
        
        # Common executive titles
        title_pattern = r'(?i)(chief\s+executive|ceo|president|cfo|chief\s+financial|' \
                       r'chief\s+operating|coo|general\s+counsel|chief\s+legal|' \
                       r'chief\s+human|evp|svp|executive\s+vice)'
        
        # This is a simplified extraction - production would use table parsing
        # For structured data, XBRL extraction is preferred
        
        # Demo extraction logic - would be enhanced with actual table parsing
        lines = table_region.split('\n')
        current_exec = None
        
        for line in lines:
            # Check for executive name line
            name_match = re.search(neo_pattern, line)
            title_match = re.search(title_pattern, line)
            
            if name_match and title_match:
                # Extract all monetary values from subsequent lines
                # This is placeholder logic - real implementation would parse
                # the actual table structure
                current_exec = ExecutiveCompensation(
                    name=name_match.group('name'),
                    title=title_match.group(0),
                    fiscal_year=datetime.now().year - 1,
                    base_salary=Decimal("0"),
                    bonus=Decimal("0"),
                    stock_awards=Decimal("0"),
                    option_awards=Decimal("0"),
                    non_equity_incentive=Decimal("0"),
                    change_in_pension=Decimal("0"),
                    all_other_compensation=Decimal("0"),
                    total_compensation=Decimal("0")
                )
                executives.append(current_exec)
        
        return executives
    
    def _validate_compensation_arithmetic(self) -> None:
        """Verify reported totals match component sums"""
        for exec_comp in self.executives:
            if not exec_comp.validate_total():
                self.violations.append(CompensationViolation(
                    violation_type=CompensationViolationType.CD_A_MATERIAL_OMISSION,
                    severity=6,
                    description=f"Compensation total mismatch for {exec_comp.name}: "
                               f"reported ${exec_comp.total_compensation} vs calculated sum",
                    affected_executives=[exec_comp.name],
                    monetary_impact=abs(exec_comp.total_compensation - (
                        exec_comp.base_salary + exec_comp.bonus + exec_comp.stock_awards +
                        exec_comp.option_awards + exec_comp.non_equity_incentive +
                        exec_comp.change_in_pension + exec_comp.all_other_compensation
                    )),
                    regulatory_citations=["17 CFR 229.402(c)", "Item 402(c) Regulation S-K"],
                    evidence_text=f"Executive: {exec_comp.name}, FY{exec_comp.fiscal_year}",
                    evidence_hash=self._hash_evidence(str(asdict(exec_comp)))
                ))
    
    def _extract_say_on_pay_results(self, text: str) -> Optional[SayOnPayResult]:
        """Extract Say-on-Pay advisory vote results per Rule 14a-21"""
        sop_pattern = r"(?i)say.on.pay|advisory\s+vote\s+on\s+(?:executive\s+)?compensation"
        sop_match = re.search(sop_pattern, text)
        
        if not sop_match:
            return None
        
        # Search for vote tallies
        vote_region = text[max(0, sop_match.start() - 500):sop_match.end() + 2000]
        
        # Pattern for vote counts
        vote_pattern = r'(?i)(?:for|against|abstain)[:\s]+(\d{1,3}(?:,\d{3})*)'
        
        votes = re.findall(vote_pattern, vote_region)
        
        if len(votes) >= 3:
            votes_for = int(votes[0].replace(',', ''))
            votes_against = int(votes[1].replace(',', ''))
            votes_abstain = int(votes[2].replace(',', ''))
            broker_non_votes = int(votes[3].replace(',', '')) if len(votes) > 3 else 0
            
            total_votes = votes_for + votes_against + votes_abstain
            approval_pct = (votes_for / total_votes * 100) if total_votes > 0 else 0
            
            return SayOnPayResult(
                fiscal_year=datetime.now().year - 1,
                votes_for=votes_for,
                votes_against=votes_against,
                votes_abstain=votes_abstain,
                broker_non_votes=broker_non_votes,
                approval_percentage=approval_pct,
                passed=approval_pct > 50
            )
        
        return None
    
    def _analyze_say_on_pay_response(self, text: str) -> None:
        """Analyze company response to Say-on-Pay results"""
        if not self.say_on_pay:
            return
        
        # Low approval (< 70%) typically triggers shareholder engagement
        if self.say_on_pay.approval_percentage < 70:
            # Check for responsive language
            response_patterns = [
                r"(?i)shareholder\s+engagement",
                r"(?i)compensation\s+committee\s+review",
                r"(?i)responsive\s+to\s+(?:shareholder|investor)",
                r"(?i)modified\s+(?:our\s+)?compensation"
            ]
            
            has_response = any(re.search(p, text) for p in response_patterns)
            
            if not has_response and self.say_on_pay.approval_percentage < 50:
                self.violations.append(CompensationViolation(
                    violation_type=CompensationViolationType.SAY_ON_PAY_FAILURE,
                    severity=8,
                    description=f"Say-on-Pay failed with {self.say_on_pay.approval_percentage:.1f}% "
                               f"approval. No responsive disclosure found in proxy.",
                    affected_executives=[e.name for e in self.executives],
                    monetary_impact=sum(e.total_compensation for e in self.executives),
                    regulatory_citations=[
                        "Exchange Act Rule 14a-21",
                        "Item 402(b) Regulation S-K"
                    ],
                    evidence_text=f"Votes For: {self.say_on_pay.votes_for:,}, "
                                 f"Against: {self.say_on_pay.votes_against:,}",
                    evidence_hash=self._hash_evidence(str(asdict(self.say_on_pay)))
                ))
    
    def _extract_peer_group(self, text: str) -> Optional[PeerGroupAnalysis]:
        """Extract compensation peer group for benchmarking analysis"""
        peer_pattern = r"(?i)(?:compensation\s+)?peer\s+group|benchmarking\s+(?:peer\s+)?companies"
        peer_match = re.search(peer_pattern, text)
        
        if not peer_match:
            return None
        
        # Extract peer company names from surrounding text
        peer_region = text[peer_match.start():peer_match.end() + 3000]
        
        # Common company name patterns (simplified)
        company_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Co|LLC|Ltd)\.?)?)'
        
        potential_peers = re.findall(company_pattern, peer_region)
        
        # Filter to likely peer companies (would need refinement)
        peers = [p for p in potential_peers if len(p) > 5 and len(p) < 50][:20]
        
        return PeerGroupAnalysis(
            reported_peers=peers,
            peer_median_ceo_comp=Decimal("0"),
            peer_75th_percentile=Decimal("0"),
            company_ceo_comp=self.executives[0].total_compensation if self.executives else Decimal("0"),
            percentile_rank=0.0
        )
    
    def _detect_peer_group_manipulation(self) -> None:
        """Detect cherry-picked peer groups favoring higher compensation"""
        if not self.peer_analysis:
            return
        
        if self.peer_analysis.detect_cherry_picking():
            self.violations.append(CompensationViolation(
                violation_type=CompensationViolationType.PEER_GROUP_MANIPULATION,
                severity=7,
                description="Peer group appears manipulated - company size significantly "
                           "outside peer group range, potentially inflating benchmarks",
                affected_executives=[e.name for e in self.executives],
                monetary_impact=Decimal("0"),  # Would calculate based on benchmark delta
                regulatory_citations=[
                    "Item 402(b) Regulation S-K",
                    "SEC Staff Observations on CD&A"
                ],
                evidence_text=f"Reported peers: {', '.join(self.peer_analysis.reported_peers[:5])}...",
                evidence_hash=self._hash_evidence(str(self.peer_analysis.reported_peers))
            ))
    
    def _analyze_pay_performance_alignment(self, financials: Dict[str, Any]) -> None:
        """
        Analyze alignment between executive pay and company performance
        
        Key metrics: TSR, Revenue Growth, EPS Growth, ROIC
        Red flags: Pay increases with declining performance
        """
        if not self.executives or not financials:
            return
        
        ceo_comp = self.executives[0].total_compensation if self.executives else Decimal("0")
        
        # Extract performance metrics
        tsr = financials.get('total_shareholder_return', 0)
        revenue_growth = financials.get('revenue_growth_pct', 0)
        eps_growth = financials.get('eps_growth_pct', 0)
        
        prior_ceo_comp = financials.get('prior_year_ceo_comp', ceo_comp)
        comp_change_pct = ((ceo_comp - prior_ceo_comp) / prior_ceo_comp * 100) if prior_ceo_comp else 0
        
        # Misalignment: Pay up significantly while performance down
        if comp_change_pct > 10 and tsr < -10:
            self.violations.append(CompensationViolation(
                violation_type=CompensationViolationType.PERFORMANCE_MISALIGNMENT,
                severity=8,
                description=f"CEO compensation increased {comp_change_pct:.1f}% while "
                           f"TSR declined {tsr:.1f}% - significant pay-performance disconnect",
                affected_executives=[self.executives[0].name],
                monetary_impact=ceo_comp - prior_ceo_comp,
                regulatory_citations=[
                    "Item 402(b) Regulation S-K",
                    "Exchange Act Section 14A"
                ],
                evidence_text=f"CEO Comp Change: {comp_change_pct:.1f}%, TSR: {tsr:.1f}%",
                evidence_hash=self._hash_evidence(f"{ceo_comp}:{tsr}")
            ))
    
    def _validate_perquisite_disclosures(self, text: str) -> None:
        """
        Validate perquisite disclosures per Item 402(c)(2)(ix)
        
        Perks must be disclosed if:
        - Total perks exceed $10,000, OR
        - Any single perk exceeds greater of $25,000 or 10% of total perks
        """
        perk_section_pattern = r"(?i)all\s+other\s+compensation|perquisites?"
        perk_match = re.search(perk_section_pattern, text)
        
        if not perk_match:
            # No perquisite section found - potential omission
            for exec_comp in self.executives:
                if exec_comp.all_other_compensation > Decimal("10000"):
                    self.violations.append(CompensationViolation(
                        violation_type=CompensationViolationType.UNDISCLOSED_PERKS,
                        severity=6,
                        description=f"All Other Compensation of ${exec_comp.all_other_compensation:,} "
                                   f"for {exec_comp.name} lacks itemized perquisite disclosure",
                        affected_executives=[exec_comp.name],
                        monetary_impact=exec_comp.all_other_compensation,
                        regulatory_citations=["Item 402(c)(2)(ix) Regulation S-K"],
                        evidence_text=f"{exec_comp.name}: ${exec_comp.all_other_compensation:,}",
                        evidence_hash=self._hash_evidence(f"{exec_comp.name}:{exec_comp.all_other_compensation}")
                    ))
    
    def _scan_related_party_transactions(self, text: str) -> None:
        """Scan for related party transactions per Item 404"""
        rpt_patterns = [
            r"(?i)related\s+(?:party|person)\s+transaction",
            r"(?i)certain\s+relationships\s+and\s+related\s+transactions",
            r"(?i)item\s+404",
            r"(?i)transactions\s+with\s+(?:related\s+)?(?:persons?|parties)"
        ]
        
        for pattern in rpt_patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                for match in matches:
                    context = text[match.start():match.end() + 1000]
                    
                    # Look for undisclosed or minimized related party transactions
                    minimization = re.search(
                        r"(?i)(?:no\s+)?(?:material\s+)?related\s+(?:party\s+)?transactions?"
                        r"(?:\s+(?:were|have\s+been))?\s+(?:required|necessary)",
                        context
                    )
                    
                    # Check for executive family members
                    family_pattern = r"(?i)(spouse|child|sibling|parent|family\s+member)"
                    family_match = re.search(family_pattern, context)
                    
                    if family_match and minimization:
                        self.violations.append(CompensationViolation(
                            violation_type=CompensationViolationType.RELATED_PARTY_TRANSACTION,
                            severity=7,
                            description="Potential undisclosed related party transaction involving "
                                       "executive family member with minimizing language",
                            affected_executives=[],
                            monetary_impact=Decimal("0"),
                            regulatory_citations=[
                                "Item 404 Regulation S-K",
                                "17 CFR 229.404"
                            ],
                            evidence_text=context[:500],
                            evidence_hash=self._hash_evidence(context[:500])
                        ))
                        break
    
    def _analyze_golden_parachute_provisions(self, text: str) -> None:
        """
        Analyze golden parachute/change-in-control provisions
        
        Per Item 402(j), must disclose arrangements providing compensation
        contingent on change in control
        """
        golden_patterns = [
            r"(?i)golden\s+parachute",
            r"(?i)change.in.control",
            r"(?i)severance\s+(?:arrangements?|agreements?|payments?)",
            r"(?i)termination\s+(?:benefits?|payments?)"
        ]
        
        for pattern in golden_patterns:
            match = re.search(pattern, text)
            if match:
                context = text[match.start():match.end() + 2000]
                
                # Look for excessive multiples
                multiple_pattern = r'(\d+(?:\.\d+)?)\s*(?:x|times?)\s*(?:base\s+)?salary'
                multiple_match = re.search(multiple_pattern, context, re.IGNORECASE)
                
                if multiple_match:
                    multiple = float(multiple_match.group(1))
                    if multiple > 3.0:  # Generally >3x is considered excessive
                        ceo_salary = self.executives[0].base_salary if self.executives else Decimal("0")
                        self.violations.append(CompensationViolation(
                            violation_type=CompensationViolationType.EXCESSIVE_SEVERANCE,
                            severity=6,
                            description=f"Excessive severance multiple of {multiple}x base salary "
                                       f"detected in change-in-control provisions",
                            affected_executives=[e.name for e in self.executives],
                            monetary_impact=ceo_salary * Decimal(str(multiple)),
                            regulatory_citations=[
                                "Item 402(j) Regulation S-K",
                                "IRC Section 280G"
                            ],
                            evidence_text=context[:500],
                            evidence_hash=self._hash_evidence(context[:500])
                        ))
                break
    
    def _detect_cd_a_omissions(self, text: str) -> None:
        """
        Detect material omissions in Compensation Discussion & Analysis
        
        CD&A must include: compensation objectives, elements, rationale for amounts,
        how each element relates to performance, role of executive officers in
        compensation decisions
        """
        cda_pattern = r"(?i)compensation\s+discussion\s+(?:and|&)\s+analysis"
        cda_match = re.search(cda_pattern, text)
        
        if not cda_match:
            self.violations.append(CompensationViolation(
                violation_type=CompensationViolationType.CD_A_MATERIAL_OMISSION,
                severity=9,
                description="Compensation Discussion & Analysis section not found in proxy - "
                           "required disclosure under Item 402(b)",
                affected_executives=[e.name for e in self.executives],
                monetary_impact=sum(e.total_compensation for e in self.executives),
                regulatory_citations=["Item 402(b) Regulation S-K"],
                evidence_text="CD&A section absent",
                evidence_hash=self._hash_evidence("CD&A_MISSING")
            ))
            return
        
        cda_section = text[cda_match.start():cda_match.end() + 15000]
        
        # Required CD&A elements per Item 402(b)
        required_elements = [
            (r"(?i)compensation\s+(?:objectives?|philosophy)", "compensation objectives"),
            (r"(?i)elements?\s+of\s+compensation", "compensation elements"),
            (r"(?i)performance\s+(?:metrics?|measures?|goals?)", "performance metrics"),
            (r"(?i)benchmarking|peer\s+group", "benchmarking methodology"),
        ]
        
        for pattern, element_name in required_elements:
            if not re.search(pattern, cda_section):
                self.violations.append(CompensationViolation(
                    violation_type=CompensationViolationType.CD_A_MATERIAL_OMISSION,
                    severity=5,
                    description=f"CD&A appears to omit required disclosure of {element_name}",
                    affected_executives=[],
                    monetary_impact=Decimal("0"),
                    regulatory_citations=["Item 402(b) Regulation S-K"],
                    evidence_text=f"Missing element: {element_name}",
                    evidence_hash=self._hash_evidence(f"OMISSION:{element_name}")
                ))
    
    def _compare_year_over_year(self, prior_proxy: str) -> None:
        """Compare current proxy to prior year for trend analysis"""
        # Placeholder for year-over-year comparison logic
        # Would extract prior year executives and compare compensation changes
        pass
    
    def _hash_evidence(self, evidence: str) -> str:
        """Generate SHA-256 hash of evidence for chain of custody"""
        return hashlib.sha256(evidence.encode('utf-8')).hexdigest()
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile analysis results into structured output"""
        results = {
            "node": "NODE_2_DEF14A",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "executives_analyzed": len(self.executives),
            "executives": [asdict(e) for e in self.executives],
            "say_on_pay": asdict(self.say_on_pay) if self.say_on_pay else None,
            "peer_group": asdict(self.peer_analysis) if self.peer_analysis else None,
            "violations_detected": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "severity_summary": {
                "critical": len([v for v in self.violations if v.severity >= 8]),
                "high": len([v for v in self.violations if 6 <= v.severity < 8]),
                "medium": len([v for v in self.violations if 4 <= v.severity < 6]),
                "low": len([v for v in self.violations if v.severity < 4])
            },
            "total_monetary_impact": str(sum(v.monetary_impact for v in self.violations)),
            "regulatory_routing": self._determine_routing()
        }
        
        # Write results to output directory
        output_path = self.output_dir / f"def14a_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"DEF 14A analysis complete. Results written to {output_path}")
        
        return results
    
    def _determine_routing(self) -> List[str]:
        """Determine regulatory routing based on violations"""
        routing = []
        
        for violation in self.violations:
            if violation.severity >= 8:
                if "fraud" in violation.description.lower():
                    routing.append("DOJ_SECURITIES_FRAUD")
                routing.append("SEC_ENFORCEMENT")
            elif violation.severity >= 6:
                routing.append("SEC_CORP_FIN_COMMENT")
        
        return list(set(routing))


# CLI Entry Point
if __name__ == "__main__":
    import sys
    
    analyzer = DEF14ACompensationAnalyzer()
    
    # Demo analysis with sample text
    sample_proxy = """
    SUMMARY COMPENSATION TABLE
    
    John Smith, Chief Executive Officer, 2024, $1,500,000, $2,000,000, 
    $5,000,000, $3,000,000, $1,500,000, $500,000, $200,000, $13,700,000
    
    Say-on-Pay Advisory Vote Results:
    For: 45,000,000
    Against: 55,000,000
    Abstain: 5,000,000
    
    Compensation Discussion and Analysis
    Our compensation philosophy is designed to attract and retain talent...
    """
    
    financials = {
        "total_shareholder_return": -15.5,
        "revenue_growth_pct": -8.2,
        "eps_growth_pct": -12.0,
        "prior_year_ceo_comp": 12000000
    }
    
    results = analyzer.analyze_proxy_statement(sample_proxy, financials)
    print(json.dumps(results, indent=2, default=str))
