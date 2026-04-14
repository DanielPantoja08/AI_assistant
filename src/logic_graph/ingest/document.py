"""PDF document processing using Docling: text chunking, image extraction, table extraction."""

import io
import logging
import time
from functools import lru_cache
from pathlib import Path

import pandas as pd

from google import genai

from logic_graph.ingest.config import IMAGE_RESOLUTION_SCALE, OUTPUT_DIR, TABLES_DIR
from logic_graph.ingest.captioning import generate_caption

_log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_converter() -> "DocumentConverter":
    """Build and cache the Docling DocumentConverter (loads ML weights once per process)."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = True

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def process_document(
    source: str | Path, gemini_client: genai.Client
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Convierte el PDF y devuelve:
    - chunks: lista de dicts con texto contextualizado
    - images: lista de dicts con caption generado por Gemini y metadata
    - tables: lista de dicts con markdown de la tabla y metadata
    """
    from docling_core.types.doc import PictureItem, TableItem
    from docling.chunking import HybridChunker

    converter = _get_converter()
    conv_res = converter.convert(str(source))
    doc = conv_res.document

    # ── Extraer chunks de texto ──

    chunker = HybridChunker()
    chunk_iter = chunker.chunk(dl_doc=doc)

    chunks = []
    for i, chunk in enumerate(chunk_iter):
        enriched_text = chunker.contextualize(chunk=chunk)
        chunks.append(
            {
                "id": f"text_{i:04d}",
                "text": enriched_text,
                "raw_text": chunk.text,
                "type": "text",
            }
        )
        
    # ── Extraer imágenes y generar captions ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = []
    picture_counter = 0

    for element, _level in doc.iterate_items():
        if not isinstance(element, PictureItem):
            continue

        pil_image = element.get_image(doc)
        if pil_image is None:
            continue

        picture_counter += 1

        # Convertir PIL Image a bytes PNG
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        # Guardar imagen a disco
        img_filename = OUTPUT_DIR / f"picture_{picture_counter:03d}.png"
        with open(img_filename, "wb") as fp:
            fp.write(img_bytes)

        # Extraer caption original del documento (si existe)
        doc_caption = ""
        try:
            doc_caption = element.caption_text(doc=doc)
        except Exception:
            pass

        # Generar caption enriquecido con Gemini Flash        
        generated_caption = generate_caption(
            gemini_client, img_bytes, "image/png", doc_caption
        )

        # Caption final: combinar caption del documento + caption generado
        if doc_caption:
            full_caption = f"[Document caption]: {doc_caption}\n[AI description]: {generated_caption}"
        else:
            full_caption = f"[AI description]: {generated_caption}"

        page_no = element.prov[0].page_no if element.prov else None

        images.append(
            {
                "id": f"img_{picture_counter:03d}",
                "doc_caption": doc_caption,
                "generated_caption": generated_caption,
                "full_caption": full_caption,
                "filename": str(img_filename),
                "page_no": page_no,
                "type": "image",
            }
        )
        
        # Pausa breve para no saturar la API
        time.sleep(0.5)

        # ── Extraer tablas ──
    
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    tables = []
    table_counter = 0

    for table_item in doc.tables:
        table_counter += 1

        # Exportar a DataFrame y luego a Markdown
        try:
            table_df: pd.DataFrame = table_item.export_to_dataframe(doc=doc)
        except Exception:
            try:
                table_df = table_item.export_to_dataframe()
            except Exception as e:
                _log.warning(f"Error exportando tabla {table_counter}: {e}")
                continue

        if table_df.empty:
            continue

        table_markdown = table_df.to_markdown(index=False)

        # Guardar como CSV
        csv_filename = TABLES_DIR / f"table_{table_counter:03d}.csv"
        table_df.to_csv(csv_filename, index=False)

        # Extraer caption de la tabla (si existe)
        table_caption = ""
        try:
            table_caption = table_item.caption_text(doc=doc)
        except Exception:
            pass

        # Número de página
        page_no = table_item.prov[0].page_no if table_item.prov else None

        # Texto para embedding: encabezado de contexto + markdown de la tabla
        context_header = f"Table {table_counter}"
        if table_caption:
            context_header += f": {table_caption}"
        if page_no:
            context_header += f" (Page {page_no})"

        embed_text = f"{context_header}\n\n{table_markdown}"

        tables.append(
            {
                "id": f"tbl_{table_counter:03d}",
                "embed_text": embed_text,
                "markdown": table_markdown,
                "caption": table_caption,
                "csv_filename": str(csv_filename),
                "page_no": page_no,
                "num_rows": len(table_df),
                "num_cols": len(table_df.columns),
                "type": "table",
            }
        )       
    
    return chunks, images, tables
