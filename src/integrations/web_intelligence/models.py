"""
Data models for Web Intelligence Engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class StatementSource(str, Enum):
    """Source category of a public statement."""
    EARNINGS_CALL = "earnings_call"
    PRESS_RELEASE = "press_release"
    NEWS_ARTICLE = "news_article"
    SEC_FILING = "sec_filing"
    SOCIAL_MEDIA = "social_media"
    ANALYST_REPORT = "analyst_report"
    CONFERENCE = "conference"
    INTERVIEW = "interview"
    SEC_COMMENT_LETTER = "sec_comment_letter"


@dataclass
class PublicStatement:
    """A public claim, promise, or financial statement made by the company or its officers."""
    text: str
    source_type: StatementSource
    source_url: str = ""
    source_title: str = ""
    speaker: str = ""
    date: Optional[datetime] = None
    context: str = ""
    financial_figures: List[Dict[str, Any]] = field(default_factory=list)
    is_quantitative: bool = False
    raw_excerpt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "speaker": self.speaker,
            "date": self.date.isoformat() if self.date else None,
            "context": self.context,
            "financial_figures": self.financial_figures,
            "is_quantitative": self.is_quantitative,
            "raw_excerpt": self.raw_excerpt,
        }


@dataclass
class ContradictionEntry:
    """A single detected contradiction between a public statement and an internal finding."""
    public_statement: PublicStatement
    sec_finding: Dict[str, Any]
    contradiction_type: str  # e.g. "revenue_mismatch", "profit_inflation", "timeline_conflict"
    severity: str  # CRITICAL / HIGH / MEDIUM / LOW
    confidence: float  # 0.0 - 1.0
    explanation: str  # Human-readable description of the contradiction
    dollar_discrepancy: Optional[float] = None  # Dollar magnitude of the discrepancy
    percentage_discrepancy: Optional[float] = None
    legal_implications: str = ""
    applicable_statutes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "public_statement": self.public_statement.to_dict(),
            "sec_finding": self.sec_finding,
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
            "explanation": self.explanation,
            "dollar_discrepancy": self.dollar_discrepancy,
            "percentage_discrepancy": self.percentage_discrepancy,
            "legal_implications": self.legal_implications,
            "applicable_statutes": self.applicable_statutes,
        }


@dataclass
class ContradictionMap:
    """Complete contradiction mapping between public statements and SEC findings."""
    company_name: str
    cik: str
    analysis_period: str
    total_statements_collected: int = 0
    total_contradictions_found: int = 0
    critical_contradictions: int = 0
    high_contradictions: int = 0
    contradictions: List[ContradictionEntry] = field(default_factory=list)
    all_statements: List[PublicStatement] = field(default_factory=list)
    source_breakdown: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": self.analysis_period,
            "total_statements_collected": self.total_statements_collected,
            "total_contradictions_found": self.total_contradictions_found,
            "critical_contradictions": self.critical_contradictions,
            "high_contradictions": self.high_contradictions,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "source_breakdown": self.source_breakdown,
        }


@dataclass
class WebIntelligenceResult:
    """Complete result from the web intelligence engine."""
    company_name: str
    cik: str
    statements: List[PublicStatement] = field(default_factory=list)
    contradiction_map: Optional[ContradictionMap] = None
    sources_scraped: int = 0
    scrape_errors: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "cik": self.cik,
            "statements_collected": len(self.statements),
            "contradiction_map": self.contradiction_map.to_dict() if self.contradiction_map else None,
            "sources_scraped": self.sources_scraped,
            "scrape_errors": self.scrape_errors,
            "execution_time_seconds": round(self.execution_time_seconds, 2),
        }
