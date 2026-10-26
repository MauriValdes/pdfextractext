"""DTOs del contrato de extracción síncrona (POST /extract)."""
from pydantic import BaseModel, Field


class ExtractionResponse(BaseModel):
    """Contrato obligatorio de respuesta del endpoint POST /extract.

    El texto extraído se devuelve en formato compatible con Markdown
    (texto plano es un subconjunto válido de Markdown).
    """

    content: str = Field(..., description="Texto extraído del PDF")
    page_count: int = Field(..., ge=0, description="Cantidad total de páginas del PDF")
