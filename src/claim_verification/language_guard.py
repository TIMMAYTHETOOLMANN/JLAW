"""Defamation and overstatement guard for generated claim-verification language."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

PROHIBITED_TERMS = {
    "fraud": "raises questions",
    "criminal": "potential regulatory exposure",
    "conspiracy": "requires independent verification",
    "guilty": "not established by the available record",
    "illegal": "potentially non-compliant",
    "proven": "not yet established",
    "confirmed wrongdoing": "available evidence does not yet establish",
    "corrupt": "appears inconsistent with stated controls",
    "cover-up": "requires independent verification",
    "insider trading": "potential insider-transaction concern",
    "securities fraud": "potential securities-law exposure",
    "environmental crime": "potential environmental compliance issue",
    "forced labor": "human-rights issue requiring verification",
}
ALLOWED_CONTEXT_HINTS = (
    "alleged",
    "potential",
    "requires investigation",
    "requires independent verification",
    "official finding",
    "agency finding",
    "statute",
    "regulatory classification",
)


@dataclass(frozen=True)
class LanguageFlag:
    """One high-risk language finding."""

    term: str
    field_name: str
    message: str
    replacement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LanguageGuardResult:
    """Scan result for generated language."""

    flags: list[LanguageFlag]
    sanitized_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "flags": [flag.to_dict() for flag in self.flags],
            "sanitized_text": self.sanitized_text,
        }


def _allowed_usage(text: str, field_name: str, term: str) -> bool:
    if "classification" in field_name or "claim_type" in field_name:
        return True
    lowered = text.lower()
    index = lowered.find(term)
    if index == -1:
        return False
    start = max(0, index - 40)
    end = min(len(lowered), index + len(term) + 40)
    context = lowered[start:end]
    return any(hint in context for hint in ALLOWED_CONTEXT_HINTS)


def scan_text(text: str, field_name: str = "narrative") -> LanguageGuardResult:
    """Scan one string for high-risk or overstated language."""
    flags: list[LanguageFlag] = []
    for term, replacement in PROHIBITED_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE) and not _allowed_usage(text, field_name, term):
            flags.append(
                LanguageFlag(
                    term=term,
                    field_name=field_name,
                    message=f"Avoid overstated term: {term}",
                    replacement=replacement,
                )
            )
    sanitized = sanitize_text(text)
    return LanguageGuardResult(flags=flags, sanitized_text=sanitized)


def sanitize_text(text: str) -> str:
    """Replace prohibited terms with safer wording."""
    sanitized = text
    for term, replacement in PROHIBITED_TERMS.items():
        sanitized = re.sub(rf"\b{re.escape(term)}\b", replacement, sanitized, flags=re.IGNORECASE)
    return sanitized


def guard_payload(payload: Any, prefix: str = "payload") -> tuple[Any, list[dict[str, Any]]]:
    """Recursively sanitize and scan string content within a payload."""
    flags: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            sanitized_value, nested_flags = guard_payload(value, f"{prefix}.{key}")
            sanitized[key] = sanitized_value
            flags.extend(nested_flags)
        return sanitized, flags
    if isinstance(payload, list):
        sanitized_list = []
        for index, value in enumerate(payload):
            sanitized_value, nested_flags = guard_payload(value, f"{prefix}[{index}]")
            sanitized_list.append(sanitized_value)
            flags.extend(nested_flags)
        return sanitized_list, flags
    if isinstance(payload, str):
        result = scan_text(payload, field_name=prefix)
        flags.extend(flag.to_dict() for flag in result.flags)
        return result.sanitized_text, flags
    return payload, flags
