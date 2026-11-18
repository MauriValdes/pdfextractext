#!/bin/bash

# Ejecutar desde cualquier directorio; los cuerpos de targets.txt son relativos
# a la raíz del repositorio.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_DIR}" || exit 1

# Configuración de variables
RATE="50/1s"
DURATION="30s"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TARGETS="${SCRIPT_DIR}/targets.txt"
RESULTS_ROOT="${SCRIPT_DIR}/results"
RUN_ID="$(date '+%Y%m%d_%H%M%S')"
RESULT_DIR="${RESULTS_ROOT}/${RUN_ID}"
SUFFIX=1
if ! mkdir -p "${RESULTS_ROOT}"; then
  echo "Error: no se pudo crear el directorio de resultados: ${RESULTS_ROOT}" >&2
  exit 1
fi
while ! mkdir "${RESULT_DIR}" 2>/dev/null; do
  RESULT_DIR="${RESULTS_ROOT}/${RUN_ID}_${SUFFIX}"
  SUFFIX=$((SUFFIX + 1))
done
BIN_OUTPUT="${RESULT_DIR}/results.bin"
JSON_OUTPUT="${RESULT_DIR}/results.json"
PLOT_OUTPUT="${RESULT_DIR}/results.html"
RENDERED_TARGETS="$(mktemp)"
trap 'rm -f "${RENDERED_TARGETS}"' EXIT

# Los targets usan una URL por defecto; reemplazarla permite apuntar a otro
# puerto host sin editar el archivo de targets.
sed "s|^POST [^ ]*/extract$|POST ${BASE_URL%/}/extract|" \
  "${TARGETS}" > "${RENDERED_TARGETS}"

# 1. Ejecutar el ataque, almacenar binario y mostrar reporte en consola
vegeta attack -rate="${RATE}" -duration="${DURATION}" -targets="${RENDERED_TARGETS}" | tee "${BIN_OUTPUT}" | vegeta report

# 2. Generar reporte JSON para análisis automático
vegeta report -type=json < "${BIN_OUTPUT}" > "${JSON_OUTPUT}"

# 3. Generar gráfico interactivo HTML para visualización en navegador
vegeta plot < "${BIN_OUTPUT}" > "${PLOT_OUTPUT}"
