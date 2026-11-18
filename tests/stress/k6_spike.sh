#!/bin/bash

# Wrapper de la prueba de spike de k6: ejecuta tests/stress/k6_spike.js sin
# modificar su configuración (executor, stages, VUs, duración, fixtures,
# timeout, métricas, thresholds) y persiste los resultados con la misma
# convención de directorios por corrida que vegeta_attack.sh:
#
#   tests/stress/results/AAAAMMDD_HHMMSS[_N]/results.json
#
# El JSON de k6 (stream de muestras + resumen final con thresholds y las
# métricas de clasificación extract_200/413/503/unexpected_status y sus
# rates) es el artefacto principal de la corrida. k6 no dispone de una
# salida HTML nativa equivalente a `vegeta plot`, por lo que no se genera
# results.html. Tampoco se genera results_clasificacion.txt: la
# clasificación ya vive en las métricas del propio script k6.
#
# BASE_URL se hereda del entorno (12-Factor); el default vive en k6_spike.js:
#   BASE_URL=http://localhost:8088 tests/stress/k6_spike.sh

# Ejecutar desde cualquier directorio. El cwd debe ser la raíz del
# repositorio porque k6_spike.js abre los fixtures con rutas relativas
# (./fixtures/...).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_DIR}" || exit 1

# Verificar que k6 exista ANTES de crear el directorio de resultados, para
# no dejar directorios vacíos si la herramienta no está disponible.
if ! command -v k6 >/dev/null 2>&1; then
  echo "Error: k6 no está disponible en el PATH." >&2
  exit 1
fi

# Configuración de persistencia (idéntica a vegeta_attack.sh)
RESULTS_ROOT="${SCRIPT_DIR}/results"
RUN_ID="$(date '+%Y%m%d_%H%M%S')"
RESULT_DIR="${RESULTS_ROOT}/${RUN_ID}"
SUFFIX=1

if ! mkdir -p "${RESULTS_ROOT}"; then
  echo "Error: no se pudo crear el directorio de resultados: ${RESULTS_ROOT}" >&2
  exit 1
fi

# Reservación atómica del directorio de la corrida: mkdir sin -p falla si el
# directorio ya existe (colisión de timestamp) y se reintenta con sufijo _N,
# de modo que corridas consecutivas nunca se sobrescriben. Si mkdir falla
# por una causa distinta a una colisión (permisos, disco, etc.), el
# directorio no existe y el script aborta en lugar de quedar en un bucle
# infinito.
while ! mkdir "${RESULT_DIR}" 2>/dev/null; do
  if [ -d "${RESULT_DIR}" ]; then
    RESULT_DIR="${RESULTS_ROOT}/${RUN_ID}_${SUFFIX}"
    SUFFIX=$((SUFFIX + 1))
  else
    echo "Error: no se pudo crear el directorio de la corrida: ${RESULT_DIR}" >&2
    exit 1
  fi
done

# Ejecutar la prueba tal cual está definida en k6_spike.js. Sin pipes: el
# exit code de k6 (distinto de cero cuando un threshold se viola) se
# conserva íntegro. Si la corrida se interrumpe a mitad, el results.json
# parcial queda conservado como evidencia dentro del directorio de la
# corrida; nunca se elimina ni se disfraza como éxito.
k6 run --out "json=${RESULT_DIR}/results.json" tests/stress/k6_spike.js
k6_status=$?
exit "${k6_status}"
