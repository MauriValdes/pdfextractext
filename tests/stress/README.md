# Tests de Carga y Estrés — POST /extract

Scripts del TP de Test de Carga y Estrés para el Microservicio de Extracción.

## Modalidad de ejecución

| Modo | Comando de arranque | Punto de entrada | Descripción |
|------|--------------------|------------------|-------------|
| **Instancia directa** | `docker compose -f docker-compose.yml -f docker-compose.single.yml up -d` | `http://localhost:8000` | 1 réplica publicada directamente para desarrollo y benchmark |
| **Réplicas manuales** | `docker compose up -d --scale document-service=N` | Red Docker, puerto `8000` | Varias réplicas sin proxy ni publicación de puerto host común |

Los scripts apuntan por defecto a `http://localhost:8000` y aceptan `BASE_URL` para seleccionar otro host/puerto. Las pruebas directas con k6 y Vegeta deben ejecutarse contra una instancia publicada mediante el override single; las réplicas manuales no proporcionan un endpoint host balanceado. En el sistema integrado, el acceso de usuarios se realiza mediante MS1.

## Requisitos

- [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) — test de spike.
- [Vegeta](https://github.com/tsenart/vegeta) — test de carga sostenida (bash / Git Bash / WSL).
- `uv` — utilizado por `vegeta_attack.sh` para el clasificador de resultados (no se requiere `jq`).

## Fixtures y corpus

- `fixtures/` contiene 3 PDFs deterministas (1, 5 y 10 páginas) usados por **k6**, cargados desde el propio `k6_spike.js` (rotación round-robin). Para regenerarlos:

  ```bash
  python tests/stress/fixtures/regenerate_fixtures.py
  ```

- `targets.txt` pertenece a **Vegeta**: define los targets (`POST /extract`, envío binario con `Content-Type: application/pdf`) sobre el corpus de `pdfs/`. Se conserva deliberadamente como está; no debe modificarse para las corridas de esta etapa.

## Resultados

La raíz única de resultados es `tests/stress/results/` (ignorada por git). Cada ejecución queda aislada en su propio directorio por timestamp:

```text
tests/stress/results/
└── AAAAMMDD_HHMMSS[_N]/
```

El sufijo `_1`, `_2`, … resuelve colisiones de timestamp (dos corridas dentro del mismo segundo); la reservación del directorio es atómica, por lo que ninguna corrida sobrescribe otra. No se utilizan rutas fijas en la raíz de `tests/stress/`.

## 1. Test de Spike (k6)

Script: `tests/stress/k6_spike.js`. Wrapper de ejecución: `tests/stress/k6_spike.sh`.

### Perfil de carga

Executor `ramping-vus` con `startVUs: 0`, duración total 40s:

- 10s: rampa 0 → 100 VUs (spike)
- 20s: meseta sostenida en 100 VUs
- 10s: descenso 100 → 0 VUs

Timeout por solicitud: `30s`.

### Comportamiento

- Envío **binario directo** del PDF con `Content-Type: application/pdf` (no es multipart).
- Rotación round-robin de los 3 fixtures mediante `__ITER % 3`.
- `BASE_URL` se toma de `__ENV.BASE_URL` (12-Factor); default `http://localhost:8000`.
- Clasificación propia de cada respuesta mediante métricas propias (Counter + Rate por categoría, registradas en todas las solicitudes): `200`, `413`, `503` e inesperados.
- `http.setResponseCallback(http.expectedStatuses(200, 413, 503))`: solo los fallos inesperados y los errores de red computan en `http_req_failed`.
- El contrato de extracción (`page_count > 0`, `content` no vacío) se valida **solamente sobre respuestas 200**; los 413/503 son rechazos esperados y no se interpretan como JSON de extracción.

### Thresholds

- `http_req_failed rate<0.05`
- `http_req_duration p(95)<5000`
- `unexpected_status_rate rate<0.05`

### Ejecución

Forma recomendada (crea el directorio de resultados por corrida):

```bash
# Instancia directa (default)
tests/stress/k6_spike.sh

# Puerto host alternativo (BASE_URL heredada al script k6)
BASE_URL=http://localhost:8088 tests/stress/k6_spike.sh
```

El wrapper:

1. verifica que `k6` esté disponible antes de crear directorios;
2. crea `tests/stress/results/AAAAMMDD_HHMMSS[_N]/`;
3. ejecuta `k6 run --out "json=<corrida>/results.json" tests/stress/k6_spike.js` sin redefinir VUs, duración, stages ni timeout;
4. hereda `BASE_URL` del entorno (no hardcodea ninguna URL);
5. conserva el exit code de k6 (una corrida que viola un threshold no queda reportada como exitosa).

Ejecución directa (sin persistencia de resultados):

```bash
k6 run tests/stress/k6_spike.js
k6 run -e BASE_URL=http://localhost:8088 tests/stress/k6_spike.js
```

### Artefactos por corrida

Únicamente `results.json` (formato propio de k6: muestras de métricas + resumen final con thresholds y las métricas de clasificación). k6 no dispone de una salida HTML nativa equivalente a `vegeta plot`, por lo que no se genera `results.html`, y la clasificación ya vive en las métricas del script, por lo que no se genera `results_clasificacion.txt`.

## 2. Test de carga sostenida (Vegeta)

Script: `tests/stress/vegeta_attack.sh`.

### Configuración

- Inyección de **50 req/s durante 30s** (`RATE="50/1s"`, `DURATION="30s"`).
- Timeout **explícito** de `30s` por solicitud (`-timeout="${TIMEOUT}"`).
- `BASE_URL` parametrizable (default `http://127.0.0.1:8000`); los targets de `targets.txt` se reescriben a ese valor al momento de la corrida.
- Corpus de `targets.txt` conservado deliberadamente sin cambios (4 targets binarios `application/pdf`; uno supera los 5 MB y por lo tanto genera `413`).

### Ejecución

```bash
# Instancia directa (default)
tests/stress/vegeta_attack.sh

# Puerto host alternativo
BASE_URL=http://localhost:8088 tests/stress/vegeta_attack.sh
```

### Clasificación de resultados

Además del reporte nativo de Vegeta, el script clasifica cada respuesta y persiste `results_clasificacion.txt` en el directorio de la corrida:

| Código | Significado |
|--------|-------------|
| `200` | Extracción exitosa |
| `413` | Rechazo esperado por tamaño (> 5 MB) |
| `503` | Rechazo esperado por saturación (backpressure) |
| `0` | Timeout / error de conexión |
| otros | Respuestas inesperadas |

Tasas calculadas (denominador: el total de solicitudes emitidas, no solo las completadas):

- Tasa de extracción: `200 / total`
- Tasa ajustada: `(200 + 413 + 503) / total` — proporción de solicitudes ante las cuales el servicio se comportó según su diseño
- Tasa de fallos inesperados: `(0 + otros) / total`

Nota: el campo `success` nativo de Vegeta (considera exitoso todo código `< 500`) **no debe usarse como métrica principal**: cuenta `413` como éxito y confunde `503` con `500`.

### Artefactos por corrida

```text
tests/stress/results/AAAAMMDD_HHMMSS[_N]/
├── results.bin
├── results.json
├── results.html
└── results_clasificacion.txt
```

El `results.json` de Vegeta tiene un formato distinto al de k6: son herramientas diferentes y la simetría está en la estructura de directorios, no en el formato interno. La comparabilidad entre ambas herramientas se apoya en el lenguaje de categorías común (`200/413/503/inesperados`).

## Nota sobre recursos

Cada réplica del `document-service` está limitada a `1.0 CPU / 1024M` (sección `deploy` de `docker-compose.yml`). El número de réplicas se define manualmente con `--scale`.
