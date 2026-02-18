"""
Tests for Enhanced Visual Reporting
====================================

Validates the new visualization generators and the visual dossier PDF generator.
"""

import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest


# ─── Sample data factories ──────────────────────────────────────────────


def _sample_transactions(n: int = 12):
    """Generate sample transaction data."""
    actors = ["John Parker (CEO)", "Sarah Kim (CFO)", "Mike Chen (Director)", "Lisa Wang (VP)"]
    types = ["SALE", "PURCHASE", "GRANT", "EXERCISE"]
    risks = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    txns = []
    base = date(2019, 3, 1)
    for i in range(n):
        txns.append({
            "date": base + timedelta(days=i * 25),
            "actor": actors[i % len(actors)],
            "value": (i + 1) * 150000,
            "shares": (i + 1) * 1000,
            "risk_level": risks[i % len(risks)],
            "transaction_type": types[i % len(types)],
            "profit": (i + 1) * 50000,
        })
    return txns


def _sample_beneficiaries():
    """Generate sample beneficiary data."""
    return [
        {"name": "John Parker", "role": "CEO", "total_profit": 2500000,
         "transaction_count": 8, "risk_score": 85, "violations": 4},
        {"name": "Sarah Kim", "role": "CFO", "total_profit": 1800000,
         "transaction_count": 6, "risk_score": 72, "violations": 3},
        {"name": "Mike Chen", "role": "Director", "total_profit": 900000,
         "transaction_count": 4, "risk_score": 45, "violations": 1},
        {"name": "Lisa Wang", "role": "VP", "total_profit": 650000,
         "transaction_count": 3, "risk_score": 30, "violations": 0},
    ]


def _sample_filings():
    """Generate sample filing data."""
    return [
        {"filing_type": "Form 4", "filing_date": date(2019, 3, 5),
         "trigger_date": date(2019, 3, 3), "filer": "John Parker"},
        {"filing_type": "Form 4", "filing_date": date(2019, 6, 10),
         "trigger_date": date(2019, 6, 1), "filer": "Sarah Kim"},
        {"filing_type": "10-K", "filing_date": date(2019, 8, 25),
         "trigger_date": date(2019, 6, 30), "filer": "NIKE, Inc."},
        {"filing_type": "10-Q", "filing_date": date(2019, 11, 5),
         "trigger_date": date(2019, 9, 30), "filer": "NIKE, Inc."},
        {"filing_type": "8-K", "filing_date": date(2019, 7, 20),
         "trigger_date": date(2019, 7, 15), "filer": "NIKE, Inc."},
    ]


def _sample_actors():
    """Generate sample actor data."""
    return [
        {"actor_id": "A1", "name": "John Parker", "risk_score": 85,
         "actor_type": "INDIVIDUAL", "roles": ["CEO", "Director"]},
        {"actor_id": "A2", "name": "Sarah Kim", "risk_score": 72,
         "actor_type": "INDIVIDUAL", "roles": ["CFO"]},
        {"actor_id": "A3", "name": "Mike Chen", "risk_score": 45,
         "actor_type": "INDIVIDUAL", "roles": ["Director"]},
        {"actor_id": "A4", "name": "Lisa Wang", "risk_score": 30,
         "actor_type": "INDIVIDUAL", "roles": ["VP"]},
    ]


def _sample_relationships():
    return [
        {"source": "A1", "target": "A2", "relationship_type": "BOARD_INTERLOCK"},
        {"source": "A1", "target": "A3", "relationship_type": "BOARD_INTERLOCK"},
        {"source": "A2", "target": "A4", "relationship_type": "REPORTING"},
    ]


def _sample_violations():
    return [
        {"violation_type": "LATE_FORM_4", "severity": "CRITICAL",
         "description": "Form 4 filed 7 days late", "risk_level": "CRITICAL",
         "evidence_hash": hashlib.sha256(b"ev1").hexdigest(),
         "regulatory_citations": ["Exchange Act §16(a)"]},
        {"violation_type": "SHORT_SWING_PROFIT", "severity": "HIGH",
         "description": "Possible short-swing profit violation",
         "risk_level": "HIGH",
         "evidence_hash": hashlib.sha256(b"ev2").hexdigest(),
         "regulatory_citations": ["Exchange Act §16(b)"]},
        {"violation_type": "SAY_ON_PAY_FAILURE", "severity": "HIGH",
         "description": "Say-on-Pay failed with 45% approval",
         "risk_level": "HIGH",
         "evidence_hash": hashlib.sha256(b"ev3").hexdigest(),
         "regulatory_citations": ["Exchange Act Rule 14a-21"]},
        {"violation_type": "TEMPORAL_INCONSISTENCY", "severity": "MEDIUM",
         "description": "Revenue figures inconsistent between 10-Q filings",
         "risk_level": "MEDIUM",
         "evidence_hash": hashlib.sha256(b"ev4").hexdigest(),
         "regulatory_citations": ["SOX §302"]},
        {"violation_type": "DISCLOSURE_GAP", "severity": "LOW",
         "description": "Minor disclosure omission",
         "risk_level": "LOW",
         "evidence_hash": hashlib.sha256(b"ev5").hexdigest(),
         "regulatory_citations": ["Regulation S-K Item 402"]},
    ]


