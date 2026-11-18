#!/bin/bash

# Ejecutar desde cualquier directorio; los cuerpos de targets.txt son relativos
# a la raíz del repositorio.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_DIR}" || exit 1

# Configuración de variables
RATE="50/1s"
DURATION="30s"
TIMEOUT="30s"
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
CLASIFICACION_OUTPUT="${RESULT_DIR}/results_clasificacion.txt"
RENDERED_TARGETS="$(mktemp)"
trap 'rm -f "${RENDERED_TARGETS}"' EXIT

# Los targets usan una URL por defecto; reemplazarla permite apuntar a otro
# puerto host sin editar el archivo de targets.
sed "s|^POST [^ ]*/extract$|POST ${BASE_URL%/}/extract|" \
  "${TARGETS}" > "${RENDERED_TARGETS}"

# 1. Ejecutar el ataque, almacenar binario y mostrar reporte en consola.
#    El timeout por solicitud queda explícito en 30s (antes dependía del
#    default de la herramienta).
vegeta attack -rate="${RATE}" -duration="${DURATION}" -timeout="${TIMEOUT}" \
  -targets="${RENDERED_TARGETS}" | tee "${BIN_OUTPUT}" | vegeta report

# 2. Generar reporte JSON para análisis automático
vegeta report -type=json < "${BIN_OUTPUT}" > "${JSON_OUTPUT}"

# 3. Generar gráfico interactivo HTML para visualización en navegador
vegeta plot < "${BIN_OUTPUT}" > "${PLOT_OUTPUT}"

# 4. Clasificar códigos de respuesta (200/413/503/0/otros) y calcular las
#    tasas propias de MS2. La entrada es el results.json de esta corrida; el
#    campo 'success' de Vegeta NO se usa para las métricas propias (cuenta
#    como éxito todo código < 500: un 413 aparecería como éxito y un 503
#    como fallo indistinguible de un 500). La interpretación queda
#    persistida junto con los resultados de la corrida.
if [ -s "${JSON_OUTPUT}" ]; then
  uv run python - "${JSON_OUTPUT}" > "${CLASIFICACION_OUTPUT}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

codes = {str(k): int(v) for k, v in data.get("status_codes", {}).items()}

total = sum(codes.values())

ok = codes.get("200", 0)
size = codes.get("413", 0)
satur = codes.get("503", 0)
net = codes.get("0", 0)

otros = total - ok - size - satur - net


def pct(n):
    return f"{(100.0 * n / total):.2f}%" if total else "n/a"


print(f"Solicitudes totales: {total}")
print(f"200  extraccion exitosa:            {ok:>5}  ({pct(ok)})")
print(f"413  rechazo esperado (tamano):     {size:>5}  ({pct(size)})")
print(f"503  rechazo esperado (saturacion): {satur:>5}  ({pct(satur)})")
print(f"0    timeout / error de conexion:   {net:>5}  ({pct(net)})")
print(f"otros codigos inesperados:          {otros:>5}  ({pct(otros)})")
print(f"Tasa de extraccion (200/total):        {pct(ok)}")
print(f"Tasa ajustada ((200+413+503)/total):   {pct(ok + size + satur)}")
print(f"Tasa de fallos inesperados ((0+otros)/total): {pct(net + otros)}")
print("Nota: el campo 'success' de Vegeta (codigo < 500) NO debe usarse como")
print("metrica principal: cuenta 413 como exito y confunde 503 con 500.")
PY
  clasificacion_status=$?
  if [ "${clasificacion_status}" -ne 0 ]; then
    echo "Error: la clasificación de resultados falló (uv run python, exit ${clasificacion_status})." >&2
    rm -f "${CLASIFICACION_OUTPUT}"
    exit "${clasificacion_status}"
  fi
  cat "${CLASIFICACION_OUTPUT}"
fi
