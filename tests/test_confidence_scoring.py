from src.claim_verification.confidence_scoring import score_claim_verification


def test_confidence_scoring_does_not_overscore_weak_evidence() -> None:
    claim = {"claim_text": "We are committed to sustainability.", "claim_date": "2025-01-01"}
    matches = [
        {
            "evidence_id": "LEAD-1",
            "relationship": "requires verification",
            "evidence_classification": "unverified lead",
            "direct_textual_alignment": False,
        }
    ]

    assessment = score_claim_verification(claim, matches)

    assert assessment.score == 2
    assert assessment.safe_wording_level.startswith("LEVEL 2")
    assert "investigative lead requiring verification" in assessment.safe_report_language
