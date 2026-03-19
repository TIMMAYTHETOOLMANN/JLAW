"""
SEC EDGAR Forensic Analyzer
============================

Core SEC filing forensic analysis engine providing:
- Entity extraction (MONEY, PERCENT, DATE patterns)
- Violation detection with regulatory citation mapping
- Risk scoring and confidence calculation
- FRE 902(13)/(14) compliant evidence hash computation

This module is imported by:
- src/forensics/anthropic_agent_analyzer.py
- src/forensics/openai_secondary_agent.py
- src/forensics/agent_sec_analyzer.py
"""

import asyncio
import hashlib
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FilingType(Enum):
    """SEC filing types."""
    FORM_3 = "3"
    FORM_4 = "4"
    FORM_5 = "5"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    DEF_14A = "DEF 14A"
    SCHEDULE_13D = "SC 13D"
    SCHEDULE_13G = "SC 13G"
    FORM_13F = "13F-HR"
    FORM_144 = "144"
    UNKNOWN = "UNKNOWN"


class ViolationSeverity(Enum):
    """Severity levels for detected violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RegulatoryAgency(Enum):
    """Regulatory agencies for enforcement routing."""
    SEC = "SEC"
    DOJ = "DOJ"
    IRS = "IRS"
    FINRA = "FINRA"


@dataclass
class ExtractedEntity:
    """Entity extracted from filing text."""
    entity_type: str  # MONEY, PERCENT, DATE, ORG, PERSON
    value: str
    position: int
    context: str = ""


@dataclass
class DetectedViolation:
    """Detected regulatory violation."""
    violation_type: str
    severity: ViolationSeverity
    description: str
    regulatory_citation: str
    confidence: float
    evidence_quote: str
    document_url: str
    statute: str = ""
    estimated_damages: Optional[float] = None


@dataclass
class FilingAnalysis:
    """
    Complete analysis result for a single SEC filing.
    
    This dataclass is the standard output format for SEC forensic analysis,
    used across all agent-based analyzers (Anthropic, OpenAI, manual).
    """
    cik: str
    filing_type: str
    filing_date: datetime
    period_end_date: datetime
    delay_days: int
    amendments: List[str]
    red_flags: List[Dict[str, Any]]
    fraud_indicators: Dict[str, Any]
    cross_reference_issues: List[Dict[str, Any]]
    revenue_anomalies: List[Dict[str, Any]]
    benford_analysis: Dict[str, Any]
    narrative_consistency: float
    integrity_hash: str
    
    def __post_init__(self):
        """Compute integrity hash if not provided."""
        if not self.integrity_hash:
            self.integrity_hash = self._compute_integrity_hash()
    
    def _compute_integrity_hash(self) -> str:
        """
        Compute SHA-256 evidence hash for FRE 902(13)/(14) compliance.
        
        Returns:
            Hex-encoded SHA-256 hash of analysis data
        """
        # Create canonical representation for hashing
        canonical_data = {
            'cik': self.cik,
            'filing_type': self.filing_type,
            'filing_date': self.filing_date.isoformat() if isinstance(self.filing_date, (date, datetime)) else str(self.filing_date),
            'period_end_date': self.period_end_date.isoformat() if isinstance(self.period_end_date, (date, datetime)) else str(self.period_end_date),
            'red_flags_count': len(self.red_flags),
            'fraud_indicators': str(self.fraud_indicators),
        }
        
        # Serialize to stable string format
        canonical_str = str(sorted(canonical_data.items()))
        
        # Compute SHA-256
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'cik': self.cik,
            'filing_type': self.filing_type,
            'filing_date': self.filing_date.isoformat() if isinstance(self.filing_date, (date, datetime)) else str(self.filing_date),
            'period_end_date': self.period_end_date.isoformat() if isinstance(self.period_end_date, (date, datetime)) else str(self.period_end_date),
            'delay_days': self.delay_days,
            'amendments': self.amendments,
            'red_flags': self.red_flags,
            'fraud_indicators': self.fraud_indicators,
            'cross_reference_issues': self.cross_reference_issues,
            'revenue_anomalies': self.revenue_anomalies,
            'benford_analysis': self.benford_analysis,
            'narrative_consistency': self.narrative_consistency,
            'integrity_hash': self.integrity_hash,
        }


class MockEdgarClient:
    """
    Mock SEC EDGAR client for testing when the actual client is unavailable.
    Provides minimal functionality to allow forensic analyzers to function.
    """
    
    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        logger.info("Initialized MockEdgarClient (testing mode)")
    
    async def fetch_filing_content(self, document_url: str) -> str:
        """Mock fetch filing content."""
        logger.warning(f"MockEdgarClient: Simulating fetch for {document_url}")
        return f"Mock filing content for {document_url}"
    
    async def get_form4_filings(self, cik: str, **kwargs) -> List[Dict[str, Any]]:
        """Mock get Form 4 filings."""
        return []
    
    async def close(self):
        """Mock close connection."""
        pass


class SECForensicAnalyzer:
    """
    Core SEC filing forensic analysis engine.
    
    Provides:
    - Entity extraction (MONEY, PERCENT, DATE patterns)
    - Violation detection with regulatory citation mapping
    - Risk scoring and confidence calculation
    - Caching support
    
    This is the manual analyzer used as a fallback when AI agents fail,
    and also provides baseline analysis capabilities.
    """
    
    # Violation patterns with regulatory citations
    VIOLATION_PATTERNS = {
        'securities_fraud': {
            'pattern': r'(material misstatement|false statement|fraudulent|omit material fact)',
            'citation': '17 CFR § 240.10b-5',
            'severity': ViolationSeverity.HIGH,
            'statute': 'Securities Exchange Act § 10(b)'
        },
        'insider_trading': {
            'pattern': r'(insider trading|material non-public information|tippee)',
            'citation': '17 CFR § 240.10b5-1, 10b5-2',
            'severity': ViolationSeverity.CRITICAL,
            'statute': 'Securities Exchange Act § 10(b)'
        },
        'sox_302_failure': {
            'pattern': r'(inadequate internal control|material weakness|control deficiency)',
            'citation': 'SOX Section 302',
            'severity': ViolationSeverity.HIGH,
            'statute': 'Sarbanes-Oxley Act § 302'
        },
        'sox_404_failure': {
            'pattern': r'(ineffective internal control over financial reporting)',
            'citation': 'SOX Section 404',
            'severity': ViolationSeverity.HIGH,
            'statute': 'Sarbanes-Oxley Act § 404'
        },
        'beneficial_ownership_violation': {
            'pattern': r'(failed to file|late filing|13D|13G|beneficial owner)',
            'citation': '17 CFR § 240.13d-1',
            'severity': ViolationSeverity.MEDIUM,
            'statute': 'Securities Exchange Act § 13(d)'
        },
        'proxy_disclosure_violation': {
            'pattern': r'(inadequate disclosure|misleading proxy|executive compensation)',
            'citation': '17 CFR § 240.14a-9',
            'severity': ViolationSeverity.MEDIUM,
            'statute': 'Securities Exchange Act § 14(a)'
        }
    }
    
    # Entity extraction patterns
    ENTITY_PATTERNS = {
        'MONEY': re.compile(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand))?'),
        'PERCENT': re.compile(r'\d+(?:\.\d+)?%'),
        'DATE': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}'),
    }
    
    def __init__(self, user_agent: Optional[str] = None, rate_limit: float = 8.0):
        """
        Initialize SEC forensic analyzer.
        
        Args:
            user_agent: SEC-compliant User-Agent string
            rate_limit: Rate limit in requests per second (default: 8)
        """
        self.user_agent = user_agent or "JLAW-Forensics/4.1.0 (contact@example.com)"
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._cache: Dict[str, FilingAnalysis] = {}
        self._sec_client = None  # Lazy-loaded
        
        logger.info(f"Initialized SECForensicAnalyzer with rate_limit={rate_limit} req/sec")
    
    async def _get_sec_client(self):
        """Lazy-load SEC EDGAR client."""
        if self._sec_client is None:
            try:
                from src.integrations.sec_edgar.edgar_client import SECEdgarClient
                self._sec_client = SECEdgarClient(user_agent=self.user_agent)
                logger.info("Loaded real SECEdgarClient")
            except ImportError:
                logger.warning("SECEdgarClient not available, using MockEdgarClient")
                self._sec_client = MockEdgarClient(user_agent=self.user_agent)
        return self._sec_client
    
    async def _rate_limit_wait(self):
        """Enforce rate limiting (8 req/sec for SEC EDGAR API compliance)."""
        import time
        now = time.time()
        time_since_last = now - self._last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    def _extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract entities from filing text.
        
        Args:
            text: Filing text content
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            for match in pattern.finditer(text):
                entity = ExtractedEntity(
                    entity_type=entity_type,
                    value=match.group(0),
                    position=match.start(),
                    context=text[max(0, match.start()-50):min(len(text), match.end()+50)]
                )
                entities.append(entity)
        
        return entities
    
    def _detect_violations(self, text: str, document_url: str) -> List[DetectedViolation]:
        """
        Detect regulatory violations in filing text.
        
        Args:
            text: Filing text content
            document_url: URL of the document
            
        Returns:
            List of detected violations
        """
        violations = []
        
        for violation_type, config in self.VIOLATION_PATTERNS.items():
            pattern = re.compile(config['pattern'], re.IGNORECASE)
            matches = list(pattern.finditer(text))
            
            for match in matches:
                # Extract evidence quote (context around match)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                evidence_quote = text[start:end]
                
                # Calculate confidence based on pattern specificity
                confidence = 0.7 if len(matches) > 2 else 0.6
                
                violation = DetectedViolation(
                    violation_type=violation_type,
                    severity=config['severity'],
                    description=f"Detected {violation_type.replace('_', ' ')} pattern",
                    regulatory_citation=config['citation'],
                    confidence=confidence,
                    evidence_quote=evidence_quote,
                    document_url=document_url,
                    statute=config['statute']
                )
                violations.append(violation)
        
        return violations
    
    def _calculate_risk_score(self, violations: List[DetectedViolation]) -> float:
        """
        Calculate overall risk score based on detected violations.
        
        Args:
            violations: List of detected violations
            
        Returns:
            Risk score from 0.0 to 1.0
        """
        if not violations:
            return 0.0
        
        severity_weights = {
            ViolationSeverity.LOW: 0.2,
            ViolationSeverity.MEDIUM: 0.4,
            ViolationSeverity.HIGH: 0.7,
            ViolationSeverity.CRITICAL: 1.0,
        }
        
        total_score = sum(severity_weights[v.severity] * v.confidence for v in violations)
        max_possible = len(violations)
        
        return min(1.0, total_score / max_possible if max_possible > 0 else 0.0)
    
    async def analyze_filing(
        self,
        cik: str,
        accession_number: str,
        filing_type: str,
        document_url: str,
        viewer_url: Optional[str] = None,
        filing_date: Optional[str] = None
    ) -> FilingAnalysis:
        """
        Analyze a single SEC filing for violations and fraud indicators.
        
        Args:
            cik: Company CIK
            accession_number: Filing accession number
            filing_type: Form type (e.g., "4", "10-K", "DEF 14A")
            document_url: URL to the primary document
            viewer_url: Optional viewer URL
            filing_date: Optional filing date (ISO format)
            
        Returns:
            FilingAnalysis with detected violations and fraud indicators
        """
        # Check cache first
        cache_key = f"{cik}:{accession_number}:{filing_type}"
        if cache_key in self._cache:
            logger.info(f"[SECForensicAnalyzer] Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        logger.info(f"[SECForensicAnalyzer] Analyzing {filing_type} for CIK {cik}")
        
        try:
            # Rate limiting
            await self._rate_limit_wait()
            
            # Fetch document content (mock for now)
            sec_client = await self._get_sec_client()
            try:
                import aiohttp
                async with aiohttp.ClientSession(trust_env=True) as session:
                    async with session.get(document_url, headers={'User-Agent': self.user_agent}) as response:
                        if response.status == 200:
                            content = await response.text()
                        else:
                            logger.warning(f"Failed to fetch {document_url}: HTTP {response.status}")
                            content = f"Failed to fetch content from {document_url}"
            except Exception as e:
                logger.warning(f"Error fetching content: {e}")
                content = f"Error fetching content: {e}"
            
            # Extract entities
            entities = self._extract_entities(content)
            
            # Detect violations
            violations = self._detect_violations(content, document_url)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(violations)
            
            # Parse dates
            if filing_date:
                try:
                    filing_dt = datetime.fromisoformat(filing_date.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    filing_dt = datetime.now()
            else:
                filing_dt = datetime.now()
            
            # Build FilingAnalysis
            analysis = FilingAnalysis(
                cik=cik,
                filing_type=filing_type,
                filing_date=filing_dt,
                period_end_date=filing_dt,
                delay_days=0,
                amendments=[],
                red_flags=[{
                    'type': v.violation_type,
                    'severity': v.severity.value,
                    'description': v.description,
                    'exact_quote': v.evidence_quote,
                    'document_url': document_url,
                    'viewer_url': viewer_url or document_url,
                    'section': 'manual_analysis',
                    'prosecutorial_merit': 'STRONG' if v.severity == ViolationSeverity.CRITICAL else 'MODERATE',
                    'estimated_damages': v.estimated_damages,
                    'evidence_refs': [document_url],
                    'statute': v.statute,
                    'analyzer': 'sec_forensic_analyzer'
                } for v in violations],
                fraud_indicators={
                    'manual_violations': len(violations),
                    'risk_score': risk_score,
                    'entity_count': len(entities),
                    'high_severity_count': sum(1 for v in violations if v.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL])
                },
                cross_reference_issues=[],
                revenue_anomalies=[],
                benford_analysis={},
                narrative_consistency=1.0 - risk_score,
                integrity_hash=""  # Will be computed in __post_init__
            )
            
            # Cache result
            self._cache[cache_key] = analysis
            
            logger.info(f"[SECForensicAnalyzer] ✓ Detected {len(violations)} violations, risk_score={risk_score:.2f}")
            return analysis
        
        except Exception as e:
            logger.error(f"[SECForensicAnalyzer] Error during analysis: {e}", exc_info=True)
            
            # Return minimal analysis on error
            return FilingAnalysis(
                cik=cik,
                filing_type=filing_type,
                filing_date=datetime.now(),
                period_end_date=datetime.now(),
                delay_days=0,
                amendments=[],
                red_flags=[],
                fraud_indicators={'error': str(e)},
                cross_reference_issues=[],
                revenue_anomalies=[],
                benford_analysis={},
                narrative_consistency=0.0,
                integrity_hash=""
            )
    
    async def batch_analyze(
        self,
        filings: List[Dict[str, Any]]
    ) -> List[FilingAnalysis]:
        """
        Analyze multiple filings in batch.
        
        Args:
            filings: List of filing metadata dicts with keys:
                cik, accession_number, filing_type, document_url
        
        Returns:
            List of FilingAnalysis results
        """
        logger.info(f"[SECForensicAnalyzer] Batch analyzing {len(filings)} filings")
        
        results = []
        for filing in filings:
            analysis = await self.analyze_filing(
                cik=filing.get('cik', ''),
                accession_number=filing.get('accession_number', ''),
                filing_type=filing.get('filing_type', 'UNKNOWN'),
                document_url=filing.get('document_url', ''),
                viewer_url=filing.get('viewer_url'),
                filing_date=filing.get('filing_date')
            )
            results.append(analysis)
        
        return results
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
        logger.info("[SECForensicAnalyzer] Cache cleared")
    
    async def close(self):
        """Close SEC client connection."""
        if self._sec_client is not None and hasattr(self._sec_client, 'close'):
            await self._sec_client.close()
