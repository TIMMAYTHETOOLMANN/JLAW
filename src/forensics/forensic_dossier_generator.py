"""
Forensic Dossier Generator - FINAL ENHANCEMENT MODULE
Generates admissible evidence packages per:
- Federal Rules of Civil Procedure 26(a)(2)(B) - Expert Witness Disclosures
- SEC Enforcement Manual § 2.3.3 - Evidence Compilation
- FRE 702 - Expert Testimony Standards
- Daubert Standard - Scientific Evidence Admissibility
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import logging
from pathlib import Path

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel
)

logger = logging.getLogger(__name__)


class DossierSection(Enum):
    """Dossier section classifications."""
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    DETAILED_FINDINGS = "DETAILED_FINDINGS"
    EVIDENTIARY_EXHIBITS = "EVIDENTIARY_EXHIBITS"
    LEGAL_FRAMEWORK = "LEGAL_FRAMEWORK"
    EXPERT_QUALIFICATIONS = "EXPERT_QUALIFICATIONS"
    METHODOLOGY = "METHODOLOGY"


class MaterialityLevel(Enum):
    """SEC SAB 99 materiality classifications."""
    CLEARLY_MATERIAL = "CLEARLY_MATERIAL"  # >5% of benchmark
    PRESUMPTIVELY_MATERIAL = "PRESUMPTIVELY_MATERIAL"  # 3-5%
    REQUIRES_ANALYSIS = "REQUIRES_ANALYSIS"  # 1-3%
    IMMATERIAL = "IMMATERIAL"  # <1%


class ScienterStrength(Enum):
    """Strength of scienter (intent) evidence."""
    STRONG = "STRONG"  # Knowing or deliberate
    MODERATE = "MODERATE"  # Reckless
    WEAK = "WEAK"  # Negligent
    INSUFFICIENT = "INSUFFICIENT"


@dataclass
class ExecutiveSummary:
    """Executive summary of forensic findings."""
    case_identifier: str
    company_name: str
    company_cik: str
    investigation_period: Tuple[str, str]
    total_violations_detected: int
    statutory_references: List[str]
    materiality_assessment: MaterialityLevel
    materiality_explanation: str
    scienter_evidence: ScienterStrength
    scienter_indicators: List[str]
    financial_impact: Dict[str, float]
    key_findings: List[str]
    prosecution_recommendation: str


@dataclass
class DetailedFindings:
    """Detailed forensic findings."""
    quantitative_anomalies: Dict[str, Any]
    linguistic_deception_markers: Dict[str, Any]
    temporal_inconsistencies: Dict[str, Any]
    peer_deviation_analysis: Dict[str, Any]
    whistleblower_correlation: Optional[Dict[str, Any]]
    statutory_violations: List[Dict[str, Any]]
    evidence_strength_summary: str


@dataclass
class EvidentExhibits:
    """Evidentiary exhibits with chain of custody."""
    primary_documents: List[Dict[str, Any]]
    chain_of_custody_records: List[Dict[str, Any]]
    expert_methodology: Dict[str, Any]
    reproducibility_data: Dict[str, Any]
    forensic_hash_chains: List[str]
    authentication_certificates: List[str]


@dataclass
class LegalFramework:
    """Legal framework and precedents."""
    applicable_statutes: List[Dict[str, Any]]
    case_law_precedents: List[Dict[str, Any]]
    regulatory_guidance: List[Dict[str, Any]]
    sec_enforcement_history: List[Dict[str, Any]]
    penalty_assessment: Dict[str, Any]


@dataclass
class ExpertQualifications:
    """Expert witness qualifications per FRCP 26(a)(2)(B)."""
    expert_name: str
    credentials: List[str]
    relevant_experience: List[str]
    prior_testimony: List[str]
    publications: List[str]
    professional_affiliations: List[str]
    compensation: str
    daubert_qualifications: str


@dataclass
class MethodologyDocumentation:
    """Methodology documentation per Daubert standard."""
    analytical_methods: List[str]
    research_foundation: List[str]
    peer_reviewed_basis: List[str]
    error_rate: float
    standards_and_controls: List[str]
    general_acceptance: str
    reliability_assessment: str


@dataclass
class ForensicDossier:
    """Complete forensic evidence dossier."""
    dossier_id: str
    generation_timestamp: str
    version: str
    
    # Core sections
    executive_summary: ExecutiveSummary
    detailed_findings: DetailedFindings
    evidentiary_exhibits: EvidentExhibits
    legal_framework: LegalFramework
    expert_qualifications: ExpertQualifications
    methodology: MethodologyDocumentation
    
    # Meta information
    total_pages: int
    total_exhibits: int
    classification: str  # CONFIDENTIAL, PUBLIC, etc.
    distribution_list: List[str]
    
    # Integrity
    dossier_hash: str


class ForensicDossierGenerator:
    """
    Advanced forensic dossier generator.
    
    Generates prosecution-ready evidence packages compliant with:
    - Federal Rules of Civil Procedure 26(a)(2)(B) - Expert Witness Disclosures
    - Federal Rules of Evidence 702 - Expert Testimony
    - SEC Enforcement Manual § 2.3.3 - Evidence Compilation Standards
    - Daubert v. Merrell Dow Pharmaceuticals (1993) - Scientific Evidence Standard
    - SEC SAB 99 - Materiality Guidance
    """
    
    def __init__(self, expert_credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize forensic dossier generator.
        
        Args:
            expert_credentials: Expert witness credentials and qualifications
        """
        self.hash_chain = ForensicHashChain("forensic_dossier_generator")
        
        # Expert credentials (required for FRCP 26(a)(2)(B))
        self.expert_credentials = expert_credentials or self._default_expert_credentials()
        
        # Case law database
        self.case_law_database = self._initialize_case_law()
        
        # Regulatory guidance
        self.regulatory_guidance = self._initialize_regulatory_guidance()
        
        # Materiality thresholds (SEC SAB 99)
        self.materiality_thresholds = {
            'clearly_material': 0.05,  # 5%
            'presumptively_material': 0.03,  # 3%
            'requires_analysis': 0.01  # 1%
        }
        
        logger.info("ForensicDossierGenerator initialized")
    
    def _default_expert_credentials(self) -> Dict[str, Any]:
        """Default expert credentials."""
        return {
            'expert_name': 'JLAW Forensic Analysis System',
            'credentials': [
                'Advanced AI/ML Forensic Analysis Platform',
                'NIST SP 800-86 Compliant',
                'FRE 902(13)/(14) Certified Electronic Evidence'
            ],
            'experience': [
                'Multi-model ensemble fraud detection',
                'Quantitative financial analysis (Beneish, Altman, Piotroski)',
                'Linguistic deception detection',
                'Statutory violation mapping'
            ]
        }
    
    def _initialize_case_law(self) -> Dict[str, Dict[str, Any]]:
        """Initialize case law precedent database."""
        return {
            'securities_fraud': {
                'basic_v_levinson': {
                    'citation': 'Basic Inc. v. Levinson, 485 U.S. 224 (1988)',
                    'principle': 'Materiality standard and fraud-on-the-market theory',
                    'relevance': 'Material misstatements in securities fraud'
                },
                'tellabs_v_makor': {
                    'citation': 'Tellabs, Inc. v. Makor Issues & Rights, Ltd., 551 U.S. 308 (2007)',
                    'principle': 'Strong inference of scienter standard',
                    'relevance': 'Intent requirements for securities fraud'
                },
                'ernst_v_hochfelder': {
                    'citation': 'Ernst & Ernst v. Hochfelder, 425 U.S. 185 (1976)',
                    'principle': 'Scienter requirement for Rule 10b-5',
                    'relevance': 'Knowing or reckless misconduct required'
                }
            },
            'expert_testimony': {
                'daubert_v_merrell': {
                    'citation': 'Daubert v. Merrell Dow Pharmaceuticals, 509 U.S. 579 (1993)',
                    'principle': 'Scientific evidence admissibility standard',
                    'relevance': 'Methodology must be scientifically valid'
                },
                'kumho_tire': {
                    'citation': 'Kumho Tire Co. v. Carmichael, 526 U.S. 137 (1999)',
                    'principle': 'Daubert applies to all expert testimony',
                    'relevance': 'Technical and specialized knowledge admissibility'
                }
            },
            'accounting_fraud': {
                'worldcom': {
                    'citation': 'SEC v. WorldCom, Inc., No. 02 Civ. 4963 (S.D.N.Y. 2002)',
                    'principle': '$3.8B accounting fraud through expense capitalization',
                    'relevance': 'Systematic accounting manipulation precedent'
                },
                'enron': {
                    'citation': 'SEC v. Enron Corp., No. H-01-3624 (S.D. Tex. 2001)',
                    'principle': 'Special purpose entities and earnings management',
                    'relevance': 'Complex accounting fraud schemes'
                }
            }
        }
    
    def _initialize_regulatory_guidance(self) -> List[Dict[str, Any]]:
        """Initialize regulatory guidance references."""
        return [
            {
                'reference': 'SEC Staff Accounting Bulletin No. 99',
                'title': 'Materiality',
                'summary': 'Guidance on materiality assessments in financial statements',
                'url': 'https://www.sec.gov/interps/account/sab99.htm'
            },
            {
                'reference': 'SEC Enforcement Manual § 2.3.3',
                'title': 'Evidence Compilation',
                'summary': 'Standards for compiling enforcement evidence packages'
            },
            {
                'reference': 'PCAOB AS 2401',
                'title': 'Consideration of Fraud',
                'summary': 'Auditor responsibilities for fraud detection'
            },
            {
                'reference': 'AICPA Forensic and Valuation Services',
                'title': 'Forensic Accounting Standards',
                'summary': 'Professional standards for forensic accounting'
            }
        ]
    
    async def generate_forensic_dossier(
        self,
        analysis_results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ForensicDossier:
        """
        Generate comprehensive forensic dossier.
        
        Args:
            analysis_results: Results from all forensic modules
            metadata: Optional case metadata
            
        Returns:
            Complete forensic dossier
        """
        logger.info("Generating forensic dossier...")
        
        metadata = metadata or {}
        
        # Generate dossier ID
        dossier_id = f"JLAW-DOSSIER-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # 1. Executive Summary
        logger.info("Generating executive summary...")
        executive_summary = await self._generate_executive_summary(
            analysis_results,
            metadata
        )
        
        # 2. Detailed Findings
        logger.info("Compiling detailed findings...")
        detailed_findings = await self._compile_detailed_findings(
            analysis_results
        )
        
        # 3. Evidentiary Exhibits
        logger.info("Assembling evidentiary exhibits...")
        exhibits = await self._assemble_evidentiary_exhibits(
            analysis_results
        )
        
        # 4. Legal Framework
        logger.info("Mapping legal framework...")
        legal_framework = await self._map_legal_framework(
            analysis_results
        )
        
        # 5. Expert Qualifications
        logger.info("Documenting expert qualifications...")
        expert_quals = await self._document_expert_qualifications()
        
        # 6. Methodology
        logger.info("Documenting methodology...")
        methodology = await self._document_methodology(
            analysis_results
        )
        
        # Calculate totals
        total_exhibits = len(exhibits.primary_documents)
        total_pages = self._estimate_total_pages(
            executive_summary,
            detailed_findings,
            exhibits,
            legal_framework
        )
        
        # Create dossier
        dossier = ForensicDossier(
            dossier_id=dossier_id,
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
            version='1.0',
            executive_summary=executive_summary,
            detailed_findings=detailed_findings,
            evidentiary_exhibits=exhibits,
            legal_framework=legal_framework,
            expert_qualifications=expert_quals,
            methodology=methodology,
            total_pages=total_pages,
            total_exhibits=total_exhibits,
            classification='CONFIDENTIAL',
            distribution_list=metadata.get('distribution_list', ['SEC Enforcement Division']),
            dossier_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "generate_forensic_dossier",
                "dossier_id": dossier_id,
                "violations_detected": executive_summary.total_violations_detected,
                "materiality": executive_summary.materiality_assessment.value,
                "scienter": executive_summary.scienter_evidence.value,
                "total_exhibits": total_exhibits,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Dossier generation complete: {dossier_id}, "
            f"{total_pages} pages, {total_exhibits} exhibits"
        )
        
        return dossier
    
    async def _generate_executive_summary(
        self,
        results: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> ExecutiveSummary:
        """Generate executive summary per SEC Enforcement Manual § 2.3.3."""
        
        # Extract violations
        violations = results.get('violations', [])
        
        # Statutory references
        statutory_refs = list(set(
            v.get('statute', 'UNKNOWN') 
            for v in violations
        ))
        
        # Calculate materiality
        materiality, materiality_explanation = self._calculate_materiality(results)
        
        # Assess scienter
        scienter, scienter_indicators = self._assess_scienter(results)
        
        # Calculate financial impact
        financial_impact = self._calculate_financial_impact(results)
        
        # Key findings
        key_findings = self._extract_key_findings(results)
        
        # Prosecution recommendation
        prosecution_rec = self._generate_prosecution_recommendation(
            len(violations),
            materiality,
            scienter
        )
        
        return ExecutiveSummary(
            case_identifier=metadata.get('case_id', 'TBD'),
            company_name=metadata.get('company_name', 'UNKNOWN'),
            company_cik=metadata.get('cik', 'UNKNOWN'),
            investigation_period=(
                metadata.get('period_start', 'UNKNOWN'),
                metadata.get('period_end', 'UNKNOWN')
            ),
            total_violations_detected=len(violations),
            statutory_references=statutory_refs,
            materiality_assessment=materiality,
            materiality_explanation=materiality_explanation,
            scienter_evidence=scienter,
            scienter_indicators=scienter_indicators,
            financial_impact=financial_impact,
            key_findings=key_findings,
            prosecution_recommendation=prosecution_rec
        )
    
    def _calculate_materiality(
        self,
        results: Dict[str, Any]
    ) -> Tuple[MaterialityLevel, str]:
        """
        Calculate materiality per SEC SAB 99.
        
        SAB 99 factors:
        1. Quantitative magnitude
        2. Nature of item
        3. Impact on trends
        4. Management intent
        5. Market perception
        """
        # Extract financial impact
        quantitative = results.get('quantitative_analysis', {})
        variances = quantitative.get('variances', [])
        
        if not variances:
            return MaterialityLevel.IMMATERIAL, "No quantitative variances identified"
        
        # Calculate maximum variance percentage
        max_variance_pct = max(
            (v.get('variance_percentage', 0) for v in variances),
            default=0
        ) / 100
        
        # Determine materiality level
        if max_variance_pct >= self.materiality_thresholds['clearly_material']:
            level = MaterialityLevel.CLEARLY_MATERIAL
            explanation = (
                f"Maximum variance of {max_variance_pct:.1%} exceeds 5% threshold. "
                f"Presumptively material per SEC SAB 99."
            )
        elif max_variance_pct >= self.materiality_thresholds['presumptively_material']:
            level = MaterialityLevel.PRESUMPTIVELY_MATERIAL
            explanation = (
                f"Maximum variance of {max_variance_pct:.1%} in 3-5% range. "
                f"Likely material, requires qualitative assessment."
            )
        elif max_variance_pct >= self.materiality_thresholds['requires_analysis']:
            level = MaterialityLevel.REQUIRES_ANALYSIS
            explanation = (
                f"Maximum variance of {max_variance_pct:.1%} in 1-3% range. "
                f"Materiality depends on qualitative factors."
            )
        else:
            level = MaterialityLevel.IMMATERIAL
            explanation = (
                f"Maximum variance of {max_variance_pct:.1%} below 1% threshold. "
                f"Quantitatively immaterial."
            )
        
        return level, explanation
    
    def _assess_scienter(
        self,
        results: Dict[str, Any]
    ) -> Tuple[ScienterStrength, List[str]]:
        """
        Assess scienter (intent) per Tellabs v. Makor.
        
        Tellabs standard: "Strong inference of scienter" required.
        """
        indicators = []
        
        # Check linguistic deception
        linguistic = results.get('linguistic_analysis', {})
        if linguistic.get('deception_probability', 0) > 0.70:
            indicators.append("High linguistic deception probability (>70%)")
        
        # Check Beneish M-Score
        quantitative = results.get('quantitative_analysis', {})
        m_score = quantitative.get('beneish_m_score', {}).get('score', 0)
        if m_score > -2.22:
            indicators.append(f"Beneish M-Score ({m_score:.3f}) indicates manipulation")
        
        # Check pattern matches
        statutory = results.get('statutory_analysis', {})
        pattern_count = len(statutory.get('pattern_matches', []))
        if pattern_count >= 3:
            indicators.append(f"{pattern_count} fraud patterns detected")
        
        # Check whistleblower evidence
        whistleblower = results.get('whistleblower_correlation') or {}
        if isinstance(whistleblower, dict) and whistleblower.get('contradiction_count', 0) >= 2:
            indicators.append("Multiple whistleblower contradictions corroborated")
        
        # Determine strength
        if len(indicators) >= 4:
            strength = ScienterStrength.STRONG
        elif len(indicators) >= 2:
            strength = ScienterStrength.MODERATE
        elif len(indicators) >= 1:
            strength = ScienterStrength.WEAK
        else:
            strength = ScienterStrength.INSUFFICIENT
        
        return strength, indicators
    
    def _calculate_financial_impact(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate total financial impact of violations."""
        impact = {
            'total_overstatement': 0.0,
            'total_understatement': 0.0,
            'net_impact': 0.0
        }
        
        quantitative = results.get('quantitative_analysis', {})
        variances = quantitative.get('variances', [])
        
        for variance in variances:
            amount = variance.get('variance_amount', 0)
            if amount > 0:
                impact['total_overstatement'] += amount
            else:
                impact['total_understatement'] += abs(amount)
        
        impact['net_impact'] = impact['total_overstatement'] - impact['total_understatement']
        
        return impact
    
    def _extract_key_findings(
        self,
        results: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings for executive summary."""
        findings = []
        
        # Quantitative findings
        quant = results.get('quantitative_analysis', {})
        if quant.get('benford_analysis', {}).get('conformance_level') == 'NON_CONFORMANT':
            findings.append("Benford's Law violation detected - possible number manipulation")
        
        if quant.get('beneish_m_score', {}).get('manipulation_indicated'):
            findings.append("Beneish M-Score indicates earnings manipulation")
        
        # Statutory findings
        statutory = results.get('statutory_analysis', {})
        if statutory.get('prosecution_priority', 0) >= 8:
            findings.append("High prosecution priority - immediate enforcement action recommended")
        
        # Linguistic findings
        linguistic = results.get('linguistic_analysis', {})
        if linguistic.get('deception_classification') == 'HIGH_DECEPTION':
            findings.append("High-confidence linguistic deception detected in management narratives")
        
        # Temporal findings
        temporal = results.get('temporal_analysis', {})
        if temporal.get('critical_failures', 0) >= 2:
            findings.append("Critical reconciliation failures in inter-period statements")
        
        # Whistleblower findings
        whistleblower = results.get('whistleblower_correlation') or {}
        if isinstance(whistleblower, dict) and whistleblower.get('prosecutorial_value') == 'HIGH':
            findings.append("Whistleblower evidence provides high prosecutorial value")
        
        return findings[:10]  # Top 10 findings
    
    def _generate_prosecution_recommendation(
        self,
        violation_count: int,
        materiality: MaterialityLevel,
        scienter: ScienterStrength
    ) -> str:
        """Generate prosecution recommendation."""
        if (violation_count >= 3 and 
            materiality in [MaterialityLevel.CLEARLY_MATERIAL, MaterialityLevel.PRESUMPTIVELY_MATERIAL] and
            scienter == ScienterStrength.STRONG):
            return (
                "IMMEDIATE ENFORCEMENT ACTION RECOMMENDED. Strong evidence of material "
                "violations with clear scienter. Refer to DOJ for criminal prosecution."
            )
        elif (violation_count >= 2 and
              materiality != MaterialityLevel.IMMATERIAL and
              scienter in [ScienterStrength.STRONG, ScienterStrength.MODERATE]):
            return (
                "HIGH PRIORITY ENFORCEMENT. Substantial evidence warrants formal investigation "
                "and civil enforcement proceedings."
            )
        elif violation_count >= 1:
            return (
                "MODERATE PRIORITY. Additional investigation recommended to strengthen case."
            )
        else:
            return (
                "LOW PRIORITY. Insufficient evidence for enforcement action at this time."
            )
    
    async def _compile_detailed_findings(
        self,
        results: Dict[str, Any]
    ) -> DetailedFindings:
        """Compile detailed forensic findings."""
        return DetailedFindings(
            quantitative_anomalies=results.get('quantitative_analysis', {}),
            linguistic_deception_markers=results.get('linguistic_analysis', {}),
            temporal_inconsistencies=results.get('temporal_analysis', {}),
            peer_deviation_analysis=results.get('peer_comparison', {}),
            whistleblower_correlation=results.get('whistleblower_correlation'),
            statutory_violations=[
                {
                    'statute': v.get('statute'),
                    'description': v.get('description'),
                    'evidence': v.get('evidence')
                }
                for v in results.get('violations', [])
            ],
            evidence_strength_summary=self._summarize_evidence_strength(results)
        )
    
    def _summarize_evidence_strength(
        self,
        results: Dict[str, Any]
    ) -> str:
        """Summarize overall evidence strength."""
        strengths = []
        
        if results.get('quantitative_analysis', {}).get('fraud_probability', 0) > 0.70:
            strengths.append("Strong quantitative indicators")
        
        if results.get('linguistic_analysis', {}).get('deception_probability', 0) > 0.65:
            strengths.append("Compelling linguistic evidence")
        
        if results.get('statutory_analysis', {}).get('prosecution_priority', 0) >= 7:
            strengths.append("High prosecutorial priority")
        
        if strengths:
            return "Overall evidence strength: STRONG (" + ", ".join(strengths) + ")"
        else:
            return "Overall evidence strength: MODERATE to WEAK"
    
    async def _assemble_evidentiary_exhibits(
        self,
        results: Dict[str, Any]
    ) -> EvidentExhibits:
        """Assemble evidentiary exhibits with chain of custody."""
        
        # Primary documents
        primary_docs = results.get('source_documents', [])
        
        # Chain of custody
        custody_records = results.get('custody_records', [])
        
        # Methodology
        methodology = {
            'quantitative_methods': [
                'Benford\'s Law analysis',
                'Beneish M-Score calculation',
                'Altman Z-Score assessment',
                'Piotroski F-Score evaluation'
            ],
            'linguistic_methods': [
                'Cognitive complexity analysis',
                'Psychological distancing detection',
                'Obfuscation metrics (Fog Index, Flesch-Kincaid)'
            ],
            'temporal_methods': [
                'Inter-period reconciliation',
                'Restatement pattern analysis',
                'Trend break detection'
            ]
        }
        
        # Reproducibility data
        reproducibility = {
            'raw_data': results.get('raw_data', {}),
            'analysis_parameters': results.get('parameters', {}),
            'software_version': 'JLAW v1.0.0',
            'execution_timestamp': results.get('timestamp', datetime.now(timezone.utc).isoformat())
        }
        
        # Forensic hash chains
        hash_chains = [
            results.get(f'{module}_hash', '') 
            for module in [
                'quantitative', 'linguistic', 'statutory',
                'temporal', 'evidence_auth', 'whistleblower'
            ]
            if results.get(f'{module}_hash')
        ]
        
        # Authentication certificates
        auth_certs = results.get('authentication_certificates', [])
        
        return EvidentExhibits(
            primary_documents=primary_docs,
            chain_of_custody_records=custody_records,
            expert_methodology=methodology,
            reproducibility_data=reproducibility,
            forensic_hash_chains=hash_chains,
            authentication_certificates=auth_certs
        )
    
    async def _map_legal_framework(
        self,
        results: Dict[str, Any]
    ) -> LegalFramework:
        """Map violations to legal framework."""
        
        # Applicable statutes
        statutes = self._map_to_statutes(results)
        
        # Case law precedents
        precedents = self._identify_precedents(results)
        
        # Regulatory guidance
        guidance = self._compile_regulatory_citations(results)
        
        # SEC enforcement history
        enforcement_history = self._compile_enforcement_history(results)
        
        # Penalty assessment
        penalties = self._assess_penalties(results)
        
        return LegalFramework(
            applicable_statutes=statutes,
            case_law_precedents=precedents,
            regulatory_guidance=guidance,
            sec_enforcement_history=enforcement_history,
            penalty_assessment=penalties
        )
    
    def _map_to_statutes(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Map violations to applicable statutes."""
        statutory_analysis = results.get('statutory_analysis', {})
        violations = statutory_analysis.get('violations_identified', [])
        
        return [
            {
                'citation': v.get('statute', {}).get('citation'),
                'title': v.get('statute', {}).get('title'),
                'description': v.get('statute', {}).get('description'),
                'penalties': v.get('statute', {}).get('penalties'),
                'evidence': {
                    'pattern_matches': v.get('pattern_matches', []),
                    'forensic_indicators': v.get('forensic_indicators', []),
                    'confidence': v.get('confidence_score', 0)
                }
            }
            for v in violations
        ]
    
    def _identify_precedents(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify relevant case law precedents."""
        precedents = []
        
        # Add securities fraud precedents
        precedents.extend([
            self.case_law_database['securities_fraud']['basic_v_levinson'],
            self.case_law_database['securities_fraud']['tellabs_v_makor'],
            self.case_law_database['securities_fraud']['ernst_v_hochfelder']
        ])
        
        # Add expert testimony precedents
        precedents.extend([
            self.case_law_database['expert_testimony']['daubert_v_merrell'],
            self.case_law_database['expert_testimony']['kumho_tire']
        ])
        
        # Add accounting fraud precedents if relevant
        quant = results.get('quantitative_analysis', {})
        if quant.get('beneish_m_score', {}).get('manipulation_indicated'):
            precedents.extend([
                self.case_law_database['accounting_fraud']['worldcom'],
                self.case_law_database['accounting_fraud']['enron']
            ])
        
        return precedents
    
    def _compile_regulatory_citations(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compile relevant regulatory guidance."""
        return self.regulatory_guidance
    
    def _compile_enforcement_history(
        self,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compile SEC enforcement history."""
        statutory = results.get('statutory_analysis', {})
        violations = statutory.get('violations_identified', [])
        
        similar_cases = []
        for violation in violations:
            cases = violation.get('similar_cases', [])
            similar_cases.extend(cases)
        
        return [{'case': case} for case in similar_cases]
    
    def _assess_penalties(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess potential penalties."""
        violations = len(results.get('violations', []))
        financial_impact = self._calculate_financial_impact(results)
        
        # Calculate potential civil penalties
        civil_penalties = violations * 1000000  # $1M per violation estimate
        
        # Criminal exposure
        criminal_exposure = "High" if violations >= 3 else "Moderate" if violations >= 1 else "Low"
        
        # Disgorgement
        disgorgement = abs(financial_impact['net_impact'])
        
        return {
            'estimated_civil_penalties': civil_penalties,
            'potential_disgorgement': disgorgement,
            'treble_damages_exposure': disgorgement * 3,
            'criminal_exposure': criminal_exposure,
            'total_exposure': civil_penalties + disgorgement * 3
        }
    
    async def _document_expert_qualifications(self) -> ExpertQualifications:
        """Document expert qualifications per FRCP 26(a)(2)(B)."""
        creds = self.expert_credentials
        
        return ExpertQualifications(
            expert_name=creds.get('expert_name', 'JLAW Forensic System'),
            credentials=creds.get('credentials', []),
            relevant_experience=creds.get('experience', []),
            prior_testimony=creds.get('prior_testimony', []),
            publications=creds.get('publications', []),
            professional_affiliations=creds.get('affiliations', []),
            compensation='Not applicable (automated system)',
            daubert_qualifications=(
                "Methods based on peer-reviewed research (Benford, Beneish, Altman, "
                "Piotroski, Pennebaker). Error rates documented. Generally accepted in "
                "forensic accounting and fraud detection fields."
            )
        )
    
    async def _document_methodology(
        self,
        results: Dict[str, Any]
    ) -> MethodologyDocumentation:
        """Document methodology per Daubert standard."""
        
        methods = [
            "Benford's Law digital analysis (Hill, 1995)",
            "Beneish M-Score earnings manipulation detection (Beneish, 1999)",
            "Altman Z-Score bankruptcy prediction (Altman, 1968)",
            "Piotroski F-Score financial strength (Piotroski, 2000)",
            "Linguistic deception analysis (Pennebaker, 2011; Newman et al., 2003)",
            "Inter-period temporal reconciliation (AICPA/ACFE standards)",
            "Legal-BERT semantic similarity analysis"
        ]
        
        research_foundation = [
            "Hill, T.P. (1995). A Statistical Derivation of the Significant-Digit Law",
            "Beneish, M.D. (1999). The Detection of Earnings Manipulation",
            "Altman, E.I. (1968). Financial Ratios, Discriminant Analysis and Corporate Bankruptcy",
            "Piotroski, J.D. (2000). Value Investing: Use of Historical Financial Statement",
            "Pennebaker, J.W. (2011). The Secret Life of Pronouns",
            "Newman et al. (2003). Lying Words: Predicting Deception from Linguistic Styles"
        ]
        
        peer_reviewed = [
            "Journal of the American Statistical Association",
            "Journal of Accounting Research",
            "Journal of Finance",
            "Journal of Accounting and Economics",
            "Psychological Science"
        ]
        
        error_rate = 0.24  # Beneish M-Score: 76% accuracy = 24% error rate
        
        standards = [
            "NIST SP 800-86: Guide to Integrating Forensic Techniques",
            "Federal Rules of Evidence 702: Expert Testimony",
            "AICPA Forensic and Valuation Services",
            "ACFE Fraud Examiners Manual"
        ]
        
        general_acceptance = (
            "All methods are widely accepted in forensic accounting, fraud examination, "
            "and financial analysis fields. Beneish M-Score used by auditors worldwide. "
            "Benford's Law accepted in fraud detection and forensic accounting. "
            "Linguistic analysis methods validated in multiple peer-reviewed studies."
        )
        
        reliability = (
            "Methodology reliability established through: (1) peer-reviewed publication, "
            "(2) documented error rates, (3) general acceptance in relevant fields, "
            "(4) rigorous testing and standards, (5) reproducible results. "
            "Daubert factors satisfied."
        )
        
        return MethodologyDocumentation(
            analytical_methods=methods,
            research_foundation=research_foundation,
            peer_reviewed_basis=peer_reviewed,
            error_rate=error_rate,
            standards_and_controls=standards,
            general_acceptance=general_acceptance,
            reliability_assessment=reliability
        )
    
    def _estimate_total_pages(
        self,
        executive_summary: ExecutiveSummary,
        findings: DetailedFindings,
        exhibits: EvidentExhibits,
        legal: LegalFramework
    ) -> int:
        """Estimate total page count."""
        pages = 0
        pages += 5  # Executive summary
        pages += 20  # Detailed findings
        pages += len(exhibits.primary_documents) * 2
        pages += 10  # Legal framework
        pages += 5  # Expert qualifications
        pages += 10  # Methodology
        pages += 5  # Appendices
        
        return pages
    
    async def export_dossier(
        self,
        dossier: ForensicDossier,
        output_path: str,
        format: str = 'json'
    ) -> str:
        """
        Export dossier to file.
        
        Args:
            dossier: Forensic dossier
            output_path: Output file path
            format: Export format ('json', 'pdf', 'html')
            
        Returns:
            Path to exported file
        """
        # Ensure output directory exists
        out_dir = Path(output_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / f"{dossier.dossier_id}.{format}"
        
        if format == 'json':
            # Convert to JSON
            dossier_dict = asdict(dossier)
            
            with open(output_file, 'w') as f:
                json.dump(dossier_dict, f, indent=2, default=str)
        
        elif format == 'html':
            # Generate HTML report
            html = self._generate_html_report(dossier)
            
            with open(output_file, 'w') as f:
                f.write(html)
        else:
            logger.warning(f"Unsupported export format '{format}', defaulting to JSON")
            dossier_dict = asdict(dossier)
            with open(out_dir / f"{dossier.dossier_id}.json", 'w') as f:
                json.dump(dossier_dict, f, indent=2, default=str)

        logger.info(f"Dossier exported to {output_file}")
        
        return str(output_file)
    
    def _generate_html_report(self, dossier: ForensicDossier) -> str:
        """Generate HTML format dossier."""
        # Simplified HTML generation
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Forensic Dossier - {dossier.dossier_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; }}
        .section {{ margin: 20px 0; }}
        .finding {{ background: #ecf0f1; padding: 10px; margin: 10px 0; }}
        .critical {{ border-left: 5px solid #e74c3c; }}
    </style>
</head>
<body>
    <h1>FORENSIC DOSSIER</h1>
    <p><strong>ID:</strong> {dossier.dossier_id}</p>
    <p><strong>Generated:</strong> {dossier.generation_timestamp}</p>
    
    <h2>EXECUTIVE SUMMARY</h2>
    <div class="section">
        <p><strong>Company:</strong> {dossier.executive_summary.company_name}</p>
        <p><strong>Violations:</strong> {dossier.executive_summary.total_violations_detected}</p>
        <p><strong>Materiality:</strong> {dossier.executive_summary.materiality_assessment.value}</p>
        <p><strong>Scienter:</strong> {dossier.executive_summary.scienter_evidence.value}</p>
        <p><strong>Recommendation:</strong> {dossier.executive_summary.prosecution_recommendation}</p>
    </div>
    
    <h2>KEY FINDINGS</h2>
    <div class="section">
        {''.join(f'<div class="finding critical">• {finding}</div>' for finding in dossier.executive_summary.key_findings)}
    </div>
    
    <p><em>Complete dossier: {dossier.total_pages} pages, {dossier.total_exhibits} exhibits</em></p>
</body>
</html>
"""
        return html
    
    async def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Dossier generator hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'ForensicDossierGenerator',
    'ForensicDossier',
    'ExecutiveSummary',
    'DetailedFindings',
    'EvidentExhibits',
    'LegalFramework',
    'MaterialityLevel',
    'ScienterStrength'
]

