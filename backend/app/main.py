from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine
from app.errors import AppError
from app.models import Base
from app.routers.documents import router as documents_router
from app.routers.review import router as review_router
from app.routers.chat import router as chat_router
from app.schemas import ErrorResponse, HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="RAG 文档审核系统",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router)
app.include_router(review_router)
app.include_router(chat_router)


@app.exception_handler(AppError)
async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    payload = ErrorResponse(code=exc.code, message=exc.message, detail=exc.detail)
    return JSONResponse(status_code=400, content=payload.model_dump())


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", llm_provider=settings.llm_provider, version=app.version)
