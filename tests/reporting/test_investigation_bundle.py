"""
Tests for the Investigation Bundle Generator and Component Modules
==================================================================

Validates:
- PublicDiscrepancyEngine: contradiction detection + exports
- InvestigativeArticleGenerator: article synthesis + exports
- MachineLogGenerator: log generation + provenance + exports
- FinancialNetworkMapper: network build + JSON export
- InvestigationBundleGenerator: full bundle orchestration
"""
from __future__ import annotations

import json
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest


# ─── Sample data factories ──────────────────────────────────────────────────


def _sample_analysis_results() -> Dict[str, Any]:
    """Minimal forensic analysis_results dict for testing."""
    return {
        "total_violations": 12,
        "critical_alerts": 1,
        "high_alerts": 4,
        "violations": [
            {
                "type": "Section 16(a) Late Form 4 Filing",
                "severity": "HIGH",
                "accession_number": "0001127602-19-035840",
                "reporting_owner": "John Parker (CEO)",
                "transaction_date": "2019-06-01",
                "filing_date": "2019-06-05",
                "days_late": 3,
                "shares": 24000.0,
                "estimated_penalty": 25000,
                "statutory_reference": "15 U.S.C. § 78p(a)",
                "node_id": "NODE_1",
            },
            {
                "type": "Section 16(a) Late Form 4 Filing",
                "severity": "CRITICAL",
                "accession_number": "0001127602-19-040000",
                "reporting_owner": "Sarah Kim (CFO)",
                "transaction_date": "2019-09-01",
                "filing_date": "2019-09-10",
                "days_late": 7,
                "shares": 50000.0,
                "estimated_penalty": 75000,
                "statutory_reference": "15 U.S.C. § 78p(a)",
                "node_id": "NODE_1",
            },
        ],
        "transactions": [
            {
                "date": "2019-06-01",
                "actor": "John Parker (CEO)",
                "value": 3600000,
                "shares": 24000,
                "risk_level": "HIGH",
                "transaction_type": "SALE",
                "profit": 1200000,
            },
            {
                "date": "2019-09-01",
                "actor": "Sarah Kim (CFO)",
                "value": 7500000,
                "shares": 50000,
                "risk_level": "CRITICAL",
                "transaction_type": "SALE",
                "profit": 2500000,
            },
        ],
        "beneficiaries": [
            {
                "name": "John Parker",
                "role": "CEO",
                "total_profit": 1200000,
                "total_shares": 24000,
                "transaction_count": 3,
                "risk_score": 82,
                "violations": 2,
            },
            {
                "name": "Sarah Kim",
                "role": "CFO",
                "total_profit": 2500000,
                "total_shares": 50000,
                "transaction_count": 5,
                "risk_score": 91,
                "violations": 3,
            },
        ],
        "actors": [
            {
                "actor_id": "A1",
                "name": "John Parker",
                "risk_score": 82,
                "actor_type": "INDIVIDUAL",
                "roles": ["CEO", "Director"],
            },
            {
                "actor_id": "A2",
                "name": "Sarah Kim",
                "risk_score": 91,
                "actor_type": "INDIVIDUAL",
                "roles": ["CFO"],
            },
        ],
        "relationships": [
            {
                "source": "John Parker",
                "target": "Sarah Kim",
                "relationship_type": "BOARD_SEAT",
                "strength": 0.8,
            }
        ],
        "sox_analysis": {
            "certifications": {
                "violations": ["Material weakness in revenue recognition controls"]
            }
        },
    }


