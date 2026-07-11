from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.chains.review_chain import ReviewChain  # noqa: E402
from app.config import Settings  # noqa: E402
from app.engines.reviewer import ReviewEngine  # noqa: E402


def run_v1(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if "仅约束乙方" in text:
        findings.append({"category": "权益不对等", "severity": "high"})
    if "合理期限" in text:
        findings.append({"category": "表述模糊", "severity": "medium"})
    if "保密" not in text:
        findings.append({"category": "条款缺失", "severity": "medium"})
    return findings


def benchmark(name: str, runner, repeats: int = 3) -> dict:
    durations: list[float] = []
    result = None
    for _ in range(repeats):
        started = perf_counter()
        result = runner()
        durations.append((perf_counter() - started) * 1_000)
    items = result.items if hasattr(result, "items") else result
    return {
        "pipeline": name,
        "runs": repeats,
        "duration_ms": {
            "min": round(min(durations), 3),
            "average": round(statistics.mean(durations), 3),
            "max": round(max(durations), 3),
        },
        "finding_count": len(items),
        "categories": [item.category if hasattr(item, "category") else item["category"] for item in items],
    }


def main() -> None:
    text = (ROOT / "backend" / "tests" / "fixtures" / "test_contract.txt").read_text(encoding="utf-8")
    v2_chain = ReviewChain(ReviewEngine(Settings(llm_provider="mock")), max_concurrency=2)
    report = {
        "fixture": "backend/tests/fixtures/test_contract.txt",
        "provider": "mock",
        "results": [
            benchmark("v1.0-inline", lambda: run_v1(text)),
            benchmark("v2.0-lcel", lambda: v2_chain.invoke(text)),
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
