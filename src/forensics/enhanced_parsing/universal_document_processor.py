"""
Universal Document Processor - Phase 1
======================================
Facade over existing UniversalDocumentExtractor with OCR cascade, table
extraction, and optional NLP entity extraction. Designed to match the
Enhancement Protocol baseline in a research-friendly, modular way.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .ocr_cascade import OCRCascade
from .table_extractor import ForensicTableExtractor
from .document_processor import EnhancedDocumentProcessor
from ..universal_document_extractor import (
    UniversalDocumentExtractor,
    ExtractionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    text: str
    tables: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UniversalDocumentProcessor:
    """Unified processor that detects format, extracts text, tables, and entities.

    Enhancements:
    - Provenance: capture engines used and versions when possible
    - Confidence: per-modality confidences + overall aggregate
    - OCR routing: if input is image or text is empty, attempt OCR cascade
    - Optional ML tables path stub (feature-flagged)
    """

    def __init__(
        self,
        confidence_threshold: float = 0.85,
        enable_ml_tables: bool = False,
    ):
        self.ocr_cascade = OCRCascade(confidence_threshold=confidence_threshold)
        self.table_extractor = ForensicTableExtractor()
        self.base_extractor = UniversalDocumentExtractor()
        self.enable_ml_tables = enable_ml_tables

        # Optional spaCy
        self._nlp = None
        self._nlp_model_name = None
        try:
            import spacy  # type: ignore
            try:
                self._nlp = spacy.load('en_core_web_trf')
                self._nlp_model_name = 'en_core_web_trf'
            except Exception:
                self._nlp = spacy.load('en_core_web_sm')
                self._nlp_model_name = 'en_core_web_sm'
        except Exception as e:
            logger.debug("spaCy not available: %s", e)
            self._nlp = None
            self._nlp_model_name = None

        logger.info("✅ UniversalDocumentProcessor initialized (ml_tables=%s)", enable_ml_tables)

    def _read_bytes(self, content_or_path: Union[str, bytes]) -> bytes:
        if isinstance(content_or_path, bytes):
            return content_or_path
        p = Path(str(content_or_path))
        if p.exists() and p.is_file():
            return p.read_bytes()
        # Treat as raw text
        return str(content_or_path).encode('utf-8', errors='ignore')

    def _mime_type(self, data: bytes) -> Optional[str]:
        try:
            import magic  # type: ignore
            return magic.from_buffer(data, mime=True)
        except Exception:
            return None

    def _is_probable_pdf(self, b: bytes) -> bool:
        return b.startswith(b"%PDF-")

    def _is_probable_image(self, b: bytes) -> bool:
        # Basic magic numbers for common formats
        return (
            b.startswith(b"\xFF\xD8\xFF")  # JPEG
            or b.startswith(b"\x89PNG\r\n\x1a\n")  # PNG
            or b.startswith(b"GIF8")  # GIF
            or b.startswith(b"BM")  # BMP
        )

    async def process(self, content_or_path: Union[str, bytes]) -> ProcessingResult:
        raw_bytes = self._read_bytes(content_or_path)
        provenance: Dict[str, Any] = {}
        # Basic MIME detection (optional)
        mime = self._mime_type(raw_bytes)
        if mime:
            provenance['mime'] = mime

        # Delegate to existing base extractor for robust format handling
        base: ExtractionResult = await self.base_extractor.extract_document(raw_bytes)
        text_engine = getattr(base, 'extraction_method', 'unknown') if base else 'unknown'
        text: str = base.raw_text if base and base.success else ""
        text_confidence = 0.90 if base and base.success and (text or '').strip() else 0.0

        # If no text extracted and input appears to be an image, try OCR cascade
        ocr_used = False
        ocr_engine = None
        if not text.strip() and self._is_probable_image(raw_bytes):
            try:
                ocr_res = self.ocr_cascade.run(raw_bytes)
                text = ocr_res.text or ""
                text_confidence = float(ocr_res.confidence or 0.0)
                ocr_engine = ocr_res.engine
                ocr_used = True
                text_engine = f"ocr:{ocr_engine}"
            except Exception as e:
                logger.debug("OCR cascade failed: %s", e)

        # If still no text and it's a PDF, attempt pypdfium2 render + OCR of first page(s)
        if not text.strip() and self._is_probable_pdf(raw_bytes):
            try:
                import pypdfium2 as pdfium  # type: ignore
                from PIL import Image
                import io as _io

                # Prefer path-based open if a file path is provided
                pdf_path: Optional[str] = None
                if isinstance(content_or_path, (str, Path)):
                    pth = Path(str(content_or_path))
                    if pth.exists() and pth.is_file():
                        pdf_path = str(pth)

                doc = pdfium.PdfDocument(pdf_path if pdf_path else raw_bytes)
                pages_to_try = min(2, len(doc)) or 1
                page_texts: List[str] = []
                page_confs: List[float] = []
                for i in range(pages_to_try):
                    page = doc[i]
                    # Render at 150-200 DPI equivalent (scale ~2.0) for OCR
                    bitmap = page.render(scale=2.0)
                    pil = bitmap.to_pil()
                    buf = _io.BytesIO()
                    pil.save(buf, format='PNG')
                    img_bytes = buf.getvalue()
                    try:
                        ocr_res = self.ocr_cascade.run(img_bytes)
                        if (ocr_res.text or '').strip():
                            page_texts.append(ocr_res.text)
                            page_confs.append(float(ocr_res.confidence or 0.0))
                            ocr_engine = ocr_res.engine
                            ocr_used = True
                    except Exception as _e:
                        logger.debug("PDF page OCR failed: %s", _e)
                if page_texts:
                    text = "\n\n".join(page_texts)
                    text_confidence = sum(page_confs) / max(len(page_confs), 1)
                    text_engine = f"pdf-ocr:{ocr_engine or 'unknown'}"
            except Exception as e:
                logger.debug("PDF OCR fallback failed: %s", e)

        # Fallback to raw decode if still empty
        if not text.strip():
            try:
                text = raw_bytes.decode('utf-8', errors='ignore')
                if text:
                    text_confidence = max(text_confidence, 0.3)
            except Exception:
                text = ""

        provenance['text_engine'] = text_engine
        if ocr_engine:
            provenance['ocr_engine'] = ocr_engine
        # Attach versions for engines actually used where possible
        versions: Dict[str, Any] = {}
        # spaCy
        try:
            if self._nlp is not None:
                import spacy  # type: ignore
                versions['spacy'] = getattr(spacy, '__version__', None)
        except Exception:
            pass
        # Text extraction engines
        try:
            if isinstance(provenance.get('text_engine', ''), str):
                eng = provenance['text_engine']
                if 'pymupdf' in eng or 'fitz' in eng:
                    import fitz  # type: ignore
                    versions['pymupdf'] = getattr(fitz, '__doc__', '')
                if 'pdfplumber' in eng:
                    import pdfplumber  # type: ignore
                    versions['pdfplumber'] = getattr(pdfplumber, '__version__', None)
                if 'pdfium' in eng or 'pdf-ocr' in eng:
                    import pypdfium2  # type: ignore
                    versions['pypdfium2'] = getattr(pypdfium2, '__version__', None)
        except Exception:
            pass
        # OCR engines
        try:
            if ocr_engine == 'PaddleOCR':
                import paddleocr  # type: ignore
                versions['paddleocr'] = getattr(paddleocr, '__version__', None)
            elif ocr_engine == 'EasyOCR':
                import easyocr  # type: ignore
                versions['easyocr'] = getattr(easyocr, '__version__', None)
            elif ocr_engine == 'Tesseract':
                import pytesseract  # type: ignore
                versions['pytesseract'] = getattr(pytesseract, '__version__', None)
        except Exception:
            pass

        # Tables from text content (best-effort)
        tables_engine = 'heuristic'
        try:
            tables_ext = await self.table_extractor.extract_tables_with_context(text)
            tables = [
                {
                    'headers': t.headers,
                    'rows': t.data,
                    'confidence': t.confidence,
                    'type': t.table_type,
                }
                for t in tables_ext
            ]
        except Exception as e:
            logger.debug("Table extraction failed: %s", e)
            tables = []

        # Optional ML tables path (feature-flagged; stubbed unless libs present)
        if self.enable_ml_tables:
            try:
                import layoutparser as lp  # type: ignore
                # Placeholder: if layoutparser is present, mark engine as 'ml-ready'
                tables_engine = 'ml'
            except Exception:
                # Silent skip if not available
                pass

        # Entities via spaCy if available
        entities: List[Dict[str, Any]] = []
        if self._nlp and text:
            try:
                doc = self._nlp(text[:500_000])  # cap to avoid memory issues
                entities = [
                    {'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char}
                    for ent in doc.ents
                ]
            except Exception as e:
                logger.debug("NLP entity extraction failed: %s", e)

        # Confidence aggregation
        table_confidence = 0.0
        if tables:
            table_conf_vals = [float(t.get('confidence') or 0.0) for t in tables]
            table_confidence = sum(table_conf_vals) / max(len(table_conf_vals), 1)

        if self._nlp_model_name == 'en_core_web_trf':
            entity_confidence = 0.9 if entities else 0.6
        elif self._nlp_model_name == 'en_core_web_sm':
            entity_confidence = 0.7 if entities else 0.4
        else:
            entity_confidence = 0.0

        # Overall confidence heuristic: weighted average
        overall_conf = max(0.0, min(1.0, (0.6 * text_confidence) + (0.25 * table_confidence) + (0.15 * entity_confidence)))

        meta = {
            'extraction_method': getattr(base, 'extraction_method', 'unknown'),
            'element_count': getattr(base, 'element_count', 0),
            'provenance': {
                **provenance,
                'tables_engine': tables_engine,
                'nlp_model': self._nlp_model_name,
                'ml_tables_enabled': bool(self.enable_ml_tables),
                'versions': versions,
            },
            'confidences': {
                'text_confidence': round(text_confidence, 4),
                'table_confidence': round(table_confidence, 4),
                'entity_confidence': round(entity_confidence, 4),
                'overall': round(overall_conf, 4),
            },
        }

        return ProcessingResult(
            text=text,
            tables=tables,
            entities=entities,
            confidence=overall_conf,
            metadata=meta
        )
