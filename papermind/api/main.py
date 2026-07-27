# =============================================================================
# PaperMind AI — FastAPI Application Entry Point
# =============================================================================

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import PaperMindError
from papermind.core.logging.logger import get_logger, setup_logging

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Configure logging
    setup_logging(
        level=settings.logging.level,
        log_format=settings.logging.format,
        log_file=settings.logging.file,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
    )

    log.info(
        "PaperMind AI starting",
        version=settings.app.version,
        env=settings.app.env,
        llm_provider=settings.llm.provider,
        embedding_model=settings.embedding.model,
    )

    # Ensure data directories exist
    figures_dir = settings.storage.upload_dir.parent / "figures"
    for d in [
        settings.storage.upload_dir,
        settings.storage.processed_dir,
        settings.storage.cache_dir,
        settings.storage.exports_dir,
        figures_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    yield

    log.info("PaperMind AI shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PaperMind AI",
        description=(
            "An End-to-End Multimodal Research Paper Intelligence Platform. "
            "Upload research papers and get deep, evidence-grounded answers."
        ),
        version=settings.app.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---------------------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------------------------------------------------------------------------
    # Mount Static Files for Extracted Figure Images
    # ---------------------------------------------------------------------------
    figures_dir = settings.storage.upload_dir.parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/figures", StaticFiles(directory=str(figures_dir)), name="figures")

    # ---------------------------------------------------------------------------
    # Global Exception Handlers
    # ---------------------------------------------------------------------------

    @app.exception_handler(PaperMindError)
    async def papermind_error_handler(request: Request, exc: PaperMindError) -> JSONResponse:
        log.warning(
            "PaperMind domain error",
            error_code=exc.error_code,
            message=exc.message,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=400,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        log.error("Unhandled exception", exc_info=exc, path=str(request.url))
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": {},
            },
        )

    # ---------------------------------------------------------------------------
    # Routers (imported lazily to avoid circular imports)
    # ---------------------------------------------------------------------------
    from papermind.api.routes import auth, documents, health, query, search

    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])

    return app


app = create_app()
