"""
Post-install verification matrix for JLAW (CPU-friendly, Windows-ready).

- Imports core and optional stacks and records pass/fail/WARN statuses
- Prints a compact console matrix
- Writes JSON to forensic_storage/install/post_install_report.json
- Exit code: 0 if all core checks pass; 1 if any core check fails

Run:
  python scripts/post_install_verify.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
import os
from typing import Callable, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


@dataclass
class CheckResult:
    name: str
    ok: bool
    warn: bool = False
    error: Optional[str] = None

    def status(self) -> str:
        if self.ok:
            return "OK"
        if self.warn:
            return "WARN"
        return "FAIL"


def _try(check_name: str, fn: Callable[[], None], warn_only: bool = False) -> CheckResult:
    try:
        fn()
        return CheckResult(name=check_name, ok=True)
    except Exception as e:
        if warn_only:
            return CheckResult(name=check_name, ok=False, warn=True, error=str(e))
        return CheckResult(name=check_name, ok=False, warn=False, error=str(e))


def _import(module_name: str):
    __import__(module_name)


def _spacy_model_check():
    # Lazy import via __import__ to avoid static import errors on systems without spaCy
    spacy = __import__("spacy")
    try:
        spacy.load("en_core_web_trf")
    except Exception:
        # Fallback to small model; if unavailable, raise so core fails visibly
        spacy.load("en_core_web_sm")


def _weasyprint_check():
    # Import only; Windows may need GTK runtime but import should work
    __import__("weasyprint")


def main() -> int:
    results: Dict[str, List[CheckResult]] = {"core": [], "optional": []}

    # -----------------
    # Core dependencies
    # -----------------
    core_checks: List[Callable[[], CheckResult]] = [
        lambda: _try("PyMuPDF (fitz)", lambda: _import("fitz")),
        lambda: _try("pdfplumber", lambda: _import("pdfplumber")),
        lambda: _try("BeautifulSoup4", lambda: _import("bs4")),
        lambda: _try("lxml", lambda: _import("lxml")),
        lambda: _try("spaCy + model", _spacy_model_check),
        lambda: _try("transformers", lambda: _import("transformers")),
        lambda: _try("torch", lambda: _import("torch")),
        lambda: _try("scikit-learn", lambda: _import("sklearn")),
        lambda: _try("jinja2", lambda: _import("jinja2")),
        lambda: _try("reportlab", lambda: _import("reportlab")),
        # Project modules (must import)
        lambda: _try("src.forensics (package)", lambda: _import("src.forensics")),
        lambda: _try("UniversalDocumentProcessor", lambda: __import__(
            "src.forensics.enhanced_parsing", fromlist=["UniversalDocumentProcessor"]
        )),
        lambda: _try("SystemHealthCheck", lambda: __import__(
            "src.forensics.deployment", fromlist=["SystemHealthCheck"]
        )),
    ]

    # --------------------
    # Optional dependencies
    # --------------------
    optional_checks: List[Callable[[], CheckResult]] = [
        lambda: _try("pytesseract", lambda: _import("pytesseract"), warn_only=True),
        lambda: _try("Pillow", lambda: _import("PIL"), warn_only=True),
        lambda: _try("python-magic", lambda: _import("magic"), warn_only=True),
        lambda: _try("chardet", lambda: _import("chardet"), warn_only=True),
        # OCR engines
        lambda: _try("PaddleOCR", lambda: _import("paddleocr"), warn_only=True),
        lambda: _try("EasyOCR", lambda: _import("easyocr"), warn_only=True),
        lambda: _try("DocTR", lambda: _import("doctr"), warn_only=True),
        # NLP / ML extras
        lambda: _try("sentence-transformers", lambda: _import("sentence_transformers"), warn_only=True),
        lambda: _try("torch-geometric", lambda: _import("torch_geometric"), warn_only=True),
        lambda: _try("networkx", lambda: _import("networkx"), warn_only=True),
        # Legal / data backends
        lambda: _try("neo4j", lambda: _import("neo4j"), warn_only=True),
        lambda: _try("elasticsearch", lambda: _import("elasticsearch"), warn_only=True),
        # Anthropic SDK and analyzers
        lambda: _try("anthropic (SDK)", lambda: _import("anthropic"), warn_only=True),
        lambda: _try(
            "AnthropicAgentAnalyzer (init)",
            lambda: __import__(
                "src.forensics.anthropic_agent_analyzer", fromlist=["AnthropicAgentAnalyzer"]
            ).AnthropicAgentAnalyzer() if os.getenv("ANTHROPIC_API_KEY") else (_ for _ in ()).throw(Exception("ANTHROPIC_API_KEY not set")),
            warn_only=True,
        ),
        lambda: _try(
            "DualAgentCoordinator (import)",
            lambda: __import__("src.forensics.dual_agent", fromlist=["DualAgentCoordinator"]),
            warn_only=True,
        ),
        # Reporting extras
        lambda: _try("WeasyPrint", _weasyprint_check, warn_only=True),
        lambda: _try("plotly", lambda: _import("plotly"), warn_only=True),
        # Orchestration / messaging
        lambda: _try("pika", lambda: _import("pika"), warn_only=True),
        lambda: _try("structlog", lambda: _import("structlog"), warn_only=True),
        lambda: _try("prometheus-client", lambda: _import("prometheus_client"), warn_only=True),
        lambda: _try("asyncpg", lambda: _import("asyncpg"), warn_only=True),
        lambda: _try("aioredis", lambda: _import("aioredis"), warn_only=True),
        lambda: _try("dagster", lambda: _import("dagster"), warn_only=True),
    ]

    for chk in core_checks:
        results["core"].append(chk())
    for chk in optional_checks:
        results["optional"].append(chk())

    # Console output
    print("\nJLAW Post-Install Verification Matrix")
    print("=" * 60)
    print("Core components:")
    for r in results["core"]:
        print(f"  [{r.status():>4}] {r.name}" + (f"  - {r.error}" if r.error and not r.ok else ""))
    print("\nOptional components:")
    for r in results["optional"]:
        label = r.status()
        print(f"  [{label:>4}] {r.name}" + (f"  - {r.error}" if r.error and not r.ok and not r.warn else ""))
    print("=" * 60)

    # Write JSON report
    out_dir = REPO / "forensic_storage" / "install"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "post_install_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "core": [asdict(r) for r in results["core"]],
                "optional": [asdict(r) for r in results["optional"]],
            },
            f,
            indent=2,
        )
    print(f"Report written: {out_path}")

    # Exit policy
    failed_core = [r for r in results["core"] if not r.ok]
    return 0 if not failed_core else 1


if __name__ == "__main__":
    raise SystemExit(main())
