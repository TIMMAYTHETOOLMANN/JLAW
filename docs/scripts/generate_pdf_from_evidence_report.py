"""
Generate Comprehensive PDF from Evidence-Backed Nike 2019 Report
================================================================

Utility script that converts the enhanced evidence‑backed text report
produced by `nike_2019_evidence_backed_analysis.py` into a comprehensive
PDF using the project's `PDFReportGenerator`. If ReportLab is not
installed, an HTML fallback is generated instead.

Usage:
    python docs/scripts/generate_pdf_from_evidence_report.py

Outputs:
    - forensic_reports/nike_2019/enhanced_evidence_backed_report_<timestamp>.pdf
      or (fallback)
    - forensic_reports/nike_2019/enhanced_evidence_backed_report_<timestamp>.html
"""

from __future__ import annotations

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.forensics.reporting.pdf_generator import PDFReportGenerator, ReportSection


def _find_latest_evidence_report() -> Path:
    candidates = sorted(REPO_ROOT.glob("EVIDENCE_BACKED_FORENSIC_REPORT_Nike_Inc_*.txt"))
    if not candidates:
        raise FileNotFoundError(
            "No evidence‑backed report found. Run `python nike_2019_evidence_backed_analysis.py` first."
        )
    return candidates[-1]


def _split_into_sections(text: str) -> List[ReportSection]:
    # Known headings in the evidence‑backed report
    h_evidence = "EVIDENCE QUALITY STANDARDS"
    h_vtypes = "VIOLATIONS BY TYPE"
    h_perfiling = "PER-FILING DETAILED ANALYSIS"

    def idx(h: str) -> int:
        return text.find(h)

    i_evidence = idx(h_evidence)
    i_vtypes = idx(h_vtypes)
    i_perfiling = idx(h_perfiling)

    # Executive summary is everything before evidence standards or whole text if not found
    exec_end = i_evidence if i_evidence != -1 else (i_vtypes if i_vtypes != -1 else (i_perfiling if i_perfiling != -1 else len(text)))
    executive = text[:exec_end].strip()

    evidence = text[i_evidence:i_vtypes].strip() if (i_evidence != -1 and i_vtypes != -1) else ""
    vtypes = text[i_vtypes:i_perfiling].strip() if (i_vtypes != -1 and i_perfiling != -1) else ""
    profiling = text[i_perfiling:].strip() if i_perfiling != -1 else ""

    sections: List[ReportSection] = []
    if executive:
        sections.append(ReportSection(section_id="executive_summary", title="Executive Summary", content=executive))
    if evidence:
        sections.append(ReportSection(section_id="evidence_standards", title="Evidence Quality Standards", content=evidence))
    if vtypes:
        sections.append(ReportSection(section_id="violations_by_type", title="Violations by Type", content=vtypes))
    if profiling:
        sections.append(ReportSection(section_id="per_filing_analysis", title="Per‑Filing Detailed Analysis", content=profiling))

    # If we failed to parse, just return the whole text as a single section
    if not sections:
        sections.append(ReportSection(section_id="full_report", title="Nike 2019 Evidence‑Backed Report", content=text))

    return sections


def _extract_metadata(executive_text: str) -> dict:
    md = {}
    # Basic fields
    m_company = re.search(r"Target Company:\s*(.+?)\s*\(CIK: (\d+)\)", executive_text)
    if m_company:
        md["Company"] = m_company.group(1).strip()
        md["CIK"] = m_company.group(2).strip()

    m_period = re.search(r"Analysis Period:\s*([^\n]+)", executive_text)
    if m_period:
        md["Analysis Period"] = m_period.group(1).strip()

    m_total = re.search(r"Total Filings Collected:\s*(\d+)", executive_text)
    if m_total:
        md["Total Filings Collected"] = m_total.group(1)

    m_v = re.search(r"Total Violations Detected:\s*(\d+)", executive_text)
    if m_v:
        md["Total Violations Detected"] = m_v.group(1)

    m_ev = re.search(r"Evidence-Backed Violations:\s*(\d+)", executive_text)
    if m_ev:
        md["Evidence‑Backed Violations"] = m_ev.group(1)

    m_dam = re.search(r"Estimated Total Damages:\s*\$([\d,\.]+)", executive_text)
    if m_dam:
        md["Estimated Total Damages"] = f"${m_dam.group(1)}"

    md["Generated From"] = "EVIDENCE_BACKED_FORENSIC_REPORT_Nike_Inc_*.txt"
    return md


def main() -> None:
    report_path = _find_latest_evidence_report()
    text = report_path.read_text(encoding="utf-8")

    sections = _split_into_sections(text)
    # Best‑effort metadata from executive summary
    executive_text = sections[0].content if sections else text
    metadata = _extract_metadata(executive_text)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = REPO_ROOT / "forensic_reports" / "nike_2019"
    out_dir.mkdir(parents=True, exist_ok=True)

    title = "NIKE INC. (NKE) — 2019 SEC Filings Enhanced Evidence‑Backed Report"
    case_number = f"NIKE_2019_ENHANCED_{ts}"

    generator = PDFReportGenerator()

    # Try to detect ReportLab availability before deciding on extension
    try:
        import reportlab  # type: ignore
        pdf_output = out_dir / f"enhanced_evidence_backed_report_{ts}.pdf"
        generator.generate_report(
            title=title,
            case_number=case_number,
            sections=sections,
            metadata=metadata,
            output_path=str(pdf_output)
        )
        print(f"✓ PDF saved to: {pdf_output}")
    except Exception:
        # Fallback to HTML if ReportLab unavailable
        html_bytes = generator.generate_report(
            title=title,
            case_number=case_number,
            sections=sections,
            metadata=metadata,
            output_path=None,
        )
        html_output = out_dir / f"enhanced_evidence_backed_report_{ts}.html"
        html_output.write_bytes(html_bytes)
        print("⚠️ ReportLab not available — HTML fallback generated.")
        print(f"✓ HTML saved to: {html_output}")
        print("You can convert the HTML to PDF with:")
        print(f"  wkhtmltopdf \"{html_output}\" \"{html_output.with_suffix('.pdf')}\"")


if __name__ == "__main__":
    main()