def _sample_public_statements() -> List[Dict[str, Any]]:
    """Minimal public statements list for discrepancy testing."""
    return [
        {
            "speaker": "John Parker (CEO)",
            "channel": "earnings_call",
            "date": "2019-04-01",
            "text": (
                "I remain fully committed to this company and confident in "
                "our long-term growth trajectory. My interests are completely "
                "aligned with those of our shareholders."
            ),
            "topic": "insider_trades",
        },
        {
            "speaker": "ACME Corp Compensation Committee",
            "channel": "proxy",
            "date": "2019-09-01",
            "text": (
                "Executive compensation is directly tied to performance metrics "
                "and is designed to align management interests with shareholder "
                "value. Pay is modest and appropriate."
            ),
            "topic": "compensation",
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════
# PublicDiscrepancyEngine Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPublicDiscrepancyEngine:
    """Tests for PublicDiscrepancyEngine."""

    def _make_engine(self):
        from src.reporting.public_discrepancy_engine import PublicDiscrepancyEngine
        return PublicDiscrepancyEngine()

    def test_analyze_returns_discrepancy_report(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
            analysis_period="FY 2019",
        )
        assert report.company_name == "ACME Corp"
        assert report.cik == "999999"
        assert report.analysis_period == "FY 2019"
        assert len(report.report_id) > 0

    def test_analyze_detects_discrepancies(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
            analysis_period="FY 2019",
        )
        # With insider sell violations + public confidence statements, should find discrepancies
        assert len(report.discrepancies) >= 1

    def test_discrepancy_has_required_fields(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )
        for d in report.discrepancies:
            assert d.discrepancy_id
            assert d.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
            assert d.category
            assert d.title
            assert d.narrative
            assert d.evidence_hash
            assert d.public_statement
            assert d.sec_disclosure

    def test_discrepancy_evidence_hash_computed(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )
        for d in report.discrepancies:
            assert len(d.evidence_hash) == 64  # SHA-256 hex

    def test_recompute_stats(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )
        report.recompute_stats()
        total = (
            report.critical_count
            + report.high_count
            + report.medium_count
            + report.low_count
        )
        assert total == len(report.discrepancies)

    def test_to_dict_structure(self):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )
        d = report.to_dict()
        assert "report_id" in d
        assert "summary" in d
        assert "discrepancies" in d
        assert isinstance(d["discrepancies"], list)

    def test_export_json(self, tmp_path):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "disc.json"
        result = engine.export_json(report, out)
        assert result == out
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["company_name"] == "ACME Corp"

    def test_export_markdown(self, tmp_path):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "disc.md"
        result = engine.export_markdown(report, out)
        assert result == out
        text = out.read_text()
        assert "ACME Corp" in text
        assert "DISCREPANCY" in text.upper()

    def test_export_html(self, tmp_path):
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "disc.html"
        result = engine.export_html(report, out)
        assert result == out
        html = out.read_text()
        assert "<html" in html.lower()
        assert "ACME Corp" in html

    def test_analyze_without_public_statements_synthesises(self):
        """Should still produce results when no public statements are provided."""
        engine = self._make_engine()
        report = engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=None,
        )
        assert report.public_statements_analyzed >= 0  # Synthesised statements

    def test_analyze_empty_violations(self):
        """Should handle empty violations gracefully."""
        engine = self._make_engine()
        results = {"total_violations": 0, "violations": [], "beneficiaries": []}
        report = engine.analyze(
            company_name="Clean Corp",
            cik="111111",
            analysis_results=results,
        )
        assert report.company_name == "Clean Corp"
        assert len(report.discrepancies) == 0


