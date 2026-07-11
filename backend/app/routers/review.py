from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.errors import LLMError
from app.models import Document, Review, ReviewItem
from app.schemas import ReviewResponse
from app.services.rag import rag_registry
from app.services.reviewer import ReviewerProvider, get_reviewer_provider


router = APIRouter(prefix="/api/documents/{document_id}/review", tags=["review"])


def _document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


@router.post("", response_model=ReviewResponse)
def trigger_review(
    document_id: int,
    db: Session = Depends(get_db),
    provider: ReviewerProvider = Depends(get_reviewer_provider),
) -> Review:
    document = _document_or_404(db, document_id)
    if document.status != "ready":
        raise HTTPException(status_code=409, detail="只有解析完成的文档可以审核")

    review = Review(document_id=document_id, status="reviewing", pipeline_version="v1.0")
    document.review_status = "reviewing"
    db.add(review)
    db.commit()
    db.refresh(review)
    started = perf_counter()

    try:
        rag = rag_registry.get_or_build(document.id, document.extracted_text)
        result = provider.review_document(document.extracted_text, rag.get_chunks())
        review.items = [ReviewItem(**item.model_dump()) for item in result.items]
        review.summary = result.summary
        review.total_items = len(review.items)
        review.risk_count = sum(item.severity == "high" for item in review.items)
        review.duration_ms = round((perf_counter() - started) * 1_000)
        review.status = "completed"
        document.review_status = "completed"
        document.last_error = None
        db.commit()
    except LLMError as exc:
        review.status = "review_failed"
        review.error_message = exc.message
        review.duration_ms = round((perf_counter() - started) * 1_000)
        document.review_status = "review_failed"
        document.last_error = exc.message
        db.commit()
        raise HTTPException(status_code=502, detail=exc.message) from exc

    statement = (
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.items))
    )
    return db.scalar(statement)


@router.get("", response_model=ReviewResponse)
def get_latest_review(document_id: int, db: Session = Depends(get_db)) -> Review:
    _document_or_404(db, document_id)
    statement = (
        select(Review)
        .where(Review.document_id == document_id)
        .options(selectinload(Review.items))
        .order_by(Review.review_time.desc(), Review.id.desc())
        .limit(1)
    )
    review = db.scalar(statement)
    if review is None:
        raise HTTPException(status_code=404, detail="该文档尚未审核")
    return review

