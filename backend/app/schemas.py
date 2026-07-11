from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: str | None = None


class DocumentResponse(ORMModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    review_status: str
    upload_time: datetime
    content_summary: str
    chunk_count: int
    parse_method: str
    last_error: str | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class ReviewItemResponse(ORMModel):
    id: int
    category: str
    severity: str
    title: str
    description: str
    suggestion: str
    source_text: str


class ReviewResponse(ORMModel):
    id: int
    document_id: int
    review_time: datetime
    status: str
    total_items: int
    risk_count: int
    summary: str
    duration_ms: int
    pipeline_version: str
    prompt_version: str
    error_message: str | None = None
    items: list[ReviewItemResponse]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    session_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: int


class ChatMessageResponse(ORMModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: int | None
    messages: list[ChatMessageResponse]


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    deepseek_api_configured: bool
    version: str
