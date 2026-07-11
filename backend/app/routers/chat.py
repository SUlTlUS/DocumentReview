from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage, ChatSession, Document
from app.schemas import ChatHistoryResponse, ChatRequest, ChatResponse
from app.services.rag import rag_registry
from app.services.reviewer import ReviewerProvider, get_reviewer_provider


router = APIRouter(prefix="/api/documents/{document_id}/chat", tags=["chat"])


def _document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    if document.status != "ready":
        raise HTTPException(status_code=409, detail="只有解析完成的文档可以问答")
    return document


def _resolve_session(db: Session, document_id: int, session_id: int | None) -> ChatSession:
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session is None or session.document_id != document_id:
            raise HTTPException(status_code=404, detail="问答会话不存在")
        return session
    statement = (
        select(ChatSession)
        .where(ChatSession.document_id == document_id)
        .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
        .limit(1)
    )
    session = db.scalar(statement)
    if session is None:
        session = ChatSession(document_id=document_id)
        db.add(session)
        db.flush()
    return session


@router.post("", response_model=ChatResponse)
def send_message(
    document_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db),
    provider: ReviewerProvider = Depends(get_reviewer_provider),
) -> ChatResponse:
    document = _document_or_404(db, document_id)
    session = _resolve_session(db, document_id, request.session_id)
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(8)
    )
    recent = list(reversed(list(db.scalars(statement))))
    history = [(message.role, message.content) for message in recent]
    rag = rag_registry.get_or_build(document.id, document.extracted_text)
    contexts = rag.retrieve_context(request.question, top_k=5)
    answer = provider.chat(contexts, request.question.strip(), history)
    db.add_all(
        [
            ChatMessage(session=session, role="user", content=request.question.strip()),
            ChatMessage(session=session, role="assistant", content=answer),
        ]
    )
    db.commit()
    return ChatResponse(answer=answer, session_id=session.id)


@router.get("/history", response_model=ChatHistoryResponse)
def get_history(
    document_id: int,
    session_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    _document_or_404(db, document_id)
    if session_id is None:
        statement = (
            select(ChatSession)
            .where(ChatSession.document_id == document_id)
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .limit(1)
        )
        session = db.scalar(statement)
        if session is None:
            return ChatHistoryResponse(session_id=None, messages=[])
    else:
        session = db.get(ChatSession, session_id)
        if session is None or session.document_id != document_id:
            raise HTTPException(status_code=404, detail="问答会话不存在")

    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
    )
    return ChatHistoryResponse(session_id=session.id, messages=list(db.scalars(statement)))

