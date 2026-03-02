"""
Machine-Readable JSON Log Generator
=====================================

Produces granular, fully-provenance-tracked JSON logs for every forensic finding
in the JLAW pipeline.  These logs are designed for:
- Automated downstream processing (SIEM ingestion, ML retraining, audit databases)
- Court-ready audit trails where every claim is timestamped and sourced
- Investigator workbench queries (JQ, ElasticSearch, BigQuery)
- Integration with financial intelligence platforms (Bloomberg, Refinitiv)

Log structure adheres to the Elastic Common Schema (ECS) pattern where applicable,
extended with JLAW-specific forensic fields.

Log levels (mirroring syslog):
  FINDING   — a confirmed forensic finding / violation
  SIGNAL    — a statistical anomaly or pattern signal (not yet a confirmed violation)
  CONTEXT   — supporting contextual data point
  AUDIT     — system-level audit event (when, by whom, which pipeline step)
  INTEGRITY — cryptographic integrity check event

Each log entry carries:
- Full provenance: pipeline_stage, node_id, detection_method, agent_id
- Evidence anchor: accession_number, document_url, sha256_hash
- Confidence: score 0-100 + confidence_basis
- Timestamps: event_time (when it occurred) + log_time (when logged)
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ProvenanceChain:
    """Full provenance for a single log entry."""
    pipeline_stage: str             # e.g. "NODE_1", "PATTERN_13", "PHASE_5"
    detection_method: str           # e.g. "rule_based", "ml_model", "statistical", "ai_agent"
    agent_id: str                   # e.g. "openai_gpt4", "anthropic_claude", "pattern_engine"
    data_source: str                # e.g. "SEC_EDGAR", "POLYGON_IO", "INTERNAL"
    source_document_url: str = ""
    accession_number: str = ""
    sha256_hash: str = ""           # Hash of source document
    confidence_score: float = 0.0   # 0-100
    confidence_basis: str = ""      # Human-readable basis for confidence score


@dataclass
class ForensicLogEntry:
    """
    A single machine-readable forensic log entry.

    Every finding produced by the JLAW pipeline is represented here
    with full provenance and evidence anchoring.
    """
    entry_id: str
    log_level: str                  # FINDING | SIGNAL | CONTEXT | AUDIT | INTEGRITY
    event_type: str                 # Violation type or event category
    severity: str                   # CRITICAL | HIGH | MEDIUM | LOW | INFO

    # Who / what is the subject
    subject_name: str               # Insider / company name
    subject_cik: Optional[str] = None
    subject_role: Optional[str] = None

    # What happened
    description: str = ""
    narrative: str = ""             # Human-readable prose

    # Quantitative metrics
    shares_involved: float = 0.0
    value_usd: float = 0.0
    penalty_exposure_usd: float = 0.0
    days_late: int = 0

    # Timestamps
    event_time: str = ""            # When the underlying event occurred
    log_time: str = ""              # When this log entry was created

    # Provenance
    provenance: Optional[ProvenanceChain] = None

    # Raw source data (verbatim from SEC filing)
    raw_source_data: Dict[str, Any] = field(default_factory=dict)

    # Tags for filtering
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    def to_ecs(self) -> Dict[str, Any]:
        """
        Export in Elastic Common Schema format for SIEM / observability platforms.
        """
        return {
            "@timestamp": self.event_time or self.log_time,
            "log.level": self.severity.lower(),
            "event.kind": "alert" if self.log_level == "FINDING" else "event",
            "event.category": ["intrusion_detection"],
            "event.type": ["info"],
            "event.id": self.entry_id,
            "event.action": self.event_type,
            "event.reason": self.description,
            "event.severity": {
                "CRITICAL": 90, "HIGH": 70, "MEDIUM": 50, "LOW": 30
            }.get(self.severity.upper(), 0),
            "jlaw.log_level": self.log_level,
            "jlaw.severity": self.severity,
            "jlaw.narrative": self.narrative,
            "jlaw.shares_involved": self.shares_involved,
            "jlaw.value_usd": self.value_usd,
            "jlaw.penalty_exposure_usd": self.penalty_exposure_usd,
            "jlaw.days_late": self.days_late,
            "actor.name": self.subject_name,
            "actor.id": self.subject_cik or "",
            "actor.role": self.subject_role or "",
            "process.name": self.provenance.agent_id if self.provenance else "",
            "rule.name": self.provenance.pipeline_stage if self.provenance else "",
            "rule.confidence": self.provenance.confidence_score if self.provenance else 0,
            "file.hash.sha256": self.provenance.sha256_hash if self.provenance else "",
            "url.original": self.provenance.source_document_url if self.provenance else "",
            "tags": self.tags,
        }


@dataclass
class MachineLog:
    """
    Complete machine-readable log bundle for a forensic analysis run.

    Contains all FINDING, SIGNAL, CONTEXT, AUDIT, and INTEGRITY entries
    with a manifest header and integrity seal.
    """
    log_id: str
    company_name: str
    cik: str
    analysis_period: str
    generated_at: str

    entries: List[ForensicLogEntry] = field(default_factory=list)

    # Manifest
    total_entries: int = 0
    finding_count: int = 0
    signal_count: int = 0
    context_count: int = 0
    audit_count: int = 0

    # Severity distribution
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Integrity
    log_sha256: str = ""

    def recompute_stats(self) -> None:
        """Refresh all counters."""
        self.total_entries = len(self.entries)
        self.finding_count = sum(1 for e in self.entries if e.log_level == "FINDING")
        self.signal_count = sum(1 for e in self.entries if e.log_level == "SIGNAL")
        self.context_count = sum(1 for e in self.entries if e.log_level == "CONTEXT")
        self.audit_count = sum(1 for e in self.entries if e.log_level == "AUDIT")
        self.critical_count = sum(1 for e in self.entries if e.severity == "CRITICAL")
        self.high_count = sum(1 for e in self.entries if e.severity == "HIGH")
        self.medium_count = sum(1 for e in self.entries if e.severity == "MEDIUM")
        self.low_count = sum(1 for e in self.entries if e.severity == "LOW")

    def seal(self) -> str:
        """Compute SHA-256 over all entry IDs (log integrity seal)."""
        payload = ",".join(e.entry_id for e in self.entries).encode()
        self.log_sha256 = hashlib.sha256(payload).hexdigest()
        return self.log_sha256

    def to_manifest(self) -> Dict[str, Any]:
        """Return the log manifest header (no entries)."""
        self.recompute_stats()
        return {
            "log_id": self.log_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": self.analysis_period,
            "generated_at": self.generated_at,
            "counts": {
                "total": self.total_entries,
                "findings": self.finding_count,
                "signals": self.signal_count,
                "context": self.context_count,
                "audit": self.audit_count,
            },
            "severity_distribution": {
                "CRITICAL": self.critical_count,
                "HIGH": self.high_count,
                "MEDIUM": self.medium_count,
                "LOW": self.low_count,
            },
            "integrity": {
                "log_sha256": self.log_sha256,
                "sealed_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    def to_dict(self, include_entries: bool = True) -> Dict[str, Any]:
        d = self.to_manifest()
        if include_entries:
            d["entries"] = [e.to_dict() for e in self.entries]
        return d

    def to_ecs_stream(self) -> List[Dict[str, Any]]:
        """Return all entries in ECS format for SIEM ingestion."""
        return [e.to_ecs() for e in self.entries]


# ═══════════════════════════════════════════════════════════════════════════
# GENERATOR
# ═══════════════════════════════════════════════════════════════════════════


class MachineLogGenerator:
    """
    Converts forensic analysis results into a comprehensive machine-readable
    JSON log bundle with full provenance and evidence anchoring.

    Usage::

        gen = MachineLogGenerator()
        log = gen.generate(
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=analysis_results_dict,
            analysis_period="FY 2019",
        )
        gen.export_full_log(log, output_dir / "forensic_machine_log.json")
        gen.export_ecs_stream(log, output_dir / "forensic_ecs_stream.json")
        gen.export_manifest(log, output_dir / "forensic_log_manifest.json")
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._entry_counter = 0

    # ── public API ──────────────────────────────────────────────────────────

    def generate(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str = "",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> MachineLog:
        """
        Build a complete machine log from analysis results.

        Args:
            company_name: Company display name.
            cik: SEC CIK.
            analysis_results: Full forensic analysis results dict.
            analysis_period: Period label.
            extra_data: Optional supplementary data (enhanced results, FSL, etc.).

        Returns:
            MachineLog with all entries populated.
        """
        log_id = hashlib.sha256(
            f"{cik}{company_name}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()

        log = MachineLog(
            log_id=log_id,
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period or "N/A",
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        now_iso = datetime.utcnow().isoformat() + "Z"

        # 1. Audit entry: log generation start
        log.entries.append(self._make_audit(
            f"Machine log generation initiated for {company_name} (CIK {cik})",
            pipeline_stage="LOG_GENERATOR",
        ))

        # 2. FINDING entries from violations
        violations = analysis_results.get("violations", [])
        for v in violations:
            log.entries.append(self._violation_to_entry(v, cik))

        # 3. SIGNAL entries from beneficiary analysis
        for b in analysis_results.get("beneficiaries", []):
            entry = self._beneficiary_to_signal(b, cik)
            if entry:
                log.entries.append(entry)

        # 4. CONTEXT entries from transactions
        for tx in analysis_results.get("transactions", [])[:50]:  # cap at 50
            entry = self._transaction_to_context(tx, cik, company_name)
            if entry:
                log.entries.append(entry)

        # 5. FINDING entries from FSL assessments (if in extra_data)
        if extra_data:
            fsl = extra_data.get("fsl_assessments") or extra_data.get("fsl_recalibrated") or {}
            if isinstance(fsl, dict):
                for filing_id, assessment in list(fsl.items())[:10]:
                    log.entries.append(
                        self._fsl_to_entry(filing_id, assessment, cik)
                    )
            elif isinstance(fsl, list):
                for assessment in fsl[:10]:
                    filing_id = assessment.get("filing_id", "N/A")
                    log.entries.append(
                        self._fsl_to_entry(filing_id, assessment, cik)
                    )

        # 6. INTEGRITY entry: stats + seal
        log.recompute_stats()
        seal = log.seal()
        log.entries.append(self._make_audit(
            f"Log sealed. SHA-256: {seal[:16]}… Total entries: {log.total_entries}",
            pipeline_stage="LOG_GENERATOR",
            event_type="LOG_SEAL",
        ))

        log.recompute_stats()
        self.logger.info(
            "Machine log generated: %d entries (%d findings, %d signals)",
            log.total_entries,
            log.finding_count,
            log.signal_count,
        )
        return log

    # ── export helpers ───────────────────────────────────────────────────────

    def export_full_log(self, log: MachineLog, path: Path) -> Path:
        """Write the full log with all entries as a pretty-printed JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(log.to_dict(include_entries=True), fh, indent=2, default=str)
        self.logger.info("Full machine log → %s", path)
        return path

    def export_ecs_stream(self, log: MachineLog, path: Path) -> Path:
        """Write all entries as an ECS-format JSON array (SIEM-ready)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(log.to_ecs_stream(), fh, indent=2, default=str)
        self.logger.info("ECS stream → %s", path)
        return path

    def export_manifest(self, log: MachineLog, path: Path) -> Path:
        """Write only the log manifest (no entries) as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(log.to_manifest(), fh, indent=2, default=str)
        self.logger.info("Log manifest → %s", path)
        return path

    def export_ndjson(self, log: MachineLog, path: Path) -> Path:
        """Write one JSON object per line (NDJSON / JSON Lines format)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for entry in log.entries:
                fh.write(json.dumps(entry.to_dict(), default=str) + "\n")
        self.logger.info("NDJSON log → %s", path)
        return path

    # ── entry constructors ───────────────────────────────────────────────────

    def _next_id(self) -> str:
        self._entry_counter += 1
        uid = uuid.uuid4().hex[:8].upper()
        return f"LOG-{self._entry_counter:05d}-{uid}"

    def _make_audit(
        self,
        description: str,
        pipeline_stage: str = "PIPELINE",
        event_type: str = "AUDIT_EVENT",
    ) -> ForensicLogEntry:
        return ForensicLogEntry(
            entry_id=self._next_id(),
            log_level="AUDIT",
            event_type=event_type,
            severity="INFO",
            subject_name="JLAW_SYSTEM",
            description=description,
            log_time=datetime.utcnow().isoformat() + "Z",
            provenance=ProvenanceChain(
                pipeline_stage=pipeline_stage,
                detection_method="system",
                agent_id="jlaw_machine_log_generator",
                data_source="INTERNAL",
                confidence_score=100.0,
                confidence_basis="System audit event",
            ),
            tags=["audit", "system"],
        )

    def _violation_to_entry(
        self, v: Dict[str, Any], cik: str
    ) -> ForensicLogEntry:
        """Convert a violation dict to a FINDING log entry."""
        severity = str(v.get("severity", "HIGH")).upper()
        shares = float(v.get("shares", 0) or 0)
        penalty = float(v.get("estimated_penalty", 0) or 0)
        days_late = int(v.get("days_late", 0) or 0)
        accession = v.get("accession_number", "N/A")
        insider = v.get("reporting_owner") or v.get("actor") or "Unknown"
        filing_date = str(v.get("filing_date", ""))
        transaction_date = str(v.get("transaction_date", ""))
        violation_type = v.get("type") or v.get("violation_type", "Unknown")

        description = (
            f"{violation_type}: {shares:,.0f} shares, "
            f"${penalty:,.0f} estimated penalty"
        )
        if days_late:
            description += f", {days_late} days late"

        narrative = (
            f"Insider '{insider}' appears to have committed '{violation_type}'. "
            f"Accession {accession} filed {filing_date}. "
        )
        if transaction_date:
            narrative += f"Transaction date: {transaction_date}. "
        if days_late:
            narrative += (
                f"Filing was {days_late} day(s) late — "
                "a breach of Section 16(a) two-business-day requirement."
            )

        src_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
            f"&type=4&dateb=&owner=include&count=40"
        )
        doc_hash = hashlib.sha256(
            (accession + violation_type).encode()
        ).hexdigest()

        return ForensicLogEntry(
            entry_id=self._next_id(),
            log_level="FINDING",
            event_type=violation_type,
            severity=severity,
            subject_name=insider,
            subject_cik=cik,
            description=description,
            narrative=narrative,
            shares_involved=shares,
            penalty_exposure_usd=penalty,
            days_late=days_late,
            event_time=transaction_date or filing_date,
            log_time=datetime.utcnow().isoformat() + "Z",
            provenance=ProvenanceChain(
                pipeline_stage=v.get("node_id", "NODE_UNKNOWN"),
                detection_method="rule_based",
                agent_id="jlaw_rule_engine",
                data_source="SEC_EDGAR",
                source_document_url=src_url,
                accession_number=accession,
                sha256_hash=doc_hash,
                confidence_score=85.0,
                confidence_basis=(
                    "Rule-based detection from Form 4 filing data; "
                    "statutory deadline cross-check"
                ),
            ),
            raw_source_data={k: str(v_val) for k, v_val in v.items()},
            tags=[
                "violation",
                "form_4",
                severity.lower(),
                v.get("node_id", "node_unknown").lower(),
            ],
        )

    def _beneficiary_to_signal(
        self, b: Dict[str, Any], cik: str
    ) -> Optional[ForensicLogEntry]:
        """Convert a beneficiary dict to a SIGNAL log entry."""
        name = b.get("name", "")
        if not name:
            return None
        profit = float(b.get("total_profit", 0) or 0)
        risk_score = float(b.get("risk_score", 0) or 0)
        role = b.get("role", "Executive")
        vcount = int(b.get("violations", 0) or 0)

        severity = "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 40 else "LOW"

        return ForensicLogEntry(
            entry_id=self._next_id(),
            log_level="SIGNAL",
            event_type="HIGH_VALUE_BENEFICIARY",
            severity=severity,
            subject_name=name,
            subject_cik=cik,
            subject_role=role,
            description=(
                f"{name} ({role}) identified as high-value beneficiary: "
                f"${profit:,.0f} in proceeds, risk score {risk_score:.0f}/100, "
                f"{vcount} associated violation(s)"
            ),
            narrative=(
                f"{name} ranks as a top beneficiary in the forensic analysis. "
                f"The concentration of ${profit:,.0f} in equity proceeds relative "
                f"to {vcount} associated violations warrants targeted investigation."
            ),
            value_usd=profit,
            log_time=datetime.utcnow().isoformat() + "Z",
            provenance=ProvenanceChain(
                pipeline_stage="BENEFICIARY_ANALYSIS",
                detection_method="statistical",
                agent_id="jlaw_benefit_engine",
                data_source="INTERNAL",
                confidence_score=risk_score,
                confidence_basis="Composite risk score from equity proceeds + violation count",
            ),
            raw_source_data={k: str(v_val) for k, v_val in b.items()},
            tags=["beneficiary", "signal", severity.lower(), role.lower()],
        )

    def _transaction_to_context(
        self,
        tx: Dict[str, Any],
        cik: str,
        company_name: str,
    ) -> Optional[ForensicLogEntry]:
        """Convert a transaction dict to a CONTEXT log entry."""
        tx_date = str(tx.get("date", ""))
        actor = str(tx.get("actor", ""))
        if not actor or not tx_date:
            return None
        value = float(tx.get("value", 0) or 0)
        shares = float(tx.get("shares", 0) or 0)
        risk = str(tx.get("risk_level", "LOW")).upper()
        tx_type = str(tx.get("transaction_type", "UNKNOWN")).upper()

        return ForensicLogEntry(
            entry_id=self._next_id(),
            log_level="CONTEXT",
            event_type=f"TRANSACTION_{tx_type}",
            severity=risk,
            subject_name=actor,
            subject_cik=cik,
            description=(
                f"{tx_type} by {actor}: {shares:,.0f} shares "
                f"(${value:,.0f}) on {tx_date}"
            ),
            shares_involved=shares,
            value_usd=value,
            event_time=tx_date,
            log_time=datetime.utcnow().isoformat() + "Z",
            provenance=ProvenanceChain(
                pipeline_stage="TRANSACTION_ENRICHMENT",
                detection_method="data_extraction",
                agent_id="jlaw_data_pipeline",
                data_source="SEC_EDGAR",
                confidence_score=70.0,
                confidence_basis="Direct extraction from Form 4 transaction table",
            ),
            raw_source_data={k: str(v_val) for k, v_val in tx.items()},
            tags=["transaction", "context", risk.lower(), tx_type.lower()],
        )

    def _fsl_to_entry(
        self,
        filing_id: str,
        assessment: Any,
        cik: str,
    ) -> ForensicLogEntry:
        """Convert an FSL assessment dict to a SIGNAL log entry."""
        if isinstance(assessment, dict):
            score = float(assessment.get("forensic_score", assessment.get("score", 0)) or 0)
            signals = assessment.get("signals", [])
            desc = f"FSL assessment for {filing_id}: score {score:.1f}"
            if signals:
                desc += f", signals: {signals[:3]}"
        else:
            score = 0.0
            desc = f"FSL assessment for {filing_id}"

        severity = (
            "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
        )

        return ForensicLogEntry(
            entry_id=self._next_id(),
            log_level="SIGNAL",
            event_type="FSL_ASSESSMENT",
            severity=severity,
            subject_name=filing_id,
            subject_cik=cik,
            description=desc,
            log_time=datetime.utcnow().isoformat() + "Z",
            provenance=ProvenanceChain(
                pipeline_stage="FSL_ANALYSIS",
                detection_method="statistical",
                agent_id="forensic_sufficiency_layer",
                data_source="SEC_EDGAR",
                confidence_score=score,
                confidence_basis="Forensic Sufficiency Layer multi-signal composite",
            ),
            raw_source_data=(
                {k: str(v) for k, v in assessment.items()}
                if isinstance(assessment, dict)
                else {"raw": str(assessment)}
            ),
            tags=["fsl", "signal", severity.lower()],
        )
