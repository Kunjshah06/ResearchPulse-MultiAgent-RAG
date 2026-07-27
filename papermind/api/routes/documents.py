# =============================================================================
# PaperMind AI — Document Management API Routes
# =============================================================================

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from papermind.chunking.chunker_service import ChunkerService
from papermind.core.config.settings import get_settings
from papermind.core.logging.logger import get_logger
from papermind.embeddings.embedding_service import EmbeddingService
from papermind.graph.builders.document_graph_builder import DocumentGraphBuilder
from papermind.models.domain.document import Document, DocumentStatus
from papermind.services.document.ingestion_service import IngestionService
from papermind.vectorstore.factory import get_vector_store

log = get_logger(__name__)
router = APIRouter()

# In-memory document storage registry for active session
_DOCUMENTS_DB: dict[str, Document] = {}


def _get_storage_dir() -> Path:
    settings = get_settings()
    docs_dir = settings.storage.upload_dir.parent / "processed_docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


class DocumentSummaryResponse(BaseModel):
    id: str
    filename: str
    status: str
    page_count: int
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    element_count: int = 0
    table_count: int = 0
    figure_count: int = 0
    equation_count: int = 0
    chunk_count: int = 0


from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from papermind.database.db_service import db_service
from papermind.api.routes.auth import get_user_from_auth_header


