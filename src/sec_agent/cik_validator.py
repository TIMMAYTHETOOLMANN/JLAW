"""
CIK Validator — CIK Validation and Resolution
================================================

Validates and resolves SEC Central Index Key (CIK) identifiers using
JLAW's SECEdgarClient infrastructure. Supports CIK lookup by ticker
symbol, company name matching, and cross-validation against the EDGAR
full-text search and XBRL Company Facts data.

Source Integration:
    JLAW edgar_client.py (1,203 LOC) → SEC EDGAR API client
    JLAW zero_dollar/edgar_client.py (723 LOC) → zero-dollar detection client
    SEC-AGENT CIK0000320187.json → 2.8MB XBRL Company Facts reference
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.integrations.sec_edgar.edgar_client import SECEdgarClient
from src.integrations.sec_edgar.models import SECFiling

logger = logging.getLogger(__name__)

# Well-known CIK → Company mappings for fast lookup
KNOWN_CIK_MAPPINGS: Dict[str, str] = {
    "320187": "NIKE, Inc.",
    "0000320187": "NIKE, Inc.",
    "789019": "MICROSOFT CORP",
    "1318605": "TESLA, INC.",
    "1652044": "ALPHABET INC.",
    "1045810": "NVIDIA CORP",
    "320193": "APPLE INC.",
    "1018724": "AMAZON COM INC",
    "1326801": "META PLATFORMS, INC.",
    "1067983": "BERKSHIRE HATHAWAY INC",
}


@dataclass
class CIKValidationResult:
    """Result of CIK validation and resolution."""

    cik: str
    cik_padded: str  # Zero-padded to 10 digits (SEC format)
    is_valid: bool
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    sic_code: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    filing_count: int = 0
    latest_filing_date: Optional[str] = None
    validation_method: str = "unknown"
    validation_timestamp: Optional[datetime] = None
    xbrl_fact_count: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "cik": self.cik,
            "cik_padded": self.cik_padded,
            "is_valid": self.is_valid,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "sic_code": self.sic_code,
            "state_of_incorporation": self.state_of_incorporation,
            "fiscal_year_end": self.fiscal_year_end,
            "filing_count": self.filing_count,
            "latest_filing_date": self.latest_filing_date,
            "validation_method": self.validation_method,
            "validation_timestamp": (
                self.validation_timestamp.isoformat()
                if self.validation_timestamp
                else None
            ),
            "xbrl_fact_count": self.xbrl_fact_count,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class CIKLookupResult:
    """Result of a CIK lookup by ticker or company name."""

    query: str
    query_type: str  # "ticker" or "company_name"
    results: List[CIKValidationResult] = field(default_factory=list)
    match_count: int = 0
    best_match: Optional[CIKValidationResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query": self.query,
            "query_type": self.query_type,
            "match_count": self.match_count,
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "results": [r.to_dict() for r in self.results],
        }


class CIKValidator:
    """
    Validate and resolve SEC Central Index Key (CIK) identifiers.

    Uses JLAW's SECEdgarClient for EDGAR API access and supports
    offline validation against XBRL Company Facts JSON.

    Args:
        user_agent: SEC EDGAR user agent string (required by SEC).
        xbrl_index_path: Path to CIK XBRL Company Facts JSON.
        offline_mode: If True, skip EDGAR API calls and use local data only.
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        xbrl_index_path: Optional[Path] = None,
        offline_mode: bool = False,
    ) -> None:
        self.user_agent = user_agent
        self.xbrl_index_path = xbrl_index_path
        self.offline_mode = offline_mode
        self.xbrl_data: Optional[Dict[str, Any]] = None
        self._ticker_cik_cache: Dict[str, str] = {}

        if xbrl_index_path and xbrl_index_path.exists():
            self._load_xbrl_data()

    def _load_xbrl_data(self) -> None:
        """Load XBRL Company Facts data for offline validation."""
        if not self.xbrl_index_path:
            return
        try:
            with open(self.xbrl_index_path, "r", encoding="utf-8") as f:
                self.xbrl_data = json.load(f)
            logger.info(
                "Loaded XBRL data from %s", self.xbrl_index_path
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load XBRL data: %s", e)

    @staticmethod
    def normalize_cik(cik: str) -> str:
        """
        Normalize CIK to standard format.

        Strips leading zeros and non-numeric characters.

        Args:
            cik: Raw CIK string.

        Returns:
            Normalized CIK string (no leading zeros).
        """
        cleaned = re.sub(r"[^0-9]", "", str(cik))
        return cleaned.lstrip("0") or "0"

    @staticmethod
    def pad_cik(cik: str, width: int = 10) -> str:
        """
        Zero-pad CIK to SEC standard width (10 digits).

        Args:
            cik: CIK string.
            width: Target width (default 10).

        Returns:
            Zero-padded CIK string.
        """
        cleaned = re.sub(r"[^0-9]", "", str(cik))
        return cleaned.zfill(width)

    def validate_format(self, cik: str) -> CIKValidationResult:
        """
        Validate CIK format (numeric, 1-10 digits).

        Args:
            cik: CIK string to validate.

        Returns:
            CIKValidationResult with format validation status.
        """
        normalized = self.normalize_cik(cik)
        padded = self.pad_cik(cik)

        result = CIKValidationResult(
            cik=normalized,
            cik_padded=padded,
            is_valid=False,
            validation_method="format",
            validation_timestamp=datetime.utcnow(),
        )

        # Basic format checks
        if not normalized:
            result.errors.append("CIK is empty after normalization")
            return result

        if not normalized.isdigit():
            result.errors.append("CIK contains non-numeric characters")
            return result

        if len(normalized) > 10:
            result.errors.append("CIK exceeds maximum length of 10 digits")
            return result

        # Check known mappings
        if normalized in KNOWN_CIK_MAPPINGS:
            result.is_valid = True
            result.company_name = KNOWN_CIK_MAPPINGS[normalized]
            result.validation_method = "known_mapping"
        elif padded in KNOWN_CIK_MAPPINGS:
            result.is_valid = True
            result.company_name = KNOWN_CIK_MAPPINGS[padded]
            result.validation_method = "known_mapping"
        else:
            # Format is valid but existence not confirmed
            result.is_valid = True
            result.validation_method = "format_only"

        return result

    def validate_offline(self, cik: str) -> CIKValidationResult:
        """
        Validate CIK against local XBRL Company Facts data.

        Args:
            cik: CIK string to validate.

        Returns:
            CIKValidationResult with XBRL validation data.
        """
        result = self.validate_format(cik)

        if not self.xbrl_data:
            result.errors.append("No XBRL data loaded for offline validation")
            return result

        # Extract entity information from XBRL data
        entity_name = self.xbrl_data.get("entityName", "")
        cik_from_xbrl = str(self.xbrl_data.get("cik", ""))

        if self.normalize_cik(cik_from_xbrl) == result.cik:
            result.is_valid = True
            result.company_name = entity_name
            result.validation_method = "xbrl_index"

            # Count XBRL facts
            facts = self.xbrl_data.get("facts", {})
            fact_count = 0
            for taxonomy in facts.values():
                for concept in taxonomy.values():
                    units = concept.get("units", {})
                    for unit_entries in units.values():
                        fact_count += len(unit_entries)
            result.xbrl_fact_count = fact_count

        return result

    async def validate_online(self, cik: str) -> CIKValidationResult:
        """
        Validate CIK against live SEC EDGAR API.

        Makes API call to retrieve company submissions and confirms
        CIK existence, company name, filing history, and metadata.

        Args:
            cik: CIK string to validate.

        Returns:
            CIKValidationResult with full EDGAR validation data.
        """
        result = self.validate_format(cik)

        if self.offline_mode:
            result.errors.append("Online validation skipped (offline mode)")
            return result

        if not self.user_agent:
            result.errors.append("No user agent configured for SEC EDGAR API")
            return result

        try:
            async with SECEdgarClient(
                user_agent=self.user_agent
            ) as client:
                submissions = await client.get_company_submissions(result.cik_padded)
                if submissions:
                    result.is_valid = True
                    result.company_name = submissions.get("name", "")
                    result.ticker = (
                        submissions.get("tickers", [""])[0]
                        if submissions.get("tickers")
                        else None
                    )
                    result.sic_code = submissions.get("sic", "")
                    result.state_of_incorporation = submissions.get(
                        "stateOfIncorporation", ""
                    )
                    result.fiscal_year_end = submissions.get("fiscalYearEnd", "")
                    result.validation_method = "edgar_api"

                    # Count filings
                    recent_filings = submissions.get("filings", {}).get(
                        "recent", {}
                    )
                    if recent_filings:
                        forms = recent_filings.get("form", [])
                        result.filing_count = len(forms)
                        dates = recent_filings.get("filingDate", [])
                        if dates:
                            result.latest_filing_date = dates[0]

                    result.metadata["exchanges"] = submissions.get(
                        "exchanges", []
                    )
                    result.metadata["ein"] = submissions.get("ein", "")
                else:
                    result.is_valid = False
                    result.errors.append(
                        f"CIK {result.cik_padded} not found in EDGAR submissions"
                    )

        except Exception as e:
            logger.error("EDGAR API validation failed for CIK %s: %s", cik, e)
            result.errors.append(f"EDGAR API error: {e}")

        return result

    async def lookup_by_ticker(self, ticker: str) -> CIKLookupResult:
        """
        Look up CIK by ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., "NKE", "AAPL").

        Returns:
            CIKLookupResult with matching CIK(s).
        """
        lookup = CIKLookupResult(query=ticker.upper(), query_type="ticker")

        # Check cache first
        if ticker.upper() in self._ticker_cik_cache:
            cached_cik = self._ticker_cik_cache[ticker.upper()]
            result = await self.validate_online(cached_cik)
            result.ticker = ticker.upper()
            lookup.results.append(result)
            lookup.match_count = 1
            lookup.best_match = result
            return lookup

        if self.offline_mode or not self.user_agent:
            lookup.results = []
            return lookup

        try:
            async with SECEdgarClient(
                user_agent=self.user_agent
            ) as client:
                cik = await client.cik_from_ticker(ticker.upper())
                if cik:
                    self._ticker_cik_cache[ticker.upper()] = cik
                    result = await self.validate_online(cik)
                    result.ticker = ticker.upper()
                    lookup.results.append(result)
                    lookup.match_count = 1
                    lookup.best_match = result

        except Exception as e:
            logger.error("Ticker lookup failed for %s: %s", ticker, e)

        return lookup

    async def validate(self, cik: str) -> CIKValidationResult:
        """
        Comprehensive CIK validation using all available methods.

        Tries XBRL offline validation first, then EDGAR API if available.

        Args:
            cik: CIK string to validate.

        Returns:
            CIKValidationResult with best available validation data.
        """
        # Try offline first (fast, no API calls)
        result = self.validate_offline(cik)
        if result.is_valid and result.validation_method == "xbrl_index":
            return result

        # Try online validation
        if not self.offline_mode:
            online_result = await self.validate_online(cik)
            if online_result.is_valid:
                # Merge XBRL fact count if available
                if result.xbrl_fact_count > 0:
                    online_result.xbrl_fact_count = result.xbrl_fact_count
                return online_result

        return result

    def validate_batch(
        self,
        ciks: List[str],
    ) -> Dict[str, CIKValidationResult]:
        """
        Validate multiple CIKs using format and offline checks.

        For online validation of batches, use validate() in an async loop.

        Args:
            ciks: List of CIK strings.

        Returns:
            Dictionary mapping CIK to validation result.
        """
        results: Dict[str, CIKValidationResult] = {}
        for cik in ciks:
            normalized = self.normalize_cik(cik)
            if self.xbrl_data:
                results[normalized] = self.validate_offline(cik)
            else:
                results[normalized] = self.validate_format(cik)
        return results

    def export_validation_report(
        self,
        results: Dict[str, CIKValidationResult],
        output_path: Path,
    ) -> Path:
        """
        Export validation results to JSON.

        Args:
            results: Dictionary of validation results.
            output_path: Output JSON file path.

        Returns:
            Path to exported file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "validation_report": {
                "total_ciks": len(results),
                "valid_count": sum(1 for r in results.values() if r.is_valid),
                "invalid_count": sum(1 for r in results.values() if not r.is_valid),
                "generated_at": datetime.utcnow().isoformat(),
            },
            "results": {cik: r.to_dict() for cik, r in results.items()},
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Exported CIK validation report to %s", output_path)
        return output_path
