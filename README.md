# PDF Text Extractor AI 📄🤖

### 👥 Integrantes
* **Fausto Basile**
* **Mauricio Valdés**

### 🤖 Descripción
Aplicación basada en la arquitectura **MVC** diseñada para la extracción y análisis inteligente de texto en archivos PDF mediante el uso de **Inteligencia Artificial**.

### 🛠️ Tecnologías
* **Lenguaje:** `Python 3.12+`
* **Gestor de dependencias:** [uv](https://github.com/astral-sh/uv)
* **Framework Web:** `FastAPI`
* **Base de Datos:** `MongoDB`
* **IA:** `Ollama` / [Modelo a definir]

### 🏗️ Arquitectura (3 Capas)
1. **API (Entrypoints):** Gestión de rutas y protocolos HTTP.
2. **Service (Lógica de Negocio):** Procesamiento de PDFs e integración con IA.
3. **Repository (Persistencia):** Comunicación con MongoDB.

### 📁 Estructura del Proyecto
Organización modular del código siguiendo el patrón de diseño de tres capas para asegurar escalabilidad y mantenibilidad:

```text
pdf-extractor/
├── src/                  # Código fuente (Capa de Aplicación)
│   ├── api/              # CAPA 1: Presentación (Rutas)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── models/           # Esquemas de Datos (Pydantic & Dominio)
│   │   ├── __init__.py
│   │   ├── domain_models.py
│   │   └── pydantic_models.py
│   ├── repository/       # CAPA 3: Persistencia (Acceso a MongoDB)
│   │   ├── __init__.py
│   │   └── database.py
│   ├── services/         # CAPA 2: Lógica de Negocio (IA)
│   │   ├── __init__.py
│   │   └── pdf_processor.py
│   ├── __init__.py
│   └── main.py           # Punto de entrada de FastAPI
├── tests/                # Suite de Pruebas (TDD)
│   ├── __init__.py
│   ├── conftest.py       # Configuración global de pytest
│   ├── test_api.py       # Tests de integración
│   └── test_services.py  # Tests unitarios
├── .env.example          # Plantilla de variables de entorno
├── .gitignore            # Archivos ignorados por Git
├── pyproject.toml        # Configuración de UV y dependencias
└── README.md             # Documentación del proyecto
