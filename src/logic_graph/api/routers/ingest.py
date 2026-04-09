from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from logic_graph.auth import User, current_active_user
from logic_graph.ingest.clients import get_chroma_client, get_gemini_client, get_or_create_collection
from logic_graph.ingest.document import process_document
from logic_graph.ingest.indexing import index_to_collection

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestResponse(BaseModel):
    status: str
    collection: str
    source_name: str
    chunks: int
    images: int
    tables: int


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    collection: str = Form(...),
    source_name: str = Form(...),
    category: str = Form(default=""),
    _user: User = Depends(current_active_user),
) -> IngestResponse:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

    pdf_bytes = await file.read()

    try:
        
        coll = get_or_create_collection(get_chroma_client(), collection)
        
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = Path(tmp.name)

    try:
        chunks, images, tables = await asyncio.to_thread(
            process_document, tmp_path, get_gemini_client()
        )
        doc_metadata = {"source_name": source_name, "source": source_name, "category": category}
        await asyncio.to_thread(
            index_to_collection, coll, chunks, images, tables, get_gemini_client(), doc_metadata
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    return IngestResponse(
        status="ok",
        collection=collection,
        source_name=source_name,
        chunks=len(chunks),
        images=len(images),
        tables=len(tables),
    )
