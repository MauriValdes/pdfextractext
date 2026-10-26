# Microservicio de Extracción de Texto PDF (`pdfextractext`)

> **Cátedra:** Desarrollo de Software — Universidad Tecnológica Nacional (UTN - FRSR)  
> **Integrantes:** Fausto & Equipo  
> **Proyecto:** Trabajo Práctico de Test de Carga, Estrés y Optimización de Microservicio

---

## 📌 Contexto y Evolución de la Arquitectura

Este repositorio formaba parte originalmente de una arquitectura monolítica con persistencia en MongoDB y colas asíncronas en Redis/Workers. Para este Trabajo Práctico, **se refactorizó y desacopló completamente el sistema**, transformando este repositorio en un **microservicio 100% *stateless* (sin estado)** dedicado en exclusiva a la extracción síncrona de texto desde archivos PDF.

### 🎯 Principales Decisiones de Ingeniería y Optimización
1. **Paso de Modelo Asíncrono a Síncrono Stateless:** Se eliminaron las capas de base de datos (MongoDB), intermediarios de mensajes (Redis) y *workers* en segundo plano. Esto redujo drásticamente el *overhead* de red y serialización I/O, permitiendo responder inmediatamente en la misma conexión HTTP.
2. **Procesamiento de Streams en Memoria (`Zero-Disk I/O`):** Se optimizó la lectura del cuerpo de la petición mediante `await request.body()` utilizando **PyMuPDF (`fitz`)**. Los bytes del PDF se procesan directo en memoria RAM sin volcar archivos temporales al disco.
3. **Control de Concurrencia y Resiliencia:** Se implementó una arquitectura contenerizada con **FastAPI + Uvicorn** escalable horizontalmente hasta 5 réplicas balanceadas por **Traefik v3**, garantizando el cumplimiento estricto de las restricciones de hardware impuestas por la cátedra.

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