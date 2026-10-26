"""Genera los PDFs de prueba (fixtures) para los tests de carga y estrés.

Uso (desde la raíz del repo, con el entorno virtual activo):
    python tests/stress/fixtures/regenerate_fixtures.py

Los fixtures son deterministas en estructura (1, 5 y 10 páginas de texto)
para que los resultados del benchmark sean comparables entre corridas.
"""
from pathlib import Path

import fitz  # PyMuPDF

FIXTURES_DIR = Path(__file__).parent

# Bloque de texto repetido para darle volumen realista a cada página
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
) * 40

PAGE_SIZES = (1, 5, 10)


def make_pdf(pages: int) -> Path:
    """Crea un PDF de N páginas con texto extraíble y lo guarda en fixtures/."""
    path = FIXTURES_DIR / f"sample_{pages}p.pdf"
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Pagina {i + 1} de {pages} - fixture de test de carga",
            fontsize=14,
        )
        page.insert_textbox(
            fitz.Rect(72, 100, 520, 700),
            LOREM,
            fontsize=11,
        )
    doc.save(path)
    doc.close()
    return path


if __name__ == "__main__":
    for n in PAGE_SIZES:
        generated = make_pdf(n)
        print(f"Generado: {generated} ({n} pagina(s), {generated.stat().st_size} bytes)")
