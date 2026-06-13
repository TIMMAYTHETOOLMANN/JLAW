#!/usr/bin/env python3
"""Extract plain text from supported evidence files into local processed outputs."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".docx"}


def _read_text_file(path: Path) -> str:
    """Read text content with UTF-8 fallback behavior."""
    return path.read_text(encoding="utf-8", errors="replace")


def extract_text(path: Path, ocr_enabled: bool = False) -> str | None:
    """Extract text from a supported file, returning None when extraction is unavailable."""
    ext = path.suffix.lower()

    if ext in {".txt", ".md"}:
        return _read_text_file(path)
    if ext == ".json":
        try:
            payload = json.loads(_read_text_file(path))
            return json.dumps(payload, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            return _read_text_file(path)
    if ext == ".csv":
        rows: list[str] = []
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                rows.append(",".join(row))
        return "\n".join(rows)
    if ext == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            print(f"WARNING: skipping {path} (.pdf extractor unavailable; install pypdf)")
            return None

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()
        if text:
            return text
        if ocr_enabled:
            print(f"WARNING: OCR requested but not implemented for {path}; skipping")
        else:
            print(f"WARNING: no embedded text found in {path}; use --ocr for OCR-enabled flows")
        return None
    if ext == ".docx":
        try:
            import docx  # type: ignore
        except ImportError:
            print(f"WARNING: skipping {path} (.docx extractor unavailable; install python-docx)")
            return None

        document = docx.Document(str(path))
        return "\n".join([paragraph.text for paragraph in document.paragraphs])

    return None


def _output_stem_for(source_file: Path, input_root: Path) -> str:
    """Build a stable output stem preserving source filename and relative location."""
    relative = source_file.relative_to(input_root)
    return str(relative.as_posix()).replace("/", "__")


def process_directory(input_root: Path, output_root: Path, ocr_enabled: bool = False) -> dict[str, int]:
    """Extract text for all supported files in a directory tree."""
    output_root.mkdir(parents=True, exist_ok=True)

    summary = {"processed": 0, "skipped": 0, "unsupported": 0}
    for source_file in sorted(path for path in input_root.rglob("*") if path.is_file()):
        ext = source_file.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(f"WARNING: skipping unsupported file type: {source_file}")
            summary["unsupported"] += 1
            continue

        extracted = extract_text(source_file, ocr_enabled=ocr_enabled)
        if extracted is None:
            summary["skipped"] += 1
            continue

        stem = _output_stem_for(source_file, input_root)
        output_text = output_root / f"{stem}.txt"
        output_meta = output_root / f"{stem}.metadata.json"

        output_text.write_text(extracted, encoding="utf-8")
        metadata: dict[str, Any] = {
            "source_file": source_file.resolve().as_posix(),
            "input_root": input_root.resolve().as_posix(),
            "output_text_file": output_text.resolve().as_posix(),
            "output_generated_at": datetime.now(tz=UTC).isoformat(),
            "source_extension": ext,
            "ocr_enabled": ocr_enabled,
            "extraction_status": "success",
        }
        output_meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        summary["processed"] += 1

    return summary


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract text from evidence files")
    parser.add_argument("--input", required=True, help="Input evidence directory")
    parser.add_argument("--output", required=True, help="Output extracted text directory")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR workflows (disabled by default)")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    input_root = Path(args.input).resolve()
    output_root = Path(args.output).resolve()

    if not input_root.exists() or not input_root.is_dir():
        print(f"ERROR: input directory not found: {input_root}")
        return 1

    summary = process_directory(input_root=input_root, output_root=output_root, ocr_enabled=args.ocr)
    print(
        "Extraction complete: "
        f"processed={summary['processed']} skipped={summary['skipped']} unsupported={summary['unsupported']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
