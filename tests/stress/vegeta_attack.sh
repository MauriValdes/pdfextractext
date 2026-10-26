#!/bin/bash

# Configuración de variables
RATE="50/1s"
DURATION="30s"
TARGETS="tests/stress/targets.txt"
BIN_OUTPUT="tests/stress/results.bin"
JSON_OUTPUT="tests/stress/results.json"
PLOT_OUTPUT="tests/stress/results.html"

# 1. Ejecutar el ataque, almacenar binario y mostrar reporte en consola
vegeta attack -rate="${RATE}" -duration="${DURATION}" -targets="${TARGETS}" | tee "${BIN_OUTPUT}" | vegeta report

# 2. Generar reporte JSON para análisis automático
vegeta report -type=json < "${BIN_OUTPUT}" > "${JSON_OUTPUT}"

# 3. Generar gráfico interactivo HTML para visualización en navegador
vegeta plot < "${BIN_OUTPUT}" > "${PLOT_OUTPUT}"