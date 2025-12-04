"""
Prosecution Report Generator - Phase 7
======================================
Generates legal/regulatory reports (HTML/PDF-ready) using Jinja2 templates.
This is a research-friendly scaffold with minimal dependencies and graceful
fallbacks when optional libraries are missing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProsecutionPackage:
    path: Path
    html_file: Optional[Path]
    pdf_file: Optional[Path]


class ProsecutionReportGenerator:
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = Path(templates_dir) if templates_dir else None
        self._env = None
        if self.templates_dir and self.templates_dir.exists():
            try:
                from jinja2 import Environment, FileSystemLoader  # type: ignore
                self._env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
            except Exception as e:
                logger.debug("Jinja2 unavailable: %s", e)
                self._env = None
        logger.info("✅ ProsecutionReportGenerator initialized")

    def _render_html(self, template_name: str, context: Dict[str, Any]) -> str:
        if self._env:
            try:
                template = self._env.get_template(template_name)
                return template.render(**context)
            except Exception as e:
                logger.debug("Template render failed: %s", e)
        # Fallback basic HTML
        return f"""
        <html><head><meta charset='utf-8'><title>Prosecution Report</title></head>
        <body>
          <h1>Prosecution Report</h1>
          <pre>{self._safe_pre(context)}</pre>
        </body></html>
        """

    def _safe_pre(self, obj: Any) -> str:
        try:
            import json
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except Exception:
            return str(obj)

    def generate(self, output_dir: str, data: Dict[str, Any], template: str = "prosecution_report.html") -> ProsecutionPackage:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        html_content = self._render_html(template, data)
        html_path = out / "report.html"
        html_path.write_text(html_content, encoding='utf-8')

        # Optional PDF using WeasyPrint if available
        pdf_path: Optional[Path] = None
        try:
            from weasyprint import HTML  # type: ignore
            pdf_path = out / "report.pdf"
            HTML(string=html_content).write_pdf(str(pdf_path))
        except Exception as e:
            logger.debug("PDF generation skipped/unavailable: %s", e)
            pdf_path = None

        logger.info("📝 Report generated at %s", str(out))
        return ProsecutionPackage(path=out, html_file=html_path, pdf_file=pdf_path)