# ═══════════════════════════════════════════════════════════════════════════
# InvestigativeArticleGenerator Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestInvestigativeArticleGenerator:
    """Tests for InvestigativeArticleGenerator."""

    def _make_gen(self):
        from src.reporting.investigative_article_generator import (
            InvestigativeArticleGenerator,
        )
        return InvestigativeArticleGenerator()

    def test_generate_returns_article(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            analysis_period="FY 2019",
        )
        assert article.company_name == "ACME Corp"
        assert article.cik == "999999"
        assert article.analysis_period == "FY 2019"
        assert len(article.headline) > 0
        assert len(article.sub_headline) > 0

    def test_article_has_sections(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        assert len(article.sections) >= 5

    def test_article_sections_have_bodies(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        for section in article.sections:
            assert section.section_id
            assert section.heading
            assert len(section.body) > 50

    def test_article_has_receipts(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        assert len(article.receipts) >= 1
        for r in article.receipts:
            assert "receipt_id" in r
            assert "type" in r

    def test_article_has_enforcement_recommendation(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        assert len(article.enforcement_recommendation) > 100

    def test_severity_label_critical(self):
        gen = self._make_gen()
        results = dict(_sample_analysis_results())
        results["critical_alerts"] = 5
        article = gen.generate(
            company_name="Bad Corp",
            cik="000001",
            analysis_results=results,
        )
        assert article.severity_label == "CRITICAL"

    def test_word_count_populated(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        assert article.word_count > 200

    def test_key_statistics(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        stats = article.key_statistics
        assert stats["total_violations"] == 12
        assert stats["insiders_identified"] >= 1

    def test_export_markdown(self, tmp_path):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "article.md"
        result = gen.export_markdown(article, out)
        assert result == out
        text = out.read_text()
        assert "ACME Corp" in text
        assert "# " in text

    def test_export_html(self, tmp_path):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "article.html"
        result = gen.export_html(article, out)
        assert result == out
        html = out.read_text()
        assert "<html" in html.lower()

    def test_export_json(self, tmp_path):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "article.json"
        result = gen.export_json(article, out)
        assert result == out
        data = json.loads(out.read_text())
        assert data["company_name"] == "ACME Corp"
        assert "sections" in data
        assert "receipts" in data

    def test_to_dict_serialisable(self):
        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        d = article.to_dict()
        # Should be JSON-serialisable
        json.dumps(d, default=str)

    def test_generate_with_discrepancy_report(self):
        """Article generation should incorporate discrepancy report if provided."""
        from src.reporting.public_discrepancy_engine import PublicDiscrepancyEngine
        disc_engine = PublicDiscrepancyEngine()
        disc_report = disc_engine.analyze(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )

        gen = self._make_gen()
        article = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            analysis_period="FY 2019",
            discrepancy_report=disc_report,
        )
        # S04 section should reference discrepancies
        s04 = next((s for s in article.sections if s.section_id == "S04"), None)
        assert s04 is not None
        # Body should mention discrepancies
        assert len(s04.body) > 50


# ═══════════════════════════════════════════════════════════════════════════
# MachineLogGenerator Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMachineLogGenerator:
    """Tests for MachineLogGenerator."""

    def _make_gen(self):
        from src.reporting.machine_log_generator import MachineLogGenerator
        return MachineLogGenerator()

    def test_generate_returns_log(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            analysis_period="FY 2019",
        )
        assert log.company_name == "ACME Corp"
        assert log.cik == "999999"
        assert len(log.entries) > 0

    def test_log_has_findings(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        findings = [e for e in log.entries if e.log_level == "FINDING"]
        # Should have one FINDING per violation
        assert len(findings) == len(_sample_analysis_results()["violations"])

    def test_log_has_audit_entries(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        audits = [e for e in log.entries if e.log_level == "AUDIT"]
        assert len(audits) >= 1

    def test_log_has_signals_from_beneficiaries(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        signals = [e for e in log.entries if e.log_level == "SIGNAL"]
        assert len(signals) >= 1  # From beneficiaries

    def test_entry_has_provenance(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        findings = [e for e in log.entries if e.log_level == "FINDING"]
        for entry in findings:
            assert entry.provenance is not None
            assert entry.provenance.pipeline_stage
            assert entry.provenance.detection_method
            assert entry.provenance.confidence_score >= 0

    def test_entry_to_dict(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        for entry in log.entries[:5]:
            d = entry.to_dict()
            assert "entry_id" in d
            assert "log_level" in d
            assert "severity" in d

    def test_entry_to_ecs(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        for entry in log.entries[:5]:
            ecs = entry.to_ecs()
            assert "@timestamp" in ecs
            assert "log.level" in ecs
            assert "jlaw.severity" in ecs

    def test_recompute_stats(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        log.recompute_stats()
        total = log.finding_count + log.signal_count + log.context_count + log.audit_count
        # total_entries should equal len(entries) after recompute
        assert log.total_entries == len(log.entries)

    def test_seal_produces_hash(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        seal = log.seal()
        assert len(seal) == 64  # SHA-256

    def test_to_manifest_no_entries(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        manifest = log.to_manifest()
        assert "entries" not in manifest
        assert "counts" in manifest
        assert "integrity" in manifest

    def test_to_ecs_stream(self):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        stream = log.to_ecs_stream()
        assert isinstance(stream, list)
        assert len(stream) == len(log.entries)

    def test_export_full_log(self, tmp_path):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "full_log.json"
        result = gen.export_full_log(log, out)
        assert result == out
        data = json.loads(out.read_text())
        assert "entries" in data

    def test_export_ecs_stream(self, tmp_path):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "ecs.json"
        result = gen.export_ecs_stream(log, out)
        assert result == out
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert len(data) > 0
        assert "@timestamp" in data[0]

    def test_export_manifest(self, tmp_path):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "manifest.json"
        result = gen.export_manifest(log, out)
        assert result == out
        data = json.loads(out.read_text())
        assert "entries" not in data
        assert "counts" in data

    def test_export_ndjson(self, tmp_path):
        gen = self._make_gen()
        log = gen.generate(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "log.ndjson"
        result = gen.export_ndjson(log, out)
        assert result == out
        lines = [l for l in out.read_text().splitlines() if l.strip()]
        assert len(lines) == len(log.entries)
        # Each line should be valid JSON
        for line in lines:
            json.loads(line)

    def test_handles_empty_violations(self):
        gen = self._make_gen()
        results = {"total_violations": 0, "violations": [], "beneficiaries": []}
        log = gen.generate(
            company_name="Clean Corp",
            cik="111111",
            analysis_results=results,
        )
        assert len(log.entries) >= 1  # At least audit entries


# ═══════════════════════════════════════════════════════════════════════════
# FinancialNetworkMapper Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestFinancialNetworkMapper:
    """Tests for FinancialNetworkMapper."""

    def _make_mapper(self):
        from src.reporting.visualizations.financial_network_map import (
            FinancialNetworkMapper,
        )
        return FinancialNetworkMapper()

    def test_build_network_returns_data(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            analysis_period="FY 2019",
        )
        assert net.company_name == "ACME Corp"
        assert net.cik == "999999"
        assert len(net.nodes) > 0
        assert len(net.edges) > 0

    def test_network_has_company_node(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        company_node = next(
            (n for n in net.nodes if n.node_type == "CORPORATION"), None
        )
        assert company_node is not None
        assert "ACME Corp" in company_node.label

    def test_network_has_insider_nodes(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        individual_nodes = [n for n in net.nodes if n.node_type == "INDIVIDUAL"]
        assert len(individual_nodes) >= 1

    def test_network_has_edges(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        assert len(net.edges) > 0
        for edge in net.edges:
            assert edge.source_id
            assert edge.target_id
            assert edge.edge_type

    def test_to_dict(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        d = net.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "metrics" in d

    def test_export_json(self, tmp_path):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        out = tmp_path / "network.json"
        result = mapper.export_json(net, out)
        assert result == out
        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "edges" in data

    def test_build_handles_empty_violations(self):
        mapper = self._make_mapper()
        results = {
            "total_violations": 0,
            "violations": [],
            "beneficiaries": [],
            "actors": [],
            "relationships": [],
        }
        net = mapper.build_network(
            company_name="Clean Corp",
            cik="111111",
            analysis_results=results,
        )
        # At minimum, should have the company node
        assert len(net.nodes) >= 1

    def test_network_node_risk_score_bounded(self):
        mapper = self._make_mapper()
        net = mapper.build_network(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
        )
        for node in net.nodes:
            assert 0.0 <= node.risk_score <= 100.0


# ═══════════════════════════════════════════════════════════════════════════
# InvestigationBundleGenerator Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestInvestigationBundleGenerator:
    """Tests for InvestigationBundleGenerator."""

    def _make_gen(self):
        from src.reporting.investigation_bundle_generator import (
            InvestigationBundleGenerator,
        )
        return InvestigationBundleGenerator()

    def test_generate_bundle_returns_manifest(self, tmp_path):
        gen = self._make_gen()
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=tmp_path / "bundle",
            analysis_period="FY 2019",
            skip_visualizations=True,
        )
        assert manifest.company_name == "ACME Corp"
        assert manifest.cik == "999999"
        assert len(manifest.files) > 0

    def test_generate_bundle_creates_files(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        # Should have created output files
        assert out.exists()
        files = list(out.iterdir())
        assert len(files) >= 3

    def test_bundle_manifest_json_written(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        manifest_file = out / "bundle_manifest.json"
        assert manifest_file.exists()
        data = json.loads(manifest_file.read_text())
        assert data["company_name"] == "ACME Corp"
        assert "files" in data
        assert "integrity" in data

    def test_bundle_manifest_has_sha256(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        assert len(manifest.bundle_sha256) == 64

    def test_all_files_have_sha256(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        for f in manifest.files:
            assert len(f.sha256) == 64
            assert f.size_bytes > 0

    def test_bundle_includes_narrative_outputs(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        narrative_files = [f for f in manifest.files if f.file_type == "narrative"]
        assert len(narrative_files) >= 3

    def test_bundle_includes_machine_logs(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        log_files = [f for f in manifest.files if f.file_type == "machine_log"]
        assert len(log_files) >= 3

    def test_bundle_skip_visualizations_respected(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        assert "financial_network_visualisation" in manifest.components_skipped

    def test_bundle_with_public_statements(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            public_statements=_sample_public_statements(),
            skip_visualizations=True,
        )
        assert len(manifest.files) > 0

    def test_bundle_manifest_summary_stats(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        assert manifest.total_violations == 12
        assert manifest.insiders_identified >= 1
        assert manifest.total_penalty_exposure_usd > 0

    def test_load_analysis_results(self, tmp_path):
        from src.reporting.investigation_bundle_generator import (
            InvestigationBundleGenerator,
        )
        data = _sample_analysis_results()
        f = tmp_path / "results.json"
        f.write_text(json.dumps(data))
        loaded = InvestigationBundleGenerator.load_analysis_results(f)
        assert loaded["total_violations"] == 12

    def test_to_dict_serialisable(self, tmp_path):
        gen = self._make_gen()
        out = tmp_path / "bundle"
        manifest = gen.generate_bundle(
            company_name="ACME Corp",
            cik="999999",
            analysis_results=_sample_analysis_results(),
            output_dir=out,
            skip_visualizations=True,
        )
        d = manifest.to_dict()
        json.dumps(d, default=str)  # Should not raise


# ═══════════════════════════════════════════════════════════════════════════
# Integration smoke test
# ═══════════════════════════════════════════════════════════════════════════


class TestBundleIntegration:
    """Integration smoke tests for the full bundle pipeline."""

    def test_full_pipeline_no_exceptions(self, tmp_path):
        """Running the full bundle pipeline should not raise exceptions."""
        from src.reporting.investigation_bundle_generator import (
            InvestigationBundleGenerator,
        )
        gen = InvestigationBundleGenerator()
        manifest = gen.generate_bundle(
            company_name="TestCo Inc.",
            cik="123456",
            analysis_results=_sample_analysis_results(),
            output_dir=tmp_path / "integration_bundle",
            analysis_period="FY 2019",
            public_statements=_sample_public_statements(),
            skip_visualizations=True,
        )
        assert manifest is not None
        assert len(manifest.files) >= 5

    def test_investigative_article_references_company(self, tmp_path):
        """Generated article should reference the company name."""
        from src.reporting.investigative_article_generator import (
            InvestigativeArticleGenerator,
        )
        gen = InvestigativeArticleGenerator()
        article = gen.generate(
            company_name="TestCo Inc.",
            cik="123456",
            analysis_results=_sample_analysis_results(),
            analysis_period="FY 2019",
        )
        md_path = tmp_path / "article.md"
        gen.export_markdown(article, md_path)
        content = md_path.read_text()
        assert "TestCo Inc." in content

    def test_discrepancy_report_references_company(self, tmp_path):
        """Generated discrepancy report should reference the company name."""
        from src.reporting.public_discrepancy_engine import PublicDiscrepancyEngine
        engine = PublicDiscrepancyEngine()
        report = engine.analyze(
            company_name="TestCo Inc.",
            cik="123456",
            analysis_results=_sample_analysis_results(),
            public_statements=_sample_public_statements(),
        )
        json_path = tmp_path / "disc.json"
        engine.export_json(report, json_path)
        data = json.loads(json_path.read_text())
        assert data["company_name"] == "TestCo Inc."
