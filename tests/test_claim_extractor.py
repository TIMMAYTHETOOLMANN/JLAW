from src.claim_verification.claim_extractor import extract_claims_from_text


def test_extracts_dummy_esg_and_safety_claims() -> None:
    metadata = {
        "title": "Dummy Sustainability Report",
        "company_name": "Example Fabrication",
        "corporate_speaker": "Example Fabrication",
        "filing_type": "ESG Report",
        "public_statement_context": "Annual report",
        "date_created": "2025-01-01",
    }
    text = (
        "We are committed to worker safety in every facility. "
        "Our sustainability program uses recycled materials and zero waste practices."
    )

    claims = extract_claims_from_text(text, metadata, source_file="dummy.txt")

    assert len(claims) == 2
    assert {claim.claim_type for claim in claims} == {"safety claim", "waste/recycling claim"}
    assert all(claim.extraction_confidence >= 3 for claim in claims)
