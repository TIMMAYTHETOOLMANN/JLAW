"""
OCRCascade - Phase 1
====================
Multi-engine OCR with graceful degradation for research environments.

This module attempts to use several OCR engines in order of preference and
returns the first successful result meeting a confidence threshold. All
third-party imports are lazy and optional to keep the system runnable
without heavy dependencies.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str


class OCRCascade:
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        logger.info("✅ OCRCascade initialized (threshold=%.2f)", confidence_threshold)

    def _ocr_paddleocr(self, image_bytes: bytes) -> Optional[OCRResult]:
        try:
            from paddleocr import PaddleOCR  # type: ignore
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            import numpy as np
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            np_img = np.array(img)
            result = ocr.ocr(np_img)
            texts = []
            confs = []
            for page in result:
                for line in page:
                    texts.append(line[1][0])
                    confs.append(float(line[1][1]))
            if texts:
                avg_conf = sum(confs) / max(len(confs), 1)
                return OCRResult("\n".join(texts), avg_conf, "PaddleOCR")
        except Exception as e:
            logger.debug("PaddleOCR unavailable or failed: %s", e)
        return None

    def _ocr_doctr(self, image_bytes: bytes) -> Optional[OCRResult]:
        try:
            from doctr.io import DocumentFile  # type: ignore
            from doctr.models import ocr_predictor  # type: ignore
            doc = DocumentFile.from_images([io.BytesIO(image_bytes)])
            model = ocr_predictor(pretrained=True)
            res = model(doc)
            # Doctr does not provide a simple numeric confidence; use heuristic
            text = res.render()
            conf = 0.88 if text.strip() else 0.0
            return OCRResult(text, conf, "DocTR")
        except Exception as e:
            logger.debug("DocTR unavailable or failed: %s", e)
        return None

    def _ocr_easyocr(self, image_bytes: bytes) -> Optional[OCRResult]:
        try:
            import easyocr  # type: ignore
            from PIL import Image
            reader = easyocr.Reader(['en'])
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            import numpy as np
            res = reader.readtext(np.array(img))
            texts = [r[1] for r in res]
            confs = [float(r[2]) for r in res if len(r) > 2]
            if texts:
                avg_conf = sum(confs) / max(len(confs), 1) if confs else 0.80
                return OCRResult("\n".join(texts), avg_conf, "EasyOCR")
        except Exception as e:
            logger.debug("EasyOCR unavailable or failed: %s", e)
        return None

    def _ocr_tesseract(self, image_bytes: bytes) -> Optional[OCRResult]:
        try:
            import pytesseract  # type: ignore
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes)).convert('L')
            text = pytesseract.image_to_string(img)
            conf = 0.70 if text.strip() else 0.0  # conservative default
            return OCRResult(text, conf, "Tesseract")
        except Exception as e:
            logger.debug("Tesseract unavailable or failed: %s", e)
        return None

    def run(self, image: Union[bytes, io.BytesIO]) -> OCRResult:
        """Run OCR through cascade and return best available result.

        Always returns an OCRResult with best-effort confidence, even if below threshold.
        """
        image_bytes = image if isinstance(image, bytes) else image.getvalue()

        strategies = [
            self._ocr_paddleocr,
            self._ocr_doctr,
            self._ocr_easyocr,
            self._ocr_tesseract,
        ]

        best: Optional[OCRResult] = None
        for strat in strategies:
            res = strat(image_bytes)
            if res is None:
                continue
            if best is None or res.confidence > best.confidence:
                best = res
            if res.confidence >= self.confidence_threshold:
                logger.info("🧠 OCR success using %s (conf=%.2f)", res.engine, res.confidence)
                return res

        # No engine met threshold; return best-effort result
        if best is not None:
            logger.info("🧠 OCR best-effort using %s (conf=%.2f)", best.engine, best.confidence)
            return best
        # Fallback empty
        return OCRResult(text="", confidence=0.0, engine="none")
