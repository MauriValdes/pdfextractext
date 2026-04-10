# 1. Usamos la versión de Python que estás usando en clase
FROM python:3.14-slim

# 2. Instalamos curl para poder bajar 'uv'
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 3. Instalamos uv (tu gestor de paquetes)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

# 4. Definimos dónde vivirá el código dentro de la "caja"
WORKDIR /app

# 5. Copiamos los archivos de configuración de dependencias
COPY pyproject.toml uv.lock ./

# 6. Instalamos las librerías (FastAPI, PyMuPDF, etc.)
RUN uv sync --frozen

# 7. Copiamos todo el resto de tu código
COPY . .

# 8. Por ahora, el comando por defecto ejecutará tus pruebas
CMD ["uv", "run", "pytest"]