from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from langchain_core.runnables import RunnableParallel

from app.engines.reviewer import ReviewEngine, ReviewResultPayload
from app.services.reporter import ReporterService


logger = logging.getLogger("uvicorn.error")


class ReviewChain:
    """Three-stage LCEL pipeline: structure, parallel dimensions, aggregation."""

    pipeline_version = "v2.0"

    def __init__(self, engine: ReviewEngine, max_concurrency: int = 2) -> None:
        self.engine = engine
        self.max_concurrency = max_concurrency
        self.reporter = ReporterService()

    def invoke(self, document_text: str) -> ReviewResultPayload:
        started = perf_counter()
        structure = self.engine.structure_runnable().invoke({"document_text": document_text})
        structure_ms = round((perf_counter() - started) * 1_000)
        logger.info("review_stage_complete stage=structure duration_ms=%d", structure_ms)

        dimension_input = {
            "document_text": document_text[: self.engine.settings.max_review_chars],
            "document_structure": structure,
        }
        dimension_chain = RunnableParallel(
            **{
                dimension["key"]: self.engine.dimension_runnable(dimension)
                for dimension in self.engine.dimensions
            }
        )
        dimension_started = perf_counter()
        dimension_results: dict[str, Any] = dimension_chain.invoke(
            dimension_input,
            config={"max_concurrency": self.max_concurrency},
        )
        dimension_ms = round((perf_counter() - dimension_started) * 1_000)
        logger.info(
            "review_stage_complete stage=dimensions dimensions=%d duration_ms=%d",
            len(dimension_results),
            dimension_ms,
        )

        report_input = {
            "document_structure": structure,
            "dimension_results": dimension_results
            if self.engine.is_mock
            else _serialize_results(dimension_results),
        }
        report_started = perf_counter()
        result = self.reporter.normalize(self.engine.report_runnable().invoke(report_input))
        report_ms = round((perf_counter() - report_started) * 1_000)
        logger.info(
            "review_stage_complete stage=report findings=%d duration_ms=%d total_ms=%d",
            len(result.items),
            report_ms,
            round((perf_counter() - started) * 1_000),
        )
        return result


def _serialize_results(results: dict[str, Any]) -> str:
    payload = {
        key: value.model_dump() if hasattr(value, "model_dump") else value
        for key, value in results.items()
    }
    import json

    return json.dumps(payload, ensure_ascii=False)
