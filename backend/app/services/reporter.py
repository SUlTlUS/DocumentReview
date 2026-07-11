from __future__ import annotations

from app.engines.reviewer import ReviewItemPayload, ReviewResultPayload


class ReporterService:
    """Applies deterministic post-processing after model report generation."""

    _severity_rank = {"high": 0, "medium": 1, "low": 2}

    def normalize(self, report: ReviewResultPayload) -> ReviewResultPayload:
        unique: dict[tuple[str, str], ReviewItemPayload] = {}
        for item in report.items:
            key = (self._normalize_source(item.source_text), item.title.strip())
            previous = unique.get(key)
            if previous is None or self._severity_rank[item.severity] < self._severity_rank[previous.severity]:
                unique[key] = item
        items = sorted(unique.values(), key=lambda item: self._severity_rank[item.severity])
        return ReviewResultPayload(summary=report.summary.strip(), items=items)

    @staticmethod
    def _normalize_source(source: str) -> str:
        return "".join(source.split()).strip("。；，,;：:")
