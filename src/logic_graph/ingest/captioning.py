"""Image captioning using Gemini Flash."""

import logging

from google import genai
from google.genai import types

from logic_graph.ingest.config import CAPTION_PROMPT, CAPTIONING_MODEL

_log = logging.getLogger(__name__)


def generate_caption(
    client: genai.Client,
    image_bytes: bytes,
    mime_type: str = "image/png",
    existing_caption: str = "",
) -> str:
    """
    Genera un caption descriptivo para una imagen usando Gemini Flash.
    Si ya existe un caption del documento, lo incorpora como contexto.
    """
    prompt_parts = []

    # Primero la imagen
    prompt_parts.append(
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    )

    # Luego el texto del prompt
    if existing_caption:
        prompt_parts.append(
            f"{CAPTION_PROMPT}\n\n"
            f"The document already provides this caption for the figure: "
            f'"{existing_caption}". '
            f"Use it as additional context but generate your own richer description."
        )
    else:
        prompt_parts.append(CAPTION_PROMPT)

    try:
        response = client.models.generate_content(
            model=CAPTIONING_MODEL,
            contents=prompt_parts,
        )
        return response.text.strip()
    except Exception as e:
        _log.warning(f"Error generando caption: {e}")
        return existing_caption or "(sin descripción)"
