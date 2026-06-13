from src.claim_verification.evidence_matcher import match_claim_to_evidence


def test_matcher_returns_conservative_relationships() -> None:
    claim = {
        "claim_text": "We maintain a safe workplace with strong guarding controls.",
        "claim_type": "safety claim",
        "corporate_speaker": "Example Fabrication",
    }
    records = [
        {
            "evidence_id": "OSHA-1",
            "title": "Inspection summary",
            "source_type": "osha log",
            "file_path": "inspection.txt",
            "legal_domain": "safety",
            "related_entities": ["Example Fabrication"],
        }
    ]
    texts = {
        "inspection.txt": "Inspectors found the company did not maintain guarding and issued a hazard citation.",
    }

    matches = match_claim_to_evidence(claim, records, texts)

    assert matches[0].relationship == "contradicts"
    assert matches[0].relationship_score <= 3
