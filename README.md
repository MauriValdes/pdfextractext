# PDF Extract Text

Aplicación web desarrollada en Python que permite subir archivos PDF, extraer su contenido de texto y almacenarlo en una base de datos no relacional, garantizando integridad mediante checksum y evitando duplicados.

---

## Tecnologías utilizadas

- 🐍 **Python**
- ⚡ **FastAPI**
- 📦 **uv** (gestor de dependencias)
- 🧪 **Pytest** (testing)
- 🗄️ Base de datos **NoSQL** (MogoDB)
- 📄 Procesamiento de PDFs (librerías como `PyPDF`, `pdfminer`, etc.)

---

## 🧠 Metodología y buenas prácticas

- ✅ TDD (Test Driven Development)
- ✅ Principios:
  - YAGNI
  - DRY
  - KISS
  - SOLID
- ✅ Arquitectura basada en capas
- ✅ Buenas prácticas de código limpio

---

## Integrantes

- **Mauricio Valdés**
- **Fausto Basile**

---

## Estructura del proyecto

```bash
pdfextractext/
│
├── src/
│   ├── api/            # Endpoints de la API (FastAPI)
│   ├── models/         # Modelos de datos
│   ├── repository/     # Acceso a datos
│   ├── services/       # Lógica de negocio
│   │   └── pdf_service.py
│   ├── main.py         # Punto de entrada de la aplicación
│
├── tests/              # Tests unitarios
│   ├── test_api.py
│   └── test_pdf_service.py
│
├── .env.example        # Variables de entorno de ejemplo
├── pyproject.toml      # Configuración del proyecto
├── uv.lock             # Lock de dependencias
└── README.md           # Documentación