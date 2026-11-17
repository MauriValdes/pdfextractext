# 1. Usamos una imagen ligera de Python como base 🐍
FROM python:3.12-slim

# 2. Instalamos uv para manejar las dependencias de forma rápida ⚡
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Establecemos la carpeta de trabajo dentro del contenedor 📁
WORKDIR /app

# 4. Copiamos los archivos de configuración de dependencias primero
# Esto ayuda a que Docker cachee las instalaciones y sea más rápido
COPY pyproject.toml uv.lock ./

# 5. Instalamos las dependencias (sin instalar el proyecto todavía)
RUN uv sync --frozen --no-cache

# 6. Copiamos todo el resto del código de tu carpeta src
COPY . .

# 7. Exponemos el puerto donde corre FastAPI
EXPOSE 8000

# 8. Comando para iniciar la aplicación usando uvicorn
# Se usa un worker por réplica; las réplicas se escalan manualmente con
# `docker compose up --scale document-service=N`.
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