def _full_analysis_results():
    """Build a complete analysis_results dict for the visual dossier."""
    return {
        "total_violations": 5,
        "critical_alerts": 1,
        "high_alerts": 2,
        "violations": _sample_violations(),
        "transactions": _sample_transactions(),
        "beneficiaries": _sample_beneficiaries(),
        "filings": _sample_filings(),
        "actors": _sample_actors(),
        "relationships": _sample_relationships(),
        "material_events": [
            {"date": date(2019, 6, 27), "event_type": "EARNINGS_CALL",
             "description": "Q4 Earnings Call"},
        ],
        "annual_events": [
            {"date": date(2019, 5, 31), "event_type": "FISCAL_YEAR_END",
             "description": "FY2019 End"},
        ],
        "regulatory_routing": {"SEC": True, "DOJ": True, "IRS": False},
        "estimated_penalties": {
            "civil_minimum": 500000,
            "civil_maximum": 15000000,
            "disgorgement": 4500000,
            "criminal_exposure": True,
            "prison_years_maximum": 20,
        },
        "evidence_chain": [
            {"item_id": "EV-0001", "description": "Form 4 filing for John Parker",
             "sha256_hash": hashlib.sha256(b"chain1").hexdigest()},
            {"item_id": "EV-0002", "description": "DEF 14A proxy statement",
             "sha256_hash": hashlib.sha256(b"chain2").hexdigest()},
        ],
    }


# ─── BUBBLE CHART TESTS ─────────────────────────────────────────────────


class TestBubbleChartGenerator:
    def test_import(self):
        from src.reporting.visualizations.bubble_chart import BubbleChartGenerator
        gen = BubbleChartGenerator()
        assert gen is not None

    def test_generate_transaction_bubbles(self):
        from src.reporting.visualizations.bubble_chart import BubbleChartGenerator
        gen = BubbleChartGenerator()
        fig = gen.generate_transaction_bubbles(_sample_transactions())
        assert fig is not None
        assert hasattr(fig, "data")
        assert len(fig.data) > 0

    def test_generate_beneficiary_profit_bubbles(self):
        from src.reporting.visualizations.bubble_chart import BubbleChartGenerator
        gen = BubbleChartGenerator()
        fig = gen.generate_beneficiary_profit_bubbles(_sample_beneficiaries())
        assert fig is not None
        assert len(fig.data) > 0

    def test_empty_data_returns_figure(self):
        from src.reporting.visualizations.bubble_chart import BubbleChartGenerator
        gen = BubbleChartGenerator()
        fig = gen.generate_transaction_bubbles([])
        assert fig is not None


# ─── FILING DEADLINE CHART TESTS ─────────────────────────────────────────


class TestFilingDeadlineChart:
    def test_import(self):
        from src.reporting.visualizations.filing_deadline_chart import FilingDeadlineChart
        gen = FilingDeadlineChart()
        assert gen is not None

    def test_generate_deadline_chart(self):
        from src.reporting.visualizations.filing_deadline_chart import FilingDeadlineChart
        gen = FilingDeadlineChart()
        fig = gen.generate_deadline_chart(_sample_filings())
        assert fig is not None
        assert len(fig.data) > 0

    def test_generate_compliance_summary(self):
        from src.reporting.visualizations.filing_deadline_chart import FilingDeadlineChart
        gen = FilingDeadlineChart()
        fig = gen.generate_compliance_summary(_sample_filings())
        assert fig is not None

    def test_enrich_filings_calculates_status(self):
        from src.reporting.visualizations.filing_deadline_chart import FilingDeadlineChart
        gen = FilingDeadlineChart()
        enriched = gen._enrich_filings(_sample_filings())
        for f in enriched:
            assert "status" in f
            assert f["status"] in ("ON_TIME", "LATE", "UNKNOWN")

    def test_empty_data_returns_figure(self):
        from src.reporting.visualizations.filing_deadline_chart import FilingDeadlineChart
        gen = FilingDeadlineChart()
        fig = gen.generate_deadline_chart([])
        assert fig is not None