@router.post("/upload", response_model=DocumentSummaryResponse)
async def upload_document(
    file: UploadFile = File(...),
    authorization: str | None = Header(None),
) -> DocumentSummaryResponse:
    """Upload a PDF document, run dual-path ingestion, chunking, embedding, and indexing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    user = get_user_from_auth_header(authorization)

    settings = get_settings()
    file_id = str(uuid.uuid4())
    save_path = settings.storage.upload_dir / f"{file_id}_{file.filename}"

    original_filename = file.filename  # preserve before any path mangling
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    log.info("Uploaded document received", filename=original_filename, path=str(save_path))

    # 1. Ingest PDF
    ingest_svc = IngestionService()
    doc = await ingest_svc.ingest_document(str(save_path), doc_id=file_id)
    doc.id = file_id  # Align document ID with storage prefix
    doc.filename = original_filename  # restore user-visible filename

    # 2. Chunking
    chunker = ChunkerService()
    chunks = chunker.process_document(doc)

    # 3. Embedding
    embedder = EmbeddingService()
    embedder.embed_document(doc)

    # 4. Vector Store Upsert
    vector_store = get_vector_store()
    vector_store.upsert_chunks(doc.chunks)

    # 5. Graph Construction
    graph_builder = DocumentGraphBuilder()
    graph_builder.build(doc)

    # Store in memory & save to disk
    _DOCUMENTS_DB[doc.id] = doc

    # If user is authenticated, store user-document association in database
    if user:
        authors_str = ", ".join(doc.metadata.authors) if isinstance(doc.metadata.authors, list) else (doc.metadata.authors or "Extracted Authors")
        title_str = doc.metadata.title or original_filename
        db_service.add_user_document(user["id"], doc.id, original_filename, title_str, authors_str)

    try:
        storage_dir = _get_storage_dir()
        doc_json_path = storage_dir / f"{doc.id}.json"
        with open(doc_json_path, "w", encoding="utf-8") as f:
            json.dump(doc.model_dump(mode="json"), f, indent=2)
        log.info("Persisted document to disk", doc_id=doc.id, path=str(doc_json_path))
    except Exception as e:
        log.warning("Failed to persist document JSON to disk", doc_id=doc.id, error=str(e))

    return DocumentSummaryResponse(
        id=doc.id,
        filename=original_filename,
        status=doc.status.value,
        page_count=doc.metadata.page_count,
        title=doc.metadata.title,
        authors=doc.metadata.authors,
        element_count=len(doc.elements),
        table_count=len(doc.tables),
        figure_count=len(doc.figures),
        equation_count=len(doc.equations),
        chunk_count=len(doc.chunks),
    )


@router.get("", response_model=list[dict[str, Any]])
@router.get("/", response_model=list[dict[str, Any]])
async def list_documents(authorization: str | None = Header(None)) -> list[dict[str, Any]]:
    """List all processed documents for the authenticated user."""
    user = get_user_from_auth_header(authorization)
    if user:
        user_docs = db_service.get_user_documents(user["id"])
        if user_docs:
            return user_docs

    storage_dir = _get_storage_dir()
    results: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    def add_doc(doc_id: str, title: str, authors: Any, status: str):
        if "api_test" in doc_id.lower() or "api_test" in title.lower() or "sample.pdf" in title.lower():
            return
        clean_title = title.strip()
        if clean_title and clean_title not in seen_titles:
            seen_titles.add(clean_title)
            authors_str = ", ".join(authors) if isinstance(authors, list) else (authors or "Extracted Authors")
            results.append({
                "id": doc_id,
                "title": clean_title,
                "authors": authors_str,
                "timestamp": status,
            })

    for doc_id, doc in _DOCUMENTS_DB.items():
        add_doc(doc.id, doc.metadata.title or doc.filename or "Research Paper", doc.metadata.authors, "Active")

    if storage_dir.exists():
        for json_file in storage_dir.glob("*.json"):
            doc_id = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    meta = data.get("metadata", {})
                    title = meta.get("title") or data.get("filename") or "Research Paper"
                    authors = meta.get("authors") or "Extracted Authors"
                    add_doc(doc_id, title, authors, "Saved")
            except Exception:
                pass

    return results


async def fetch_document_entity(doc_id: str) -> Document | None:
    """Helper function to load Document domain model from memory, disk JSON, or PDF auto-recovery."""
    if doc_id in _DOCUMENTS_DB:
        return _DOCUMENTS_DB[doc_id]

    storage_dir = _get_storage_dir()
    doc_json_path = storage_dir / f"{doc_id}.json"
    if doc_json_path.exists():
        try:
            with open(doc_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                doc = Document.model_validate(data)
                _DOCUMENTS_DB[doc_id] = doc

                # Re-index chunks into vector store if not already present
                if doc.chunks:
                    try:
                        embedder = EmbeddingService()
                        embedder.embed_document(doc)
                        vector_store = get_vector_store()
                        vector_store.upsert_chunks(doc.chunks)
                    except Exception as ve:
                        log.warning("Failed indexing loaded document chunks to vector store", doc_id=doc_id, error=str(ve))

                return doc
        except Exception as e:
            log.error("Failed parsing document JSON from disk", doc_id=doc_id, error=str(e))

    settings = get_settings()
    matching_files = list(settings.storage.upload_dir.glob(f"{doc_id}_*.pdf"))
    if matching_files:
        pdf_path = matching_files[0]
        try:
            ingest_svc = IngestionService()
            doc = await ingest_svc.ingest_document(str(pdf_path))
            doc.id = doc_id
            _DOCUMENTS_DB[doc_id] = doc
            with open(doc_json_path, "w", encoding="utf-8") as f:
                json.dump(doc.model_dump(mode="json"), f, indent=2)
            return doc
        except Exception as e:
            log.error("Failed auto-recovering document", doc_id=doc_id, error=str(e))

    return None


@router.get("/{doc_id}", response_model=dict[str, Any])
async def get_document(doc_id: str) -> dict[str, Any]:
    """Retrieve processed document metadata and details."""
    doc = await fetch_document_entity(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return doc.model_dump(mode="json")


@router.get("/{doc_id}/file")
async def get_document_file(doc_id: str):
    """Stream the raw uploaded PDF file for native PDF rendering."""
    from fastapi.responses import FileResponse
    settings = get_settings()

    matching_files = list(settings.storage.upload_dir.glob(f"{doc_id}_*.pdf"))
    if matching_files:
        return FileResponse(
            path=matching_files[0],
            media_type="application/pdf",
            filename=matching_files[0].name,
        )

    # Check processed_docs or fallback sample PDF
    fallback_sample = Path(__file__).resolve().parents[2] / "samples" / "sample.pdf"
    if fallback_sample.exists():
        return FileResponse(path=fallback_sample, media_type="application/pdf")

    raise HTTPException(status_code=404, detail=f"PDF file for document '{doc_id}' not found.")


@router.post("/{doc_id}/generate-presentation")
async def generate_document_presentation(doc_id: str):
    """Generates a downloadable 10-slide PowerPoint presentation (.pptx) summarizing the paper."""
    from fastapi.responses import Response
    from papermind.services.presentation.pptx_generator import PresentationService

    # Fetch document entity
    doc_dict = await get_document(doc_id)
    doc = Document.model_validate(doc_dict)

    # Generate 10-slide PPTX binary bytes
    pres_svc = PresentationService()
    pptx_bytes = pres_svc.generate_presentation(doc)

    clean_filename = f"{doc_id}_Presentation_Deck.pptx"

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={clean_filename}"},
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str) -> dict[str, str]:
    """Delete a document from index and memory."""
    if doc_id in _DOCUMENTS_DB:
        del _DOCUMENTS_DB[doc_id]

    storage_dir = _get_storage_dir()
    doc_json_path = storage_dir / f"{doc_id}.json"
    if doc_json_path.exists():
        doc_json_path.unlink()

    vector_store = get_vector_store()
    vector_store.delete_document(doc_id)
    return {"status": "deleted", "doc_id": doc_id}
