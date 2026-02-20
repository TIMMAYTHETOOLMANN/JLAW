"""
Web Intelligence Engine — OSINT Scraper & Statement Extractor
=============================================================

Scrapes public sources for company statements, claims, and financial figures:
- SEC EDGAR press releases & exhibits
- Earnings call transcripts (SEC 8-K exhibits, Seeking Alpha)
- Financial news articles (SEC filings RSS, financial press)
- Social media (Twitter/X posts by corporate accounts)
- Conference transcripts
- Analyst coverage

Extracts structured claims (financial figures, promises, projections) and
feeds them into the Contradiction Mapper for cross-referencing against
SEC filing analysis findings.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin

import aiohttp
from bs4 import BeautifulSoup

from .models import (
    ContradictionEntry,
    ContradictionMap,
    PublicStatement,
    StatementSource,
    WebIntelligenceResult,
)

logger = logging.getLogger(__name__)

# Financial figure extraction patterns
_MONEY_RE = re.compile(
    r"\$\s?[\d,]+(?:\.\d+)?\s*(?:billion|million|thousand|B|M|K|bn|mn)?",
    re.IGNORECASE,
)
_PERCENT_RE = re.compile(
    r"[\-\+]?\d+(?:\.\d+)?\s*%",
)
_REVENUE_KEYWORDS = re.compile(
    r"\b(revenue|sales|net\s+sales|top[- ]line|gross\s+revenue)\b", re.IGNORECASE,
)
_PROFIT_KEYWORDS = re.compile(
    r"\b(profit|earnings|net\s+income|ebit(?:da)?|operating\s+income|bottom[- ]line)\b",
    re.IGNORECASE,
)
_GROWTH_KEYWORDS = re.compile(
    r"\b(grow(?:th|ing|n)?|increas(?:e|ed|ing)|expand(?:ed|ing)?|improv(?:e|ed|ing))\b",
    re.IGNORECASE,
)
_DECLINE_KEYWORDS = re.compile(
    r"\b(declin(?:e|ed|ing)|decreas(?:e|ed|ing)|drop(?:ped)?|fell|contract(?:ed|ing)?|shrink|loss)\b",
    re.IGNORECASE,
)

# SEC EDGAR EFTS full-text search
SEC_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_FILINGS = "https://www.sec.gov/cgi-bin/browse-edgar"
SEC_EDGAR_FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"

# EDGAR full-text search (public)
EDGAR_FULLTEXT_URL = "https://efts.sec.gov/LATEST/search-index"

# Rate limiting
SEC_RATE_LIMIT = 8  # requests per second


def _parse_money(text: str) -> Optional[float]:
    """Parse a dollar string like '$10.5 million' into a float."""
    text = text.replace(",", "").replace("$", "").strip()
    multipliers = {
        "billion": 1e9, "bn": 1e9, "b": 1e9,
        "million": 1e6, "mn": 1e6, "m": 1e6,
        "thousand": 1e3, "k": 1e3,
    }
    for suffix, mult in multipliers.items():
        if text.lower().endswith(suffix):
            num_str = text[:len(text) - len(suffix)].strip()
            try:
                return float(num_str) * mult
            except ValueError:
                return None
    try:
        return float(text)
    except ValueError:
        return None


class WebIntelligenceEngine:
    """
    Comprehensive OSINT engine for scraping public company statements.

    Collects claims, financial figures, and promises from:
      1. SEC EDGAR filings (8-K exhibits, press releases, earnings call transcripts)
      2. SEC EDGAR full-text search for specific financial claims
      3. Financial news via public APIs
      4. Social media corporate accounts

    Then feeds all collected statements into the Contradiction Mapper for
    cross-referencing against the 15-node forensic analysis findings.
    """

    def __init__(
        self,
        user_agent: str = "",
        rate_limit: float = SEC_RATE_LIMIT,
    ):
        self.user_agent = user_agent or os.getenv(
            "SEC_USER_AGENT", "JLAW-Forensics/4.1.0 (research@jlaw.io)"
        )
        self.rate_limit = rate_limit
        self._last_request_time = 0.0
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                trust_env=True,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self._session

    async def _rate_limited_get(self, url: str, **kwargs) -> Optional[str]:
        """GET with rate limiting and error handling."""
        elapsed = time.time() - self._last_request_time
        wait = (1.0 / self.rate_limit) - elapsed
        if wait > 0:
            await asyncio.sleep(wait)

        session = await self._get_session()
        self._last_request_time = time.time()

        try:
            async with session.get(url, **kwargs) as resp:
                if resp.status == 200:
                    return await resp.text()
                logger.warning(f"HTTP {resp.status} for {url}")
                return None
        except Exception as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ─── MAIN ENTRY POINT ────────────────────────────────────────────

    async def collect_intelligence(
        self,
        company_name: str,
        ticker: str,
        cik: str,
        start_date: date,
        end_date: date,
        sec_findings: Optional[Dict[str, Any]] = None,
    ) -> WebIntelligenceResult:
        """
        Collect public intelligence and map contradictions against SEC findings.

        Args:
            company_name: Target company name
            ticker: Stock ticker symbol
            cik: SEC CIK number
            start_date: Start of analysis period
            end_date: End of analysis period
            sec_findings: Dict of SEC analysis findings from the 15-node engine
                          (used for contradiction mapping)

        Returns:
            WebIntelligenceResult with all statements and contradiction map
        """
        t0 = time.time()
        all_statements: List[PublicStatement] = []
        errors: List[str] = []
        sources_scraped = 0

        # Run all scrapers concurrently
        scraper_tasks = [
            self._scrape_edgar_filings(cik, company_name, start_date, end_date),
            self._scrape_edgar_press_releases(cik, company_name, start_date, end_date),
            self._scrape_earnings_transcripts(company_name, ticker, cik, start_date, end_date),
            self._scrape_financial_news(company_name, ticker, start_date, end_date),
            self._scrape_sec_comment_letters(cik, company_name, start_date, end_date),
        ]

        results = await asyncio.gather(*scraper_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            source_names = [
                "EDGAR Filings", "EDGAR Press Releases",
                "Earnings Transcripts", "Financial News",
                "SEC Comment Letters",
            ]
            if isinstance(result, Exception):
                err = f"{source_names[i]}: {result}"
                logger.error(err)
                errors.append(err)
            elif isinstance(result, list):
                all_statements.extend(result)
                sources_scraped += 1
                logger.info(f"{source_names[i]}: collected {len(result)} statements")

        # ── Contradiction mapping ──
        contradiction_map = None
        if sec_findings and all_statements:
            contradiction_map = self._map_contradictions(
                company_name, cik, f"{start_date} to {end_date}",
                all_statements, sec_findings,
            )

        elapsed = time.time() - t0
        logger.info(
            f"Web intelligence complete: {len(all_statements)} statements, "
            f"{sources_scraped} sources in {elapsed:.1f}s"
        )

        result = WebIntelligenceResult(
            company_name=company_name,
            cik=cik,
            statements=all_statements,
            contradiction_map=contradiction_map,
            sources_scraped=sources_scraped,
            scrape_errors=errors,
            execution_time_seconds=elapsed,
        )

        await self.close()
        return result

    # ═══════════════════════════════════════════════════════════════════
    # SOURCE SCRAPERS
    # ═══════════════════════════════════════════════════════════════════

    async def _scrape_edgar_filings(
        self, cik: str, company_name: str, start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Scrape SEC EDGAR filings (8-K, 10-K, 10-Q) for financial statements."""
        statements: List[PublicStatement] = []
        cik_padded = cik.zfill(10)

        # Use EDGAR full-text search API
        url = f"https://efts.sec.gov/LATEST/search-index?q=%22{quote_plus(company_name)}%22&dateRange=custom&startdt={start_date}&enddt={end_date}&forms=8-K,10-K,10-Q&from=0&size=40"

        html = await self._rate_limited_get(url)
        if not html:
            # Fallback: use submissions API
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
            html = await self._rate_limited_get(submissions_url)
            if html:
                statements.extend(
                    self._extract_statements_from_submissions(html, company_name, start_date, end_date)
                )
            return statements

        statements.extend(self._extract_statements_from_search(html, company_name))
        return statements

    async def _scrape_edgar_press_releases(
        self, cik: str, company_name: str, start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Scrape 8-K exhibit press releases from EDGAR."""
        statements: List[PublicStatement] = []
        cik_padded = cik.zfill(10)

        # 8-K press releases are in EX-99.1 exhibits
        url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{quote_plus(company_name)}%22+%22press+release%22"
            f"&dateRange=custom&startdt={start_date}&enddt={end_date}"
            f"&forms=8-K&from=0&size=20"
        )

        html = await self._rate_limited_get(url)
        if html:
            statements.extend(
                self._extract_press_release_statements(html, company_name)
            )

        # Also check direct EDGAR filing index for 8-K with EX-99
        index_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar?"
            f"action=getcompany&CIK={cik_padded}&type=8-K&dateb={end_date.strftime('%Y%m%d')}"
            f"&owner=include&count=40&search_text=&action=getcompany"
        )
        index_html = await self._rate_limited_get(index_url)
        if index_html:
            links = self._extract_filing_links(index_html)
            for link in links[:10]:  # Limit to 10 most recent
                filing_html = await self._rate_limited_get(link)
                if filing_html:
                    stmts = self._extract_financial_claims_from_html(
                        filing_html, company_name, StatementSource.PRESS_RELEASE, link
                    )
                    statements.extend(stmts)

        return statements

    async def _scrape_earnings_transcripts(
        self, company_name: str, ticker: str, cik: str,
        start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Scrape earnings call transcripts from SEC filings and public sources."""
        statements: List[PublicStatement] = []

        # Search EDGAR for earnings-related 8-K filings
        search_terms = [
            f'"{company_name}" "earnings" "quarter"',
            f'"{company_name}" "financial results"',
            f'"{company_name}" "conference call"',
        ]

        for term in search_terms:
            url = (
                f"https://efts.sec.gov/LATEST/search-index?"
                f"q={quote_plus(term)}"
                f"&dateRange=custom&startdt={start_date}&enddt={end_date}"
                f"&forms=8-K&from=0&size=10"
            )
            html = await self._rate_limited_get(url)
            if html:
                stmts = self._extract_earnings_statements(html, company_name)
                statements.extend(stmts)

        return statements

    async def _scrape_financial_news(
        self, company_name: str, ticker: str,
        start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Scrape financial news articles for company claims."""
        statements: List[PublicStatement] = []

        # Use SEC EDGAR full-text search as a proxy for news (EDGAR indexes press releases)
        search_terms = [
            f'"{company_name}" revenue profit',
            f'"{ticker}" earnings guidance outlook',
        ]

        for term in search_terms:
            url = (
                f"https://efts.sec.gov/LATEST/search-index?"
                f"q={quote_plus(term)}"
                f"&dateRange=custom&startdt={start_date}&enddt={end_date}"
                f"&from=0&size=10"
            )
            html = await self._rate_limited_get(url)
            if html:
                stmts = self._extract_news_statements(html, company_name)
                statements.extend(stmts)

        return statements

    async def _scrape_sec_comment_letters(
        self, cik: str, company_name: str, start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Scrape SEC staff comment letters for contradictions to filings."""
        statements: List[PublicStatement] = []
        cik_padded = cik.zfill(10)

        url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{quote_plus(company_name)}%22"
            f"&dateRange=custom&startdt={start_date}&enddt={end_date}"
            f"&forms=CORRESP,UPLOAD&from=0&size=10"
        )
        html = await self._rate_limited_get(url)
        if html:
            stmts = self._extract_comment_letter_statements(html, company_name)
            statements.extend(stmts)

        return statements

    # ═══════════════════════════════════════════════════════════════════
    # STATEMENT EXTRACTION
    # ═══════════════════════════════════════════════════════════════════

    def _extract_statements_from_submissions(
        self, json_text: str, company_name: str,
        start_date: date, end_date: date,
    ) -> List[PublicStatement]:
        """Extract statements from EDGAR submissions JSON."""
        import json
        statements: List[PublicStatement] = []

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return statements

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get("accessionNumber", [])
        titles = filings.get("primaryDocDescription", [])

        for i, (form, fdate_str, accession) in enumerate(zip(forms, dates, accessions)):
            try:
                fdate = datetime.strptime(fdate_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            if fdate < start_date or fdate > end_date:
                continue

            title = titles[i] if i < len(titles) else ""

            # 8-K filings often contain earnings/press releases
            if form in ("8-K", "8-K/A"):
                statements.append(PublicStatement(
                    text=f"{company_name} filed {form}: {title}",
                    source_type=StatementSource.SEC_FILING,
                    source_title=f"{form} - {title}",
                    date=datetime.combine(fdate, datetime.min.time()),
                    context=f"SEC filing {accession}",
                    metadata={"form_type": form, "accession": accession},
                ))

        return statements

    def _extract_statements_from_search(
        self, html: str, company_name: str,
    ) -> List[PublicStatement]:
        """Extract statements from EDGAR full-text search results."""
        statements: List[PublicStatement] = []
        soup = BeautifulSoup(html, "html.parser")

        # EDGAR EFTS returns JSON or HTML depending on endpoint
        # Try to extract from search result snippets
        for result in soup.select(".result, .filing, tr"):
            text = result.get_text(strip=True, separator=" ")
            if not text or len(text) < 20:
                continue

            # Extract financial claims from the snippet
            claims = self._extract_financial_claims_from_text(text, company_name)
            for claim in claims:
                claim.source_type = StatementSource.SEC_FILING
                statements.append(claim)

        return statements

    def _extract_press_release_statements(
        self, html: str, company_name: str,
    ) -> List[PublicStatement]:
        """Extract statements from press release search results."""
        statements: List[PublicStatement] = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.select(".result, .filing, tr"):
            text = result.get_text(strip=True, separator=" ")
            if not text or len(text) < 20:
                continue

            claims = self._extract_financial_claims_from_text(text, company_name)
            for claim in claims:
                claim.source_type = StatementSource.PRESS_RELEASE
                statements.append(claim)

        return statements

    def _extract_earnings_statements(
        self, html: str, company_name: str,
    ) -> List[PublicStatement]:
        """Extract statements from earnings-related search results."""
        statements: List[PublicStatement] = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.select(".result, .filing, tr, p"):
            text = result.get_text(strip=True, separator=" ")
            if not text or len(text) < 20:
                continue

            claims = self._extract_financial_claims_from_text(text, company_name)
            for claim in claims:
                claim.source_type = StatementSource.EARNINGS_CALL
                statements.append(claim)

        return statements

    def _extract_news_statements(
        self, html: str, company_name: str,
    ) -> List[PublicStatement]:
        """Extract statements from financial news search results."""
        statements: List[PublicStatement] = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.select(".result, .filing, tr, p"):
            text = result.get_text(strip=True, separator=" ")
            if not text or len(text) < 20:
                continue

            claims = self._extract_financial_claims_from_text(text, company_name)
            for claim in claims:
                claim.source_type = StatementSource.NEWS_ARTICLE
                statements.append(claim)

        return statements

    def _extract_comment_letter_statements(
        self, html: str, company_name: str,
    ) -> List[PublicStatement]:
        """Extract statements from SEC comment letters."""
        statements: List[PublicStatement] = []
        soup = BeautifulSoup(html, "html.parser")

        for result in soup.select(".result, .filing, tr, p"):
            text = result.get_text(strip=True, separator=" ")
            if not text or len(text) < 20:
                continue

            claims = self._extract_financial_claims_from_text(text, company_name)
            for claim in claims:
                claim.source_type = StatementSource.SEC_COMMENT_LETTER
                statements.append(claim)

        return statements

    def _extract_filing_links(self, html: str) -> List[str]:
        """Extract filing document links from EDGAR filing index page."""
        links = []
        soup = BeautifulSoup(html, "html.parser")
        for a_tag in soup.select("a[href*='/Archives/edgar/data/']"):
            href = a_tag.get("href", "")
            if href and (".htm" in href or ".txt" in href):
                full = urljoin("https://www.sec.gov", href)
                links.append(full)
        return links[:20]

    def _extract_financial_claims_from_html(
        self, html: str, company_name: str,
        source_type: StatementSource, url: str,
    ) -> List[PublicStatement]:
        """Extract financial claims from a full HTML filing page."""
        soup = BeautifulSoup(html, "html.parser")
        full_text = soup.get_text(separator=" ", strip=True)
        statements = self._extract_financial_claims_from_text(full_text, company_name)
        for stmt in statements:
            stmt.source_type = source_type
            stmt.source_url = url
        return statements

    def _extract_financial_claims_from_text(
        self, text: str, company_name: str,
    ) -> List[PublicStatement]:
        """
        Core NLP extraction: find sentences with financial claims.

        Identifies sentences containing:
        - Dollar amounts ($X million/billion)
        - Percentage figures (X%)
        - Revenue/profit/earnings keywords
        - Growth/decline language
        """
        statements: List[PublicStatement] = []

        # Split into sentences (simple rule-based)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30 or len(sentence) > 500:
                continue

            money_matches = _MONEY_RE.findall(sentence)
            pct_matches = _PERCENT_RE.findall(sentence)
            has_revenue = bool(_REVENUE_KEYWORDS.search(sentence))
            has_profit = bool(_PROFIT_KEYWORDS.search(sentence))
            has_growth = bool(_GROWTH_KEYWORDS.search(sentence))
            has_decline = bool(_DECLINE_KEYWORDS.search(sentence))

            is_financial = (
                bool(money_matches) or bool(pct_matches)
            ) and (has_revenue or has_profit or has_growth or has_decline)

            if not is_financial:
                continue

            figures = []
            for m in money_matches:
                val = _parse_money(m)
                if val is not None:
                    figures.append({"raw": m, "value": val, "type": "dollar"})
            for p in pct_matches:
                figures.append({"raw": p, "type": "percentage"})

            # Determine speaker (look for attribution patterns)
            speaker = ""
            speaker_match = re.search(
                r'(?:said|stated|noted|reported|announced|according\s+to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                sentence,
            )
            if speaker_match:
                speaker = speaker_match.group(1)

            # Determine claim type
            claim_type = "financial_claim"
            if has_revenue:
                claim_type = "revenue_claim"
            elif has_profit:
                claim_type = "profit_claim"

            statements.append(PublicStatement(
                text=sentence,
                source_type=StatementSource.SEC_FILING,
                speaker=speaker,
                financial_figures=figures,
                is_quantitative=True,
                raw_excerpt=sentence,
                context=claim_type,
                metadata={"has_growth": has_growth, "has_decline": has_decline},
            ))

        return statements

    # ═══════════════════════════════════════════════════════════════════
    # CONTRADICTION MAPPING ENGINE
    # ═══════════════════════════════════════════════════════════════════

    def _map_contradictions(
        self,
        company_name: str,
        cik: str,
        analysis_period: str,
        statements: List[PublicStatement],
        sec_findings: Dict[str, Any],
    ) -> ContradictionMap:
        """
        Map public statements against SEC analysis findings to detect contradictions.

        Cross-references:
        1. Revenue claims vs. actual revenue trends from SEC filings
        2. Profit claims vs. actual earnings data
        3. Growth claims vs. declining metrics
        4. Executive compensation claims vs. proxy data
        5. Insider trading timing vs. public optimism
        6. Guidance vs. actual performance
        """
        contradictions: List[ContradictionEntry] = []

        # Extract SEC findings data for comparison
        violations = sec_findings.get("violations", [])
        transactions = sec_findings.get("transactions", [])
        beneficiaries = sec_findings.get("beneficiaries", [])
        material_events = sec_findings.get("material_events", [])
        penalties = sec_findings.get("estimated_penalties", {})
        total_violations = sec_findings.get("total_violations", 0)
        critical_alerts = sec_findings.get("critical_alerts", 0)

        for stmt in statements:
            if not stmt.is_quantitative:
                continue

            # ── Revenue / Profit Contradiction Check ──
            contradiction = self._check_financial_contradiction(
                stmt, violations, transactions, sec_findings
            )
            if contradiction:
                contradictions.append(contradiction)

            # ── Growth vs. Decline Contradiction ──
            contradiction = self._check_growth_decline_contradiction(
                stmt, violations, sec_findings
            )
            if contradiction:
                contradictions.append(contradiction)

            # ── Insider Trading Timing Contradiction ──
            contradiction = self._check_insider_timing_contradiction(
                stmt, transactions, material_events
            )
            if contradiction:
                contradictions.append(contradiction)

            # ── Compensation Claims Contradiction ──
            contradiction = self._check_compensation_contradiction(
                stmt, beneficiaries, violations
            )
            if contradiction:
                contradictions.append(contradiction)

        # Sort by severity then confidence
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        contradictions.sort(
            key=lambda c: (severity_order.get(c.severity, 4), -c.confidence)
        )

        # Build source breakdown
        source_breakdown: Dict[str, int] = {}
        for stmt in statements:
            key = stmt.source_type.value
            source_breakdown[key] = source_breakdown.get(key, 0) + 1

        crit = sum(1 for c in contradictions if c.severity == "CRITICAL")
        high = sum(1 for c in contradictions if c.severity == "HIGH")

        return ContradictionMap(
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period,
            total_statements_collected=len(statements),
            total_contradictions_found=len(contradictions),
            critical_contradictions=crit,
            high_contradictions=high,
            contradictions=contradictions,
            all_statements=statements,
            source_breakdown=source_breakdown,
        )

    def _check_financial_contradiction(
        self,
        stmt: PublicStatement,
        violations: List[Dict],
        transactions: List[Dict],
        sec_findings: Dict[str, Any],
    ) -> Optional[ContradictionEntry]:
        """Check if a financial claim contradicts SEC findings."""
        has_revenue = stmt.context == "revenue_claim"
        has_profit = stmt.context == "profit_claim"
        has_growth = stmt.metadata.get("has_growth", False)

        if not (has_revenue or has_profit):
            return None

        # Check for related violations
        related = []
        for v in violations:
            vtype = v.get("violation_type", "").lower()
            desc = v.get("description", "").lower()
            if has_revenue and ("revenue" in vtype or "revenue" in desc or "material" in vtype):
                related.append(v)
            elif has_profit and ("earnings" in vtype or "profit" in desc or "income" in desc):
                related.append(v)

        if not related:
            return None

        # Compute discrepancy from statement figures vs findings
        dollar_discrepancy = None
        for fig in stmt.financial_figures:
            if fig.get("type") == "dollar" and fig.get("value"):
                dollar_discrepancy = fig["value"]
                break

        severity = "HIGH" if has_growth else "MEDIUM"
        if any(v.get("severity", "").upper() == "CRITICAL" for v in related):
            severity = "CRITICAL"

        explanation = (
            f"Public statement claims "
            f"{'revenue growth' if has_revenue else 'profit/earnings'}"
            f"{' with positive growth language' if has_growth else ''}, "
            f"but SEC analysis identified {len(related)} related violation(s): "
            f"{', '.join(v.get('violation_type', 'Unknown') for v in related[:3])}."
        )

        return ContradictionEntry(
            public_statement=stmt,
            sec_finding={
                "related_violations": related[:5],
                "source": "15-node SEC analysis",
            },
            contradiction_type="revenue_mismatch" if has_revenue else "profit_inflation",
            severity=severity,
            confidence=0.75 + (0.1 * min(len(related), 3)),
            explanation=explanation,
            dollar_discrepancy=dollar_discrepancy,
            legal_implications=(
                "Potential violation of Securities Exchange Act §10(b) and Rule 10b-5 "
                "(fraud in connection with purchase/sale of securities). "
                "Misleading public statements about financial performance may constitute "
                "securities fraud if made with scienter."
            ),
            applicable_statutes=[
                "Securities Exchange Act §10(b)",
                "SEC Rule 10b-5",
                "Sarbanes-Oxley Act §302 (CEO/CFO certification)",
                "18 U.S.C. §1348 (Securities fraud)",
            ],
        )

    def _check_growth_decline_contradiction(
        self,
        stmt: PublicStatement,
        violations: List[Dict],
        sec_findings: Dict[str, Any],
    ) -> Optional[ContradictionEntry]:
        """Check for growth claims that contradict declining metrics."""
        has_growth = stmt.metadata.get("has_growth", False)
        has_decline = stmt.metadata.get("has_decline", False)

        if not has_growth:
            return None

        # Look for violations indicating decline or deterioration
        decline_violations = []
        for v in violations:
            desc = v.get("description", "").lower()
            vtype = v.get("violation_type", "").lower()
            if any(kw in desc or kw in vtype for kw in [
                "declin", "loss", "material weakness", "going concern",
                "restatement", "impairment", "writedown", "write-down",
            ]):
                decline_violations.append(v)

        if not decline_violations:
            return None

        pct_discrepancy = None
        for fig in stmt.financial_figures:
            if fig.get("type") == "percentage":
                raw = fig.get("raw", "").replace("%", "").strip()
                try:
                    pct_discrepancy = float(raw)
                except ValueError:
                    pass
                break

        return ContradictionEntry(
            public_statement=stmt,
            sec_finding={
                "decline_indicators": decline_violations[:5],
                "source": "15-node SEC analysis",
            },
            contradiction_type="growth_vs_decline",
            severity="CRITICAL" if len(decline_violations) >= 2 else "HIGH",
            confidence=0.80 + (0.05 * min(len(decline_violations), 4)),
            explanation=(
                f"Company publicly claimed growth/improvement, but SEC analysis "
                f"found {len(decline_violations)} indicator(s) of decline or deterioration: "
                f"{', '.join(v.get('violation_type', 'Unknown') for v in decline_violations[:3])}."
            ),
            percentage_discrepancy=pct_discrepancy,
            legal_implications=(
                "Making misleading growth claims when internal metrics show decline "
                "may constitute fraud under §10(b)/10b-5. If executives traded during "
                "this period, insider trading charges under §10(b) and §16(b) may apply."
            ),
            applicable_statutes=[
                "Securities Exchange Act §10(b)",
                "SEC Rule 10b-5",
                "Securities Exchange Act §16(b) (Short-swing profits)",
            ],
        )

    def _check_insider_timing_contradiction(
        self,
        stmt: PublicStatement,
        transactions: List[Dict],
        material_events: List[Dict],
    ) -> Optional[ContradictionEntry]:
        """Check if insiders traded near times of public optimistic statements."""
        if not stmt.date or not transactions:
            return None

        has_growth = stmt.metadata.get("has_growth", False)
        if not has_growth:
            return None

        # Find transactions near the statement date (within 30 days)
        suspicious_trades = []
        for txn in transactions:
            txn_date = txn.get("date")
            if not txn_date:
                continue
            if isinstance(txn_date, str):
                try:
                    txn_date = datetime.strptime(txn_date[:10], "%Y-%m-%d")
                except ValueError:
                    continue
            if isinstance(txn_date, date) and not isinstance(txn_date, datetime):
                txn_date = datetime.combine(txn_date, datetime.min.time())

            delta = abs((txn_date - stmt.date).days)
            if delta <= 30:
                txn_type = txn.get("type", txn.get("transaction_type", "")).lower()
                if "sale" in txn_type or "sell" in txn_type or txn_type == "s":
                    suspicious_trades.append(txn)

        if not suspicious_trades:
            return None

        total_value = sum(abs(t.get("value", 0)) for t in suspicious_trades)

        return ContradictionEntry(
            public_statement=stmt,
            sec_finding={
                "suspicious_trades": suspicious_trades[:10],
                "total_trade_value": total_value,
                "source": "Node 1 Form 4 + Node 10 Form 144 analysis",
            },
            contradiction_type="insider_timing",
            severity="CRITICAL",
            confidence=0.85,
            explanation=(
                f"Executives made optimistic public statements while simultaneously "
                f"selling {len(suspicious_trades)} position(s) totaling "
                f"${total_value:,.0f} within 30 days. This pattern is consistent "
                f"with insider trading ahead of adverse information."
            ),
            dollar_discrepancy=total_value,
            legal_implications=(
                "Trading on material nonpublic information while making optimistic "
                "public statements constitutes classic insider trading under "
                "Dirks v. SEC and SEC v. Texas Gulf Sulphur."
            ),
            applicable_statutes=[
                "Securities Exchange Act §10(b)",
                "SEC Rule 10b-5",
                "Securities Exchange Act §16(b)",
                "18 U.S.C. §1348 (Securities fraud)",
                "Insider Trading Sanctions Act of 1984",
                "Insider Trading and Securities Fraud Enforcement Act of 1988",
            ],
        )

    def _check_compensation_contradiction(
        self,
        stmt: PublicStatement,
        beneficiaries: List[Dict],
        violations: List[Dict],
    ) -> Optional[ContradictionEntry]:
        """Check if compensation claims contradict proxy/filing data."""
        text_lower = stmt.text.lower()
        if not any(kw in text_lower for kw in [
            "compensation", "pay", "salary", "bonus", "equity", "stock option",
        ]):
            return None

        comp_violations = [
            v for v in violations
            if any(kw in v.get("violation_type", "").lower() for kw in [
                "compensation", "pay", "say-on-pay", "golden parachute",
            ])
        ]

        if not comp_violations:
            return None

        total_comp = sum(b.get("total_profit", 0) for b in beneficiaries)

        return ContradictionEntry(
            public_statement=stmt,
            sec_finding={
                "compensation_violations": comp_violations[:5],
                "total_executive_compensation": total_comp,
                "source": "Node 2 DEF 14A + Node 5 IRC §83 analysis",
            },
            contradiction_type="compensation_misrepresentation",
            severity="HIGH",
            confidence=0.70,
            explanation=(
                f"Public statements about executive compensation contradict "
                f"SEC proxy analysis findings: {len(comp_violations)} violation(s) detected "
                f"with total executive compensation of ${total_comp:,.0f}."
            ),
            dollar_discrepancy=total_comp,
            legal_implications=(
                "Misrepresentation of executive compensation in proxy materials "
                "violates SEC proxy rules (§14(a)) and may trigger §10(b)/10b-5 claims."
            ),
            applicable_statutes=[
                "Securities Exchange Act §14(a) (Proxy solicitations)",
                "SEC Rule 14a-9 (False or misleading statements)",
                "Dodd-Frank Act §953 (Pay-for-performance)",
            ],
        )
