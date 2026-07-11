from __future__ import annotations

from app.engines.reviewer import ChatEngine
from app.services.rag import RetrievalResult


class ChatChain:
    pipeline_version = "v2.0"

    def __init__(self, engine: ChatEngine) -> None:
        self.engine = engine

    def invoke(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        context_text = "\n\n".join(
            f"[片段 {index}，相关度 {item.score:.3f}]\n{item.content}"
            for index, item in enumerate(contexts, start=1)
        )
        history_text = "\n".join(f"{role}: {content}" for role, content in history[-8:])
        return self.engine.invoke(context_text, history_text, question)
