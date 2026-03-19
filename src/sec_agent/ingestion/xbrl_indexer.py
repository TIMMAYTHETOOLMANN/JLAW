"""
XBRL Indexer — CIK XBRL Company Facts Indexer
================================================

Indexes SEC XBRL Company Facts JSON data for cross-referencing with
the raw EDGAR filing corpus. Supports extraction of financial data
points, filing metadata, and US-GAAP concept mappings.

Designed for the SEC-AGENT data format:
    CIK0000320187.json → 2.8MB XBRL Company Facts with 417 US-GAAP items
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class XBRLFact:
    """Single XBRL fact data point."""

    taxonomy: str      # e.g., "us-gaap"
    concept: str       # e.g., "Revenue"
    value: Any         # Numeric or string value
    unit: str          # e.g., "USD", "shares"
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    instant: Optional[date] = None
    form_type: Optional[str] = None
    filing_date: Optional[date] = None
    accession_number: Optional[str] = None
    fiscal_year: Optional[int] = None
    fiscal_period: Optional[str] = None
    frame: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "taxonomy": self.taxonomy,
            "concept": self.concept,
            "value": self.value,
            "unit": self.unit,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "instant": self.instant.isoformat() if self.instant else None,
            "form_type": self.form_type,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "accession_number": self.accession_number,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
        }


@dataclass
class XBRLIndex:
    """Indexed XBRL Company Facts data."""

    cik: str
    entity_name: str
    source_file: str
    indexed_at: datetime
    total_facts: int = 0
    taxonomies: Set[str] = field(default_factory=set)
    concepts: Set[str] = field(default_factory=set)
    form_types: Set[str] = field(default_factory=set)
    fiscal_years: Set[int] = field(default_factory=set)
    accession_numbers: Set[str] = field(default_factory=set)
    facts: List[XBRLFact] = field(default_factory=list)
    facts_by_concept: Dict[str, List[XBRLFact]] = field(default_factory=dict)
    facts_by_year: Dict[int, List[XBRLFact]] = field(default_factory=dict)
    facts_by_form: Dict[str, List[XBRLFact]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize summary to dictionary."""
        return {
            "cik": self.cik,
            "entity_name": self.entity_name,
            "source_file": self.source_file,
            "indexed_at": self.indexed_at.isoformat(),
            "total_facts": self.total_facts,
            "taxonomy_count": len(self.taxonomies),
            "concept_count": len(self.concepts),
            "form_type_count": len(self.form_types),
            "fiscal_year_range": (
                f"{min(self.fiscal_years)}-{max(self.fiscal_years)}"
                if self.fiscal_years
                else "N/A"
            ),
            "accession_number_count": len(self.accession_numbers),
        }

    def get_concept_values(
        self,
        concept: str,
        fiscal_year: Optional[int] = None,
        form_type: Optional[str] = None,
    ) -> List[XBRLFact]:
        """
        Get facts for a specific concept with optional filters.

        Args:
            concept: XBRL concept name (e.g., "Revenue", "NetIncomeLoss").
            fiscal_year: Optional fiscal year filter.
            form_type: Optional form type filter.

        Returns:
            Matching XBRLFact entries.
        """
        facts = self.facts_by_concept.get(concept, [])

        if fiscal_year is not None:
            facts = [f for f in facts if f.fiscal_year == fiscal_year]

        if form_type is not None:
            facts = [f for f in facts if f.form_type == form_type]

        return facts

    def get_filings_in_year(self, year: int) -> List[str]:
        """Get all accession numbers for filings in a specific year."""
        return list({
            f.accession_number
            for f in self.facts_by_year.get(year, [])
            if f.accession_number
        })


