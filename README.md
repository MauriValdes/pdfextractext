# PDF Extract Text

Aplicación web desarrollada en Python diseñada para la carga, procesamiento y persistencia de archivos PDF. El sistema permite la extracción automatizada de contenido textual, garantizando la integridad de los datos mediante el uso de checksum y evitando la duplicidad en una base de datos NoSQL.

---

## Objetivo

El objetivo del proyecto es desarrollar una aplicación web capaz de:

- Cargar archivos PDF.
- Extraer únicamente el contenido textual.
- Calcular el checksum del archivo.
- Evitar la persistencia de documentos duplicados.
- Almacenar la información en una base de datos NoSQL.
- Exponer una API REST para la gestión de documentos.

---

## Stack Tecnológico

- **Lenguaje:** Python
- **Framework:** FastAPI
- **Servidor ASGI:** Uvicorn
- **Gestión de Dependencias:** uv
- **Testing:** Pytest
- **Base de Datos:** MongoDB
- **Contenedores:** Docker & Docker Compose
- **Procesamiento de PDF:** PyPDF, pdfminer

---

## Metodología y Buenas Prácticas

El proyecto se desarrolla bajo un enfoque de ingeniería de software orientado a la mantenibilidad y calidad del código:

- Metodología: Test Driven Development (TDD).
- Principios de Diseño: YAGNI, DRY, KISS y SOLID.
- Arquitectura: Diseño basado en capas (Separation of Concerns).
- Calidad de Código: Adhesión a estándares de Código Limpio (Clean Code).

---

## Arquitectura

El proyecto sigue una arquitectura por capas con el objetivo de separar responsabilidades y facilitar el mantenimiento del código.

| Capa       | Responsabilidad |
|------------|------------------|
| API        | Endpoints REST de FastAPI |
| Services   | Lógica de negocio |
| Repository | Acceso a datos |
| Models     | Modelos y esquemas |
| Database   | Conexión con MongoDB |
| Config     | Configuración de la aplicación |

---

## Estructura del proyecto

```bash
pdfextractext/
├── docs/                          # Documentación técnica y diagramas
│   └── procesamiento_pdf.puml     # Diagrama de flujo del proceso (PlantUML)
├── src/                           # Código fuente principal
│   ├── api/                       # Endpoints y definición de rutas (FastAPI)
│   │   ├── __init__.py
│   │   └── docs_api.py
│   ├── config/                    # Gestión de configuración y variables de entorno
│   │   └── config.py
│   ├── database/                  # Configuración de conexión con MongoDB
│   │   └── mongodb.py
│   ├── models/                    # Definición de esquemas de datos (Pydantic/Document)
│   │   ├── __init__.py
│   │   └── document.py
│   ├── repository/                # Capa de acceso a datos (Patrón Repository)
│   │   ├── __init__.py
│   │   └── document_repository.py
│   ├── services/                  # Lógica de negocio y servicios de procesamiento
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   └── pdf_service.py         # Lógica de extracción de texto
│   ├── __init__.py
│   └── main.py                    # Punto de entrada de la aplicación
├── tests/                         # Suite de pruebas automatizadas (TDD)
│   ├── __init__.py
│   ├── test_api.py                # Tests de integración para endpoints
│   ├── test_database.py           # Tests de persistencia de datos
│   ├── test_docs.py               # Tests de validación de documentación
│   ├── test_document_service.py   # Tests de lógica de negocio
│   └── test_pdf_service.py        # Tests de extracción de PDF
├── .env                           # Variables de entorno locales
├── .env.example                   # Plantilla para variables de entorno
├── .gitignore                     # Archivos y carpetas ignorados por Git
├── docker-compose.yml             # Orquestación de contenedores (App + DB)
├── Dockerfile                     # Definición de la imagen Docker
├── pyproject.toml                 # Configuración del proyecto y dependencias (uv)
├── README.md                      # Documentación del proyecto
└── uv.lock                        # Versiones fijas de dependencias (lockfile)
```

---

## Flujo de procesamiento

El procesamiento de un documento sigue el siguiente flujo:

1. Recepción del archivo PDF.
2. Validación del formato.
3. Extracción del contenido textual.
4. Cálculo del checksum.
5. Verificación de documentos duplicados.
6. Persistencia en MongoDB.
7. Respuesta al cliente.

El diagrama correspondiente se encuentra en:

```
docs/procesamiento_pdf.puml
```

---

## Requisitos

Antes de ejecutar el proyecto es necesario tener instalado:

- Python 3.12+
- Git
- Docker
- Docker Compose
- uv

---

## Configuración y Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/MauriValdes/pdfextractext.git
cd pdfextractext
```

### 2. Configurar el entorno con `uv`

```bash
# Sincronizar dependencias (crea el entorno virtual automáticamente)
uv sync
```

### 3. Configurar variables de entorno

Copie el archivo de ejemplo para establecer sus configuraciones locales:

```bash
cp .env.example .env
# Edite el archivo .env con las credenciales necesarias para MongoDB
```

### 4. Levantar la infraestructura

Utilice `docker-compose` para iniciar la base de datos:

```bash
docker compose up -d
```

### 5. Ejecutar la aplicación

Inicie el servidor de FastAPI utilizando Uvicorn:

```bash
uv run uvicorn src.main:app --reload
```

Una vez iniciado el servidor, la aplicación estará disponible en:

- API: http://127.0.0.1:8000
- Documentación interactiva (Swagger UI): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Desde **Swagger UI** podrá probar los endpoints de la API, incluyendo la carga de archivos PDF mediante el endpoint correspondiente (`/upload`).

## Uso

La API puede utilizarse directamente desde **Swagger UI**.

Flujo de uso:

1. Iniciar la aplicación.
2. Acceder a `/docs`.
3. Seleccionar el endpoint correspondiente.
4. Subir un archivo PDF.
5. Ejecutar la petición.
6. Visualizar la respuesta de la API.

---

### 6. Ejecución de pruebas

Para validar el cumplimiento de los requerimientos mediante TDD:

```bash
# Ejecutar toda la suite de pruebas
uv run pytest
```

## Gestión del proyecto

El desarrollo del proyecto se organiza mediante **GitHub Projects**, utilizando un enfoque incremental para el seguimiento de tareas y funcionalidades.

---

## Estado del proyecto

🚧 **Etapa 1 - En desarrollo**

Actualmente el proyecto implementa las funcionalidades requeridas para la primera etapa del trabajo práctico.

En futuras etapas se incorporarán nuevas funcionalidades y mejoras sobre la API.

---

## Equipo de Desarrollo

- **Mauricio Valdés**
- **Fausto Basile**

---

## Licencia

Proyecto desarrollado con fines académicos para la asignatura **Desarrollo de Software** de la **Universidad Tecnológica Nacional (UTN)**.