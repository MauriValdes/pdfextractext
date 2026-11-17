# Microservicio de Extracción de Texto PDF (`pdfextractext`)

> **Cátedra:** Desarrollo de Software — Universidad Tecnológica Nacional (UTN - FRSR)  
> **Integrantes:** Fausto & Equipo  
> **Proyecto:** Trabajo Práctico de Test de Carga, Estrés y Optimización de Microservicio

---

## 📌 Contexto y Evolución de la Arquitectura

Este repositorio implementa un **microservicio 100% *stateless* (sin estado)** dedicado en exclusiva a la extracción síncrona de texto desde archivos PDF.

### 🎯 Principales Decisiones de Ingeniería y Optimización
1. **Procesamiento síncrono stateless:** el servicio procesa el PDF en memoria y responde directamente en la misma conexión HTTP, sin persistencia ni colas de tareas.
2. **Procesamiento de Streams en Memoria (`Zero-Disk I/O`):** Se optimizó la lectura del cuerpo de la petición mediante `await request.body()` utilizando **PyMuPDF (`fitz`)**. Los bytes del PDF se procesan directo en memoria RAM sin volcar archivos temporales al disco.
3. **Ejecución contenerizada:** FastAPI + Uvicorn escucha en el puerto interno `8000`. El Compose de MS2 no incluye proxy; el escalado de réplicas es manual. En el sistema integrado, los usuarios acceden mediante MS1.

---

## 🛠️ Especificación del Endpoint Obligatorio

* **Ruta:** `POST /extract`
* **Entrada (Request):** Archivo binario PDF enviado mediante `multipart/form-data` o *payload* binario directo en el cuerpo de la petición (`application/pdf`).
* **Salida (Response - `200 OK`):** JSON estructurado con el texto extraído en Markdown y la cantidad de páginas del documento.

```json
{
  "content": "# Título del Documento\nTexto extraído en formato Markdown...",
  "page_count": 292
}
```

## Configuración local

MS2 solo utiliza `MAX_FILE_SIZE_MB` y `LOG_LEVEL`. La configuración compartida
está documentada en `../pdfinfraestructure/.env.example`; crear allí el archivo
local `.env` y cargarlo explícitamente al iniciar MS2:

```bash
uv run --env-file ../pdfinfraestructure/.env uvicorn src.main:app --host 0.0.0.0 --port 8002
```

La aplicación no busca ni necesita un archivo `.env` dentro del contenedor.
En Compose individual, pasar el mismo archivo central con `--env-file`; Compose
no descubre automáticamente un `.env` ubicado en el repositorio hermano.

## Ejecución con Docker Compose

El Compose base ejecuta MS2 sin proxy reverso ni publicación de puerto y permite
escalar manualmente las réplicas:

```bash
docker compose --env-file ../pdfinfraestructure/.env up -d --scale document-service=3
```

Las réplicas escuchan en el puerto interno `8000` y no hay un endpoint HTTP
balanceado para acceder desde el host. Para desarrollo o pruebas directas con
una instancia, usar el override single:

```bash
docker compose --env-file ../pdfinfraestructure/.env -f docker-compose.yml -f docker-compose.single.yml up -d
```

La instancia queda disponible en `http://localhost:8000` (`/health` y
`/extract`). El puerto host se puede cambiar con `MS2_HOST_PORT`; el puerto
interno permanece en `8000`. Esta publicación directa es para desarrollo y
pruebas: en el uso del sistema, el acceso de los usuarios se realiza a través
de MS1.
Si MS3 también se ejecuta en Compose single, configurar `APP_PORT=8001` para
evitar que ambos servicios intenten publicar el mismo puerto host.

### Despliegue integrado centralizado

En el despliegue integrado, MS2 se ejecuta exclusivamente desde
`../pdfinfraestructure/docker-compose.integration.yml`. Traefik interno en
`proxy_internal` descubre y balancea las réplicas; MS2 no publica puertos en el
host y no se añade una ruta pública hacia `/extract`. El escalado manual se
realiza desde `pdfinfraestructure/`:

```bash
docker compose -f docker-compose.integration.yml up -d --scale extract-service=1
docker compose -f docker-compose.integration.yml up -d --scale extract-service=2
docker compose -f docker-compose.integration.yml up -d --scale extract-service=3
docker compose -f docker-compose.integration.yml up -d --scale extract-service=5
```

El Compose integrado lee `pdfinfraestructure/.env` desde esa carpeta y entrega
`MAX_FILE_SIZE_MB` y `LOG_LEVEL` a MS2; el contenedor no lee el archivo.

Para probar el extractor de forma aislada dentro del despliegue integrado, usar
un contenedor temporal de k6 o curl conectado a `proxy_internal` y enviar la
petición a `http://traefik-internal:8080/extract`. Esto no publica MS2 en el host
ni crea una ruta en Traefik público. El override `docker-compose.single.yml`
continúa siendo una opción de desarrollo standalone; no debe combinarse con el
Compose integrado.
