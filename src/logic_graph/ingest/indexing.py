"""Index documents and emergency data into ChromaDB collections."""

import chromadb
from google import genai

from logic_graph.ingest.config import OUTPUT_DIMENSIONALITY
from logic_graph.ingest.embeddings import embed_texts, normalize_embedding


def index_to_collection(
    collection: chromadb.Collection,
    chunks: list[dict],
    images: list[dict],
    tables: list[dict],
    gemini_client: genai.Client,
    doc_metadata: dict,
) -> chromadb.Collection:
    """Indexa texto, imágenes y tablas en una colección ChromaDB existente.

    Args:
        collection: ChromaDB collection (already created by caller).
        chunks: Text chunks from process_document().
        images: Image dicts from process_document().
        tables: Table dicts from process_document().
        gemini_client: Authenticated Gemini client for embeddings.
        doc_metadata: Per-document metadata merged into every record.
            Must contain 'source_name' for ID prefixing.
    """
    source_name = doc_metadata["source_name"]
    print(f"\n7️⃣️  Indexando en coleccion '{collection.name}' (fuente: {source_name})...")

    # ── Indexar chunks de texto en lotes ──
    BATCH_SIZE = 50
    texts = [c["text"] for c in chunks]
    ids = [f"{source_name}_{c['id']}" for c in chunks]
    metadatas = [{"type": "text", "raw_text": c["raw_text"], **doc_metadata} for c in chunks]

    for start in range(0, len(texts), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(texts))
        batch_texts = texts[start:end]
        batch_ids = ids[start:end]
        batch_meta = metadatas[start:end]

        print(f"   📝 Embeddings de texto para chunks {start}–{end - 1}...")
        embeddings = embed_texts(gemini_client, batch_texts)
        embeddings = [normalize_embedding(e) for e in embeddings]

        collection.upsert(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_meta,
        )

    print(f"   ✅ Indexados {len(chunks)} chunks de texto.")

    # ── Indexar imágenes usando embedding de su descripción textual ──
    if images:
        print(f"\n   🖼️  Generando embeddings de descripciones para {len(images)} imágenes...")

        img_texts = [img["full_caption"] for img in images]
        img_ids = [f"{source_name}_{img['id']}" for img in images]
        img_metadatas = [
            {
                "type": "image",
                "doc_caption": img["doc_caption"],
                "generated_caption": img["generated_caption"],
                "filename": img["filename"],
                "page_no": img["page_no"] or -1,
                **doc_metadata,
            }
            for img in images
        ]
        img_documents = [
            f"[IMAGEN: {img['filename']}] "
            f"Página: {img['page_no']} | "
            f"{img['full_caption']}"
            for img in images
        ]

        for start in range(0, len(img_texts), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(img_texts))
            print(f"      Embeddings de descripciones {start}–{end - 1}...")

            embeddings = embed_texts(gemini_client, img_texts[start:end])
            embeddings = [normalize_embedding(e) for e in embeddings]

            collection.upsert(
                ids=img_ids[start:end],
                embeddings=embeddings,
                documents=img_documents[start:end],
                metadatas=img_metadatas[start:end],
            )

        print(f"   ✅ Indexadas {len(images)} imágenes.")

    # ── Indexar tablas usando embedding de su markdown ──
    if tables:
        print(f"\n   📊 Generando embeddings para {len(tables)} tablas...")

        tbl_texts = [t["embed_text"] for t in tables]
        tbl_ids = [f"{source_name}_{t['id']}" for t in tables]
        tbl_metadatas = [
            {
                "type": "table",
                "caption": t["caption"],
                "csv_filename": t["csv_filename"],
                "page_no": t["page_no"] or -1,
                "num_rows": t["num_rows"],
                "num_cols": t["num_cols"],
                **doc_metadata,
            }
            for t in tables
        ]
        tbl_documents = [
            f"[TABLA: {t['csv_filename']}] "
            f"Página: {t['page_no']} | "
            f"{t['caption'] or '(sin caption)'}\n\n"
            f"{t['markdown']}"
            for t in tables
        ]

        for start in range(0, len(tbl_texts), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(tbl_texts))
            print(f"      Embeddings de tablas {start}–{end - 1}...")

            embeddings = embed_texts(gemini_client, tbl_texts[start:end])
            embeddings = [normalize_embedding(e) for e in embeddings]

            collection.upsert(
                ids=tbl_ids[start:end],
                embeddings=embeddings,
                documents=tbl_documents[start:end],
                metadatas=tbl_metadatas[start:end],
            )

        print(f"   ✅ Indexadas {len(tables)} tablas.")

    total = len(chunks) + len(images) + len(tables)
    print(f"\n🎉 Total indexado en ChromaDB: {total} elementos "
          f"({len(chunks)} texto + {len(images)} imágenes + {len(tables)} tablas)")
    return collection


def index_emergencia(
    collection: chromadb.Collection,
    entries: list[dict],
) -> None:
    """
    Indexes emergency resource entries into the emergencia collection.
    Uses dummy zero-embeddings since this collection is for direct lookup only.
    """
    if not entries:
        print("⚠️  No hay entradas de emergencia para indexar.")
        return

    ids = [f"emergencia_{i:04d}" for i, _ in enumerate(entries)]
    # Use zero-embeddings — emergencia uses metadata lookup, not vector search
    zero_embedding = [0.0] * OUTPUT_DIMENSIONALITY
    embeddings = [zero_embedding] * len(entries)
    documents = [entry.get("name", f"Recurso {i}") for i, entry in enumerate(entries)]
    metadatas = [
        {
            "type": entry.get("type", ""),
            "name": entry.get("name", ""),
            "phone": entry.get("phone", ""),
            "description": entry.get("description", ""),
        }
        for entry in entries
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print(f"✅ Indexadas {len(entries)} entradas de emergencia.")
