from app.engines.reviewer import ReviewItemPayload, ReviewResultPayload
from app.services.reporter import ReporterService


def test_reporter_deduplicates_normalized_quotes_and_keeps_highest_severity():
    low = ReviewItemPayload(
        category="表述模糊",
        severity="low",
        title="期限不清",
        description="描述",
        suggestion="建议",
        source_text="合理 期限。",
    )
    high = low.model_copy(update={"severity": "high", "source_text": "合理期限"})

    normalized = ReporterService().normalize(
        ReviewResultPayload(summary="  总结  ", items=[low, high])
    )

    assert normalized.summary == "总结"
    assert len(normalized.items) == 1
    assert normalized.items[0].severity == "high"