class XBRLIndexer:
    """
    Index SEC XBRL Company Facts JSON for cross-referencing.

    Parses the CIK Company Facts JSON (e.g., CIK0000320187.json)
    and builds an indexed structure for fast lookup by concept,
    fiscal year, and form type.

    Args:
        source_path: Path to XBRL Company Facts JSON file.
    """

    def __init__(self, source_path: Optional[Path] = None) -> None:
        self.source_path = source_path

    def index(self, source_path: Optional[Path] = None) -> XBRLIndex:
        """
        Parse and index XBRL Company Facts JSON.

        Args:
            source_path: Path to JSON file. Uses constructor path if None.

        Returns:
            XBRLIndex with all facts indexed by concept, year, and form.
        """
        path = source_path or self.source_path
        if not path or not path.exists():
            logger.error("XBRL source file not found: %s", path)
            return XBRLIndex(
                cik="",
                entity_name="",
                source_file=str(path or ""),
                indexed_at=datetime.utcnow(),
            )

        logger.info("Indexing XBRL data from %s", path)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load XBRL data: %s", e)
            return XBRLIndex(
                cik="",
                entity_name="",
                source_file=str(path),
                indexed_at=datetime.utcnow(),
            )

        cik = str(data.get("cik", ""))
        entity_name = data.get("entityName", "")

        index = XBRLIndex(
            cik=cik,
            entity_name=entity_name,
            source_file=str(path),
            indexed_at=datetime.utcnow(),
        )

        facts_data = data.get("facts", {})

        for taxonomy, concepts in facts_data.items():
            index.taxonomies.add(taxonomy)

            for concept_name, concept_data in concepts.items():
                index.concepts.add(concept_name)
                units = concept_data.get("units", {})

                for unit_key, entries in units.items():
                    for entry in entries:
                        fact = self._parse_fact(
                            taxonomy=taxonomy,
                            concept=concept_name,
                            unit=unit_key,
                            entry=entry,
                        )
                        if fact:
                            index.facts.append(fact)
                            index.total_facts += 1

                            # Index by concept
                            if concept_name not in index.facts_by_concept:
                                index.facts_by_concept[concept_name] = []
                            index.facts_by_concept[concept_name].append(fact)

                            # Index by year
                            if fact.fiscal_year:
                                index.fiscal_years.add(fact.fiscal_year)
                                if fact.fiscal_year not in index.facts_by_year:
                                    index.facts_by_year[fact.fiscal_year] = []
                                index.facts_by_year[fact.fiscal_year].append(fact)

                            # Index by form
                            if fact.form_type:
                                index.form_types.add(fact.form_type)
                                if fact.form_type not in index.facts_by_form:
                                    index.facts_by_form[fact.form_type] = []
                                index.facts_by_form[fact.form_type].append(fact)

                            # Track accession numbers
                            if fact.accession_number:
                                index.accession_numbers.add(fact.accession_number)

        logger.info(
            "XBRL indexing complete: %d facts, %d concepts, %d taxonomies, years %s",
            index.total_facts,
            len(index.concepts),
            len(index.taxonomies),
            f"{min(index.fiscal_years)}-{max(index.fiscal_years)}" if index.fiscal_years else "N/A",
        )

        return index

    def export_index(
        self,
        index: XBRLIndex,
        output_path: Path,
        include_facts: bool = False,
    ) -> Path:
        """
        Export XBRL index to JSON.

        Args:
            index: XBRLIndex to export.
            output_path: Output JSON file path.
            include_facts: Whether to include full fact listing (large).

        Returns:
            Path to exported file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = index.to_dict()
        data["taxonomies"] = sorted(index.taxonomies)
        data["form_types"] = sorted(index.form_types)
        data["fiscal_years"] = sorted(index.fiscal_years)

        if include_facts:
            data["facts"] = [f.to_dict() for f in index.facts]

        # Concept summary (counts per concept)
        data["concept_summary"] = {
            concept: len(facts)
            for concept, facts in sorted(
                index.facts_by_concept.items(),
                key=lambda x: -len(x[1]),
            )[:50]  # Top 50 concepts
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("XBRL index exported to %s", output_path)
        return output_path

    @staticmethod
    def _parse_fact(
        taxonomy: str,
        concept: str,
        unit: str,
        entry: Dict[str, Any],
    ) -> Optional[XBRLFact]:
        """Parse a single XBRL fact entry."""
        try:
            # Parse dates
            period_start = None
            period_end = None
            instant = None

            start_str = entry.get("start")
            end_str = entry.get("end")
            instant_str = entry.get("instant")

            if start_str:
                try:
                    period_start = date.fromisoformat(start_str)
                except ValueError:
                    pass
            if end_str:
                try:
                    period_end = date.fromisoformat(end_str)
                except ValueError:
                    pass
            if instant_str:
                try:
                    instant = date.fromisoformat(instant_str)
                except ValueError:
                    pass

            filing_date = None
            filed_str = entry.get("filed")
            if filed_str:
                try:
                    filing_date = date.fromisoformat(filed_str)
                except ValueError:
                    pass

            return XBRLFact(
                taxonomy=taxonomy,
                concept=concept,
                value=entry.get("val"),
                unit=unit,
                period_start=period_start,
                period_end=period_end,
                instant=instant,
                form_type=entry.get("form"),
                filing_date=filing_date,
                accession_number=entry.get("accn"),
                fiscal_year=entry.get("fy"),
                fiscal_period=entry.get("fp"),
                frame=entry.get("frame"),
            )

        except Exception as e:
            logger.debug(
                "Failed to parse XBRL fact %s/%s: %s", taxonomy, concept, e
            )
            return None
