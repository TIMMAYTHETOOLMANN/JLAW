"""Tests for evidence text extraction utility."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import extract_evidence_text as extractor


def test_extract_txt_and_md_files(tmp_path: Path) -> None:
    """Text extraction should work for .txt and .md files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir(parents=True)

    (input_dir / "a.txt").write_text("alpha", encoding="utf-8")
    (input_dir / "b.md").write_text("# beta", encoding="utf-8")

    summary = extractor.process_directory(input_root=input_dir, output_root=output_dir, ocr_enabled=False)

    assert summary["processed"] == 2
    assert (output_dir / "a.txt.txt").exists()
    assert (output_dir / "b.md.txt").exists()
    assert (output_dir / "a.txt.metadata.json").exists()

    metadata = json.loads((output_dir / "a.txt.metadata.json").read_text(encoding="utf-8"))
    assert metadata["source_extension"] == ".txt"
    assert metadata["ocr_enabled"] is False


def test_unsupported_files_are_skipped_cleanly(tmp_path: Path, capsys) -> None:
    """Unsupported files should be skipped with warnings and no output text file."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir(parents=True)

    (input_dir / "unsupported.bin").write_bytes(b"\x00\x01")

    summary = extractor.process_directory(input_root=input_dir, output_root=output_dir, ocr_enabled=False)
    captured = capsys.readouterr()

    assert summary["processed"] == 0
    assert summary["unsupported"] == 1
    assert "skipping unsupported file type" in captured.out
    assert list(output_dir.glob("*.txt")) == []
