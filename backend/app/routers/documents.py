from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.errors import ParseError
from app.models import Document
from app.schemas import DocumentListResponse, DocumentResponse, DocumentUploadResponse
from app.services.parser import SUPPORTED_TYPES, parse_file
from app.services.rag import rag_registry


router = APIRouter(prefix="/api/documents", tags=["documents"])


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower().lstrip(".")
    if not original_name or suffix not in SUPPORTED_TYPES:
        raise HTTPException(status_code=422, detail="仅支持 PDF、DOCX、TXT 格式")

    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=422, detail="不能上传空文件")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="文件超过 10MB 限制")

    stored_filename = f"{uuid4().hex}.{suffix}"
    storage_path = (settings.upload_dir / stored_filename).resolve()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    document = Document(
        filename=original_name,
        stored_filename=stored_filename,
        storage_path=str(storage_path),
        file_type=suffix,
        file_size=len(content),
        status="uploaded",
        review_status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        document.status = "parsing"
        db.commit()
        storage_path.write_bytes(content)
        text = parse_file(storage_path, suffix)
        rag = rag_registry.build(document.id, text)
        document.extracted_text = text
        document.content_summary = text[:200]
        document.chunk_count = len(rag.get_chunks())
        document.parse_method = "digital"
        document.status = "ready"
        document.last_error = None
        db.commit()
        db.refresh(document)
    except ParseError as exc:
        document.status = "parse_failed"
        document.last_error = exc.message if exc.detail is None else f"{exc.message}: {exc.detail}"
        db.commit()
        db.refresh(document)

    message = (
        f"已索引 {document.chunk_count} 个文本块"
        if document.status == "ready"
        else "文件已保存，但解析失败"
    )
    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(document),
        message=message,
        chunk_count=document.chunk_count,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = list(db.scalars(select(Document).order_by(Document.upload_time.desc())))
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(document) for document in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    return _get_document_or_404(db, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)) -> Response:
    document = _get_document_or_404(db, document_id)
    storage_path = Path(document.storage_path)
    db.delete(document)
    db.commit()
    rag_registry.remove(document_id)
    if storage_path.is_file():
        storage_path.unlink()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

