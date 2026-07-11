from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size 必须为正数，且 0 <= overlap < chunk_size")

    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            window = normalized[start:end]
            candidates = [window.rfind(separator) for separator in ("\n", "。", "！", "？", "；")]
            boundary = max(candidates)
            if boundary >= chunk_size // 2:
                end = start + boundary + 1
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks


@dataclass(frozen=True)
class RetrievalResult:
    content: str
    score: float


class RAGService:
    def __init__(self, chunk_size: int = 500, overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunks: list[str] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None

    def build_index(self, text: str) -> list[str]:
        chunks = split_text(text, self.chunk_size, self.overlap)
        if not chunks:
            raise ValueError("无法为无文本内容建立索引")
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        matrix = vectorizer.fit_transform(chunks)
        self._chunks = chunks
        self._vectorizer = vectorizer
        self._matrix = matrix
        return list(chunks)

    def retrieve_context(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if self._vectorizer is None or self._matrix is None:
            raise RuntimeError("RAG 索引尚未建立")
        if not query.strip():
            return []
        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix).ravel()
        ranked = scores.argsort()[::-1][: min(top_k, len(self._chunks))]
        return [
            RetrievalResult(content=self._chunks[index], score=float(scores[index]))
            for index in ranked
        ]

    def get_chunks(self) -> list[str]:
        return list(self._chunks)


class RAGRegistry:
    def __init__(self) -> None:
        self._services: dict[int, RAGService] = {}
        self._lock = RLock()

    def build(self, document_id: int, text: str) -> RAGService:
        service = RAGService()
        service.build_index(text)
        with self._lock:
            self._services[document_id] = service
        return service

    def register(self, document_id: int, service: RAGService) -> None:
        with self._lock:
            self._services[document_id] = service

    def get_or_build(self, document_id: int, text: str) -> RAGService:
        with self._lock:
            service = self._services.get(document_id)
        return service if service is not None else self.build(document_id, text)

    def remove(self, document_id: int) -> None:
        with self._lock:
            self._services.pop(document_id, None)

    def clear(self) -> None:
        with self._lock:
            self._services.clear()


rag_registry = RAGRegistry()