# ─── BENEFICIARY PROFIT CHART TESTS ─────────────────────────────────────


class TestBeneficiaryProfitChart:
    def test_import(self):
        from src.reporting.visualizations.beneficiary_profit_chart import BeneficiaryProfitChart
        gen = BeneficiaryProfitChart()
        assert gen is not None

    def test_generate_profit_waterfall(self):
        from src.reporting.visualizations.beneficiary_profit_chart import BeneficiaryProfitChart
        gen = BeneficiaryProfitChart()
        fig = gen.generate_profit_waterfall(_sample_beneficiaries())
        assert fig is not None
        assert len(fig.data) > 0

    def test_generate_role_distribution(self):
        from src.reporting.visualizations.beneficiary_profit_chart import BeneficiaryProfitChart
        gen = BeneficiaryProfitChart()
        fig = gen.generate_role_distribution(_sample_beneficiaries())
        assert fig is not None
        assert len(fig.data) > 0

    def test_generate_profit_risk_dashboard(self):
        from src.reporting.visualizations.beneficiary_profit_chart import BeneficiaryProfitChart
        gen = BeneficiaryProfitChart()
        fig = gen.generate_profit_risk_dashboard(_sample_beneficiaries())
        assert fig is not None

    def test_empty_data_returns_figure(self):
        from src.reporting.visualizations.beneficiary_profit_chart import BeneficiaryProfitChart
        gen = BeneficiaryProfitChart()
        fig = gen.generate_profit_waterfall([])
        assert fig is not None


# ─── VISUAL REPORT GENERATOR TESTS ──────────────────────────────────────


class TestForensicVisualReportGenerator:
    def test_import(self):
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        assert ForensicVisualReportGenerator is not None

    def test_instantiation(self, tmp_path):
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))
        assert gen is not None
        assert gen.output_dir == tmp_path

    def test_generate_visual_dossier_creates_pdf(self, tmp_path):
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))
        results = _full_analysis_results()

        output_path = gen.generate_visual_dossier(
            case_id="TEST-001",
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=results,
            output_filename="test_visual_dossier.pdf",
        )

        assert output_path.exists()
        assert output_path.suffix == ".pdf"
        assert output_path.stat().st_size > 0

    def test_generate_dossier_minimal_data(self, tmp_path):
        """Test with minimal analysis results (no transactions, beneficiaries, etc.)."""
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))

        minimal_results = {
            "total_violations": 0,
            "critical_alerts": 0,
            "high_alerts": 0,
            "violations": [],
            "estimated_penalties": {},
        }

        output_path = gen.generate_visual_dossier(
            case_id="MINIMAL-001",
            company_name="Test Corp",
            cik="999999",
            analysis_results=minimal_results,
            output_filename="test_minimal.pdf",
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_severity_breakdown_table(self, tmp_path):
        """Verify severity breakdown with violations of different severity levels."""
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))
        results = {"violations": _sample_violations()}
        story = gen._build_severity_breakdown(results)
        assert len(story) > 0

    def test_kpi_dashboard(self, tmp_path):
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))
        results = _full_analysis_results()
        story = gen._build_kpi_dashboard(results)
        assert len(story) > 0

    def test_extract_violations(self, tmp_path):
        from src.reporting.visual_report_generator import ForensicVisualReportGenerator
        gen = ForensicVisualReportGenerator(output_dir=str(tmp_path))
        results = _full_analysis_results()
        violations = gen._extract_violations(results)
        assert len(violations) == 5

    def test_reporting_init_exports_visual_generator(self):
        """Verify ForensicVisualReportGenerator is exported from reporting __init__."""
        from src.reporting import ForensicVisualReportGenerator
        assert ForensicVisualReportGenerator is not None


# ─── VISUALIZATIONS PACKAGE EXPORTS ─────────────────────────────────────


class TestVisualizationsExports:
    def test_bubble_chart_exported(self):
        from src.reporting.visualizations import BubbleChartGenerator
        assert BubbleChartGenerator is not None

    def test_filing_deadline_chart_exported(self):
        from src.reporting.visualizations import FilingDeadlineChart
        assert FilingDeadlineChart is not None

    def test_beneficiary_profit_chart_exported(self):
        from src.reporting.visualizations import BeneficiaryProfitChart
        assert BeneficiaryProfitChart is not None

    def test_existing_generators_still_exported(self):
        from src.reporting.visualizations import (
            TimelineGenerator,
            NetworkGraphGenerator,
            HeatMapGenerator,
            MerkleTreeVisualizer,
        )
        assert TimelineGenerator is not None
        assert NetworkGraphGenerator is not None
        assert HeatMapGenerator is not None
        assert MerkleTreeVisualizer is not None
