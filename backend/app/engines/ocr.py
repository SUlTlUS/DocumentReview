from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from app.errors import ParseError


class OCRProvider(Protocol):
    name: str

    def process_image(self, image_path: str | Path) -> str: ...

    def process_pdf(self, pdf_path: str | Path) -> str: ...


class FakeOCREngine:
    """Deterministic OCR contract double used when PaddleOCR is not enabled."""

    name = "ocr-mock"

    def __init__(self, text: str = "模拟 OCR 提取内容：扫描合同待人工核对。") -> None:
        self.text = text

    def process_image(self, image_path: str | Path) -> str:
        return self.text

    def process_pdf(self, pdf_path: str | Path) -> str:
        return self.text


class PaddleOCREngine:
    """Lazy PaddleOCR adapter; the large optional runtime is loaded only when used."""

    name = "ocr-paddle"

    def __init__(self, language: str = "ch") -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ParseError(
                "PaddleOCR 未安装",
                "请安装 backend/requirements-ocr.txt 或将 OCR_PROVIDER 设为 fake",
            ) from exc
        self._ocr = PaddleOCR(lang=language)

    @staticmethod
    def _text_from_results(results: list[Any]) -> str:
        lines: list[str] = []
        for result in results:
            payload = getattr(result, "json", result)
            if callable(payload):
                payload = payload()
            if isinstance(payload, dict):
                data = payload.get("res", payload)
                texts = data.get("rec_texts", []) if isinstance(data, dict) else []
                lines.extend(str(text).strip() for text in texts if str(text).strip())
        return "\n".join(lines)

    def _predict(self, path: str | Path) -> str:
        try:
            results = list(self._ocr.predict(input=str(path)))
        except Exception as exc:
            raise ParseError("OCR 识别失败", type(exc).__name__) from exc
        text = self._text_from_results(results)
        if not text.strip():
            raise ParseError("OCR 未识别到可审核文字")
        return text

    def process_image(self, image_path: str | Path) -> str:
        return self._predict(image_path)

    def process_pdf(self, pdf_path: str | Path) -> str:
        return self._predict(pdf_path)


def create_ocr_provider(provider: str) -> OCRProvider:
    if provider.lower() == "paddle":
        return PaddleOCREngine()
    if provider.lower() == "fake":
        return FakeOCREngine()
    raise ParseError("未知 OCR Provider", provider)
