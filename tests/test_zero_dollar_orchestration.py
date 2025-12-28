#!/usr/bin/env python3
"""
Zero-Dollar Transaction Orchestration Integration Test
======================================================

Tests the complete JLAW forensic analysis pipeline including:
- Configuration
- Behavioral scoring
- Narrative generation
- Pipeline orchestration
- Forensic engine

This validates PR #8: Master Orchestration Engine & Prosecutorial Narrative Generation
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all new modules can be imported."""
    print("\n" + "=" * 70)
    print("TEST 1: Import Validation")
    print("=" * 70)
    
    try:
        # Test config imports
        from src.zero_dollar.config import JLAWConfig
        print("✓ JLAWConfig imports successfully")
        
        # Test behavioral scoring imports
        from src.zero_dollar.modules import BehavioralScoringEngine
        print("✓ BehavioralScoringEngine imports successfully")
        
        # Test narrative imports
        from src.zero_dollar.narrative import (
            ProsecutorialNarrativeGenerator,
            Citation,
            SECURITIES_CITATIONS,
            TAX_CITATIONS,
            ANTITRUST_CITATIONS,
            EVIDENCE_CITATIONS,
            get_citations_for_anomaly,
            get_citations_for_risk_tier,
        )
        print("✓ Narrative module imports successfully")
        
        # Test orchestration imports
        from src.zero_dollar.orchestration import (
            JLAWForensicEngine,
            PipelineExecutor,
            PipelineStage,
            StageStatus,
        )
        print("✓ Orchestration module imports successfully")
        
        # Test dossier imports
        from src.zero_dollar.models import (
            ProsecutorialNarrative,
            ForensicDossier,
        )
        print("✓ Dossier models import successfully")
        
        # Test package-level imports
        from src.zero_dollar import (
            JLAWConfig,
            JLAWForensicEngine,
            ProsecutorialNarrativeGenerator,
            BehavioralScoringEngine,
            ForensicDossier,
        )
        print("✓ Package-level imports work correctly")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_initialization():
    """Test JLAWConfig initialization and validation."""
    print("\n" + "=" * 70)
    print("TEST 2: Configuration Initialization")
    print("=" * 70)
    
    try:
        from src.zero_dollar.config import JLAWConfig
        from pathlib import Path
        
        # Test default config
        config = JLAWConfig()
        print(f"✓ Default config created")
        print(f"  - SEC User-Agent: {config.sec_user_agent}")
        print(f"  - Output Directory: {config.output_directory}")
        print(f"  - Rate Limit: {config.rate_limit_requests_per_second}/sec")
        print(f"  - Parallel Execution: {config.parallel_execution}")
        
        # Test custom config
        custom_config = JLAWConfig(
            sec_user_agent="Test Agent test@example.com",
            output_directory=Path("/tmp/jlaw_test"),
            parallel_execution=False,
        )
        print(f"✓ Custom config created")
        print(f"  - Parallel Execution: {custom_config.parallel_execution}")
        
        # Test config validation
        try:
            invalid_config = JLAWConfig(rate_limit_requests_per_second=15)
            print(f"✗ Should have rejected rate limit > 10")
            return False
        except ValueError:
            print(f"✓ Config validation works (rejected rate limit > 10)")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_citation_matrix():
    """Test regulatory citation matrix."""
    print("\n" + "=" * 70)
    print("TEST 3: Citation Matrix")
    print("=" * 70)
    
    try:
        from src.zero_dollar.narrative import (
            SECURITIES_CITATIONS,
            TAX_CITATIONS,
            ANTITRUST_CITATIONS,
            EVIDENCE_CITATIONS,
            get_citations_for_anomaly,
            get_citations_for_risk_tier,
        )
        
        # Test securities citations
        print(f"✓ Securities citations loaded: {len(SECURITIES_CITATIONS)} citations")
        assert "10b-5" in SECURITIES_CITATIONS
        assert "section-16a" in SECURITIES_CITATIONS
        print(f"  - Rule 10b-5: {SECURITIES_CITATIONS['10b-5'].title}")
        
        # Test tax citations
        print(f"✓ Tax citations loaded: {len(TAX_CITATIONS)} citations")
        assert "7201" in TAX_CITATIONS
        assert "section-83" in TAX_CITATIONS
        print(f"  - IRC § 83: {TAX_CITATIONS['section-83'].title}")
        
        # Test antitrust citations
        print(f"✓ Antitrust citations loaded: {len(ANTITRUST_CITATIONS)} citations")
        assert "hsr-act" in ANTITRUST_CITATIONS
        
        # Test evidence citations
        print(f"✓ Evidence citations loaded: {len(EVIDENCE_CITATIONS)} citations")
        assert "fre-902-13" in EVIDENCE_CITATIONS
        assert "fre-902-14" in EVIDENCE_CITATIONS
        
        # Test citation retrieval functions
        temporal_citations = get_citations_for_anomaly("TEMPORAL_CLUSTERING")
        print(f"✓ Temporal clustering citations: {len(temporal_citations)} citations")
        
        critical_citations = get_citations_for_risk_tier("CRITICAL")
        print(f"✓ Critical risk citations: {len(critical_citations)} citations")
        
        return True
    except Exception as e:
        print(f"✗ Citation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_behavioral_scoring():
    """Test behavioral scoring engine."""
    print("\n" + "=" * 70)
    print("TEST 4: Behavioral Scoring Engine")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules import (
            BehavioralScoringEngine,
            TemporalClusteringOutput,
        )
        from src.zero_dollar.models import (
            Transaction,
            EventProximityFlag,
            OwnershipChain,
            OwnershipNode,
            EntityType,
            MaterialEvent,
        )
        from decimal import Decimal
        
        # Create test data
        transactions = [
            Transaction(
                accession_number="0000320187-20-000001",
                issuer_cik="0000320187",
                issuer_name="Test Company",
                reporting_person_cik="0001234567",
                reporting_person_name="John Doe",
                transaction_date=date(2020, 1, 10),
                filing_date=date(2020, 1, 15),
                transaction_code="P",
                shares=Decimal("100000"),
                price_per_share=None,  # Zero-dollar
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("500000"),
                direct_indirect="I",
                nature_of_ownership="By Trust",
            )
        ]
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            clusters_detected=[],
            total_anomaly_score=Decimal("0"),
            escalation_recommendation="NONE",
        )
        
        event_flags = []
        
        ownership_chain = OwnershipChain(
            chain_id="CHAIN-001",
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            nodes=[
                OwnershipNode(
                    node_id="NODE-001", entity_name="John Doe",
                    entity_type=EntityType.RLT, ownership_percentage=100.0,
                    
                )
            ],
            total_depth=1,
            effective_ownership=100.0,
        )
        
        # Create scoring engine
        engine = BehavioralScoringEngine()
        
        # Calculate assessment
        assessment = engine.calculate_assessment(
            reporting_person_cik="0001234567",
            reporting_person_name="John Doe",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            transactions=transactions,
            temporal_output=temporal_output,
            event_flags=event_flags,
            ownership_chain=ownership_chain,
        )
        
        print(f"✓ Behavioral assessment calculated")
        print(f"  - Risk Score: {assessment.risk_score:.1f}/100")
        print(f"  - Risk Level: {assessment.risk_level}")
        print(f"  - Priority: {assessment.prosecutorial_priority}")
        print(f"  - Zero-Dollar Transactions: {assessment.zero_dollar_transaction_count}")
        
        # Validate assessment structure
        assert assessment.risk_score >= 0
        assert assessment.risk_level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
        assert 1 <= assessment.prosecutorial_priority <= 5
        print(f"✓ Assessment structure validated")
        
        return True
    except Exception as e:
        print(f"✗ Behavioral scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_narrative_generation():
    """Test prosecutorial narrative generation."""
    print("\n" + "=" * 70)
    print("TEST 5: Narrative Generation")
    print("=" * 70)
    
    try:
        from src.zero_dollar.narrative import ProsecutorialNarrativeGenerator
        from src.zero_dollar.config import JLAWConfig
        from src.zero_dollar.models import (
            Transaction,
            BehavioralRiskAssessment,
            BehavioralScoreComponents,
            EventProximityFlag,
            OwnershipChain,
            OwnershipNode,
            EntityType,
        )
        from src.zero_dollar.modules import TemporalClusteringOutput
        from decimal import Decimal
        
        # Create test data
        config = JLAWConfig()
        generator = ProsecutorialNarrativeGenerator(config)
        
        score_components = BehavioralScoreComponents(
            magnitude_score=15.0,
            frequency_score=10.0,
            timing_score=5.0,
            filing_compliance_score=0.0,
            entity_complexity_score=5.0,
        )
        
        assessment = BehavioralRiskAssessment(
            assessment_id="TEST-001",
            reporting_person_cik="0001234567",
            reporting_person_name="John Doe",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            assessment_date=datetime.utcnow(),
            score_components=score_components,
            zero_dollar_transaction_count=1,
            total_transaction_count=5,
            temporal_clusters_detected=0,
            prosecutorial_priority=3,
            recommendation="Continue monitoring",
        )
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            clusters_detected=[],
            total_anomaly_score=Decimal("0"),
            escalation_recommendation="NONE",
        )
        
        ownership_chain = OwnershipChain(
            chain_id="CHAIN-002",
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            nodes=[
                OwnershipNode(
                    node_id="NODE-001", entity_name="John Doe",
                    entity_type=EntityType.RLT, ownership_percentage=100.0,
                    
                )
            ],
            total_depth=1,
            effective_ownership=100.0,
        )
        
        transactions = [
            Transaction(
                accession_number="0000320187-20-000001",
                issuer_cik="0000320187",
                issuer_name="Test Company",
                reporting_person_cik="0001234567",
                reporting_person_name="John Doe",
                transaction_date=date(2020, 1, 10),
                filing_date=date(2020, 1, 15),
                transaction_code="P",
                shares=Decimal("100000"),
                price_per_share=None,
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("500000"),
                direct_indirect="I",
                nature_of_ownership="By Trust",
            )
        ]
        
        # Generate narrative
        narrative = generator.generate(
            assessment=assessment,
            temporal=temporal_output,
            events=[],
            ownership=ownership_chain,
            transactions=transactions,
        )
        
        print(f"✓ Narrative generated: {narrative.narrative_id}")
        print(f"  - Case ID: {narrative.case_id}")
        print(f"  - Citations: {len(narrative.regulatory_citations)}")
        
        # Validate narrative structure
        assert narrative.subject_identification
        assert narrative.factual_summary
        assert narrative.anomaly_analysis
        assert narrative.violation_analysis
        assert narrative.damage_estimation
        assert narrative.enforcement_recommendation
        assert narrative.evidence_summary
        print(f"✓ Narrative has all 7 required sections")
        
        # Test markdown export
        markdown = narrative.to_markdown()
        assert "# PROSECUTORIAL NARRATIVE" in markdown
        assert "## 1. SUBJECT IDENTIFICATION" in markdown
        assert "## 2. FACTUAL SUMMARY" in markdown
        print(f"✓ Markdown export working")
        print(f"  - Length: {len(markdown)} characters")
        
        return True
    except Exception as e:
        print(f"✗ Narrative generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_orchestration():
    """Test pipeline execution coordinator."""
    print("\n" + "=" * 70)
    print("TEST 6: Pipeline Orchestration")
    print("=" * 70)
    
    try:
        from src.zero_dollar.orchestration import (
            PipelineExecutor,
            PipelineStage,
            StageStatus,
        )
        
        # Create pipeline executor
        pipeline = PipelineExecutor(issuer_cik="0000320187")
        print(f"✓ Pipeline executor created")
        
        # Test stage execution
        pipeline.start_stage(PipelineStage.ACQUISITION)
        print(f"✓ Started ACQUISITION stage")
        
        pipeline.complete_stage(
            PipelineStage.ACQUISITION,
            data={'filing_count': 10}
        )
        print(f"✓ Completed ACQUISITION stage")
        
        # Test stage status
        result = pipeline.state.get_stage_result(PipelineStage.ACQUISITION)
        assert result is not None
        assert result.status == StageStatus.COMPLETED
        assert result.data['filing_count'] == 10
        print(f"✓ Stage result retrieved correctly")
        
        # Test progress tracking
        progress = pipeline.state.progress_percentage
        print(f"✓ Progress tracking: {progress:.1f}%")
        
        # Test pipeline summary
        summary = pipeline.get_summary()
        assert "Pipeline Execution Summary" in summary
        print(f"✓ Pipeline summary generated")
        
        return True
    except Exception as e:
        print(f"✗ Pipeline orchestration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dossier_export():
    """Test forensic dossier export functionality."""
    print("\n" + "=" * 70)
    print("TEST 7: Dossier Export")
    print("=" * 70)
    
    try:
        from src.zero_dollar.models import (
            ForensicDossier,
            ProsecutorialNarrative,
            BehavioralRiskAssessment,
            BehavioralScoreComponents,
            OwnershipChain,
            OwnershipNode,
            EntityType,
        )
        from src.zero_dollar.modules import TemporalClusteringOutput
        from decimal import Decimal
        import tempfile
        import json
        
        # Create test dossier
        score_components = BehavioralScoreComponents(
            magnitude_score=15.0,
            frequency_score=10.0,
            timing_score=5.0,
            filing_compliance_score=0.0,
            entity_complexity_score=5.0,
        )
        
        assessment = BehavioralRiskAssessment(
            assessment_id="TEST-DOSSIER-001",
            reporting_person_cik="0001234567",
            reporting_person_name="John Doe",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            assessment_date=datetime.utcnow(),
            score_components=score_components,
            zero_dollar_transaction_count=1,
            total_transaction_count=5,
            temporal_clusters_detected=0,
            prosecutorial_priority=3,
            recommendation="Continue monitoring",
        )
        
        narrative = ProsecutorialNarrative(
            narrative_id="NARRATIVE-001",
            case_id="TEST-DOSSIER-001",
            generated_timestamp=datetime.utcnow(),
            subject_identification="Test subject",
            factual_summary="Test summary",
            anomaly_analysis="Test analysis",
            violation_analysis="Test violations",
            damage_estimation="Test damages",
            enforcement_recommendation="Test recommendation",
            evidence_summary="Test evidence",
        )
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            clusters_detected=[],
            total_anomaly_score=Decimal("0"),
            escalation_recommendation="NONE",
        )
        
        ownership_chain = OwnershipChain(
            chain_id="CHAIN-003",
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            nodes=[
                OwnershipNode(
                    node_id="NODE-001", entity_name="John Doe",
                    entity_type=EntityType.RLT, ownership_percentage=100.0,
                    
                )
            ],
            total_depth=1,
            effective_ownership=100.0,
        )
        
        dossier = ForensicDossier(
            case_id="TEST-DOSSIER-001",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            issuer_ticker="TST",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            total_transactions_analyzed=5,
            zero_dollar_transactions=1,
            temporal_analysis=temporal_output,
            event_proximity_analysis=[],
            ownership_chain_analysis=ownership_chain,
            risk_assessment=assessment,
            prosecutorial_narrative=narrative,
            merkle_root_hash="0" * 64,
        )
        
        print(f"✓ Dossier created: {dossier.case_id}")
        
        # Test JSON export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = Path(f.name)
        
        dossier.export_json(json_path)
        assert json_path.exists()
        
        # Validate JSON content
        with open(json_path, 'r') as f:
            json_data = json.load(f)
            assert json_data['case_id'] == "TEST-DOSSIER-001"
            assert json_data['issuer_name'] == "Test Company"
        
        print(f"✓ JSON export successful: {json_path}")
        json_path.unlink()  # Clean up
        
        # Test Markdown export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            md_path = Path(f.name)
        
        dossier.export_markdown(md_path)
        assert md_path.exists()
        
        # Validate Markdown content
        with open(md_path, 'r') as f:
            md_content = f.read()
            assert "# FORENSIC DOSSIER" in md_content
            assert "Test Company" in md_content
        
        print(f"✓ Markdown export successful: {md_path}")
        md_path.unlink()  # Clean up
        
        # Test evidence package export
        with tempfile.TemporaryDirectory() as tmpdir:
            package_path = Path(tmpdir) / "evidence_package"
            dossier.export_evidence_package(package_path)
            
            assert (package_path / "dossier.json").exists()
            assert (package_path / "narrative.md").exists()
            assert (package_path / "evidence_integrity.txt").exists()
            assert (package_path / "temporal_analysis.json").exists()
            assert (package_path / "event_proximity.json").exists()
            assert (package_path / "ownership_chain.json").exists()
            assert (package_path / "risk_assessment.json").exists()
            
            print(f"✓ Evidence package export successful")
        
        return True
    except Exception as e:
        print(f"✗ Dossier export test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("JLAW ORCHESTRATION ENGINE INTEGRATION TEST SUITE")
    print("PR #8: Master Orchestration Engine & Prosecutorial Narrative Generation")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config_initialization),
        ("Citation Matrix", test_citation_matrix),
        ("Behavioral Scoring", test_behavioral_scoring),
        ("Narrative Generation", test_narrative_generation),
        ("Pipeline Orchestration", test_pipeline_orchestration),
        ("Dossier Export", test_dossier_export),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! PR #8 implementation is complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
