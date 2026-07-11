from __future__ import annotations

from typing import Protocol

from fastapi import Depends

from app.chains.chat_chain import ChatChain
from app.chains.review_chain import ReviewChain
from app.config import Settings, get_settings
from app.engines.reviewer import (
    ChatEngine,
    ReviewEngine,
    ReviewItemPayload,
    ReviewResultPayload,
    validate_review_result,
)
from app.services.rag import RetrievalResult


class ReviewerProvider(Protocol):
    pipeline_version: str
    prompt_version: str

    def review_document(self, text: str, chunks: list[str]) -> ReviewResultPayload: ...

    def chat(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str: ...


class V2ReviewerProvider:
    pipeline_version = "v2.0"

    def __init__(self, settings: Settings) -> None:
        review_engine = ReviewEngine(settings)
        self.prompt_version = review_engine.prompt_version
        self.review_chain = ReviewChain(review_engine, max_concurrency=2)
        self.chat_chain = ChatChain(ChatEngine(settings))

    def review_document(self, text: str, chunks: list[str]) -> ReviewResultPayload:
        return self.review_chain.invoke(text)

    def chat(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        return self.chat_chain.invoke(contexts, question, history)


def get_reviewer_provider(
    settings: Settings = Depends(get_settings),
) -> ReviewerProvider:
    return V2ReviewerProvider(settings)


__all__ = [
    "ReviewItemPayload",
    "ReviewResultPayload",
    "ReviewerProvider",
    "V2ReviewerProvider",
    "get_reviewer_provider",
    "validate_review_result",
]
