from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.engines.ocr import OCRProvider
from app.services.parser import ParsedDocument, parse_document
from app.services.rag import RAGService


@dataclass(frozen=True)
class ParsedAndIndexedDocument:
    parsed: ParsedDocument
    rag: RAGService


class DocumentParsingChain:
    """Coordinates extraction/OCR and indexing without coupling either service to HTTP."""

    pipeline_version = "v2.0"

    def invoke(
        self,
        file_path: str | Path,
        file_type: str,
        ocr_provider: OCRProvider | None,
    ) -> ParsedAndIndexedDocument:
        parsed = parse_document(file_path, file_type, ocr_provider)
        rag = RAGService()
        rag.build_index(parsed.text)
        return ParsedAndIndexedDocument(parsed=parsed, rag=rag)
