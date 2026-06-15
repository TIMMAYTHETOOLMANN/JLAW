from src.claim_verification.language_guard import sanitize_text, scan_text


def test_language_guard_flags_prohibited_terms() -> None:
    result = scan_text("This proves fraud and a cover-up.")

    assert len(result.flags) == 2
    assert "raises questions" in result.sanitized_text
    assert "requires independent verification" in result.sanitized_text


def test_language_guard_allows_qualified_usage() -> None:
    result = scan_text("This is a potential securities fraud theory that requires investigation.")

    assert result.flags == []


def test_safe_wording_replacements_generated() -> None:
    sanitized = sanitize_text("illegal and criminal conduct")

    assert "potentially non-compliant" in sanitized
    assert "potential regulatory exposure" in sanitized
