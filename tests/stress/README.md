# Tests de Carga y Estrés — POST /extract

Scripts del TP de Test de Carga y Estrés para el Microservicio de Extracción.

## Topologías de benchmark

| Modo | Comando de arranque | Punto de entrada | Descripción |
|------|--------------------|------------------|-------------|
| **Cluster (default)** | `docker compose up -d` | `http://localhost:80` | 5 réplicas del `document-service` balanceadas por Traefik |
| **Single instance** | `docker compose -f docker-compose.yml -f docker-compose.single.yml up -d` | `http://localhost:8000` | 1 réplica con puerto directo (línea base comparativa) |

Los scripts usan la variable de entorno `BASE_URL` (default: `http://localhost:80`).

## Requisitos

- [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) — test de spike
- [Vegeta](https://github.com/tsenart/vegeta) — test de carga sostenida (bash / Git Bash / WSL)

## Fixtures

`fixtures/` contiene 3 PDFs deterministas (1, 5 y 10 páginas) usados en rotación.
Para regenerarlos:

```bash
python tests/stress/fixtures/regenerate_fixtures.py
```

## 1. Test de Spike (k6)

Perfil: **0 → 100 VUs en 10s**, **100 VUs sostenidos 20s**, **100 → 0 en 10s**.

```bash
# Cluster (default)
k6 run tests/stress/k6_spike.js

# Single instance
k6 run -e BASE_URL=http://localhost:8000 tests/stress/k6_spike.js
```

Valida el contrato en cada request: status `200`, `page_count > 0` y `content` no vacío.
Umbrales iniciales (ajustables en el script): `<5%` de errores y `p(95) < 5s`.

## 2. Test de carga sostenida (Vegeta)

Inyección de **50 req/s durante 30s** con timeout de **30s** por request.

```bash
cd tests/stress

# Cluster (default)
./vegeta_attack.sh

# Single instance
BASE_URL=http://localhost:8000 ./vegeta_attack.sh
```

Notas:
- Vegeta no arma multipart por flag: el script pre-construye el cuerpo
  `multipart/form-data` con boundary fijo a partir de `fixtures/sample_5p.pdf`.
- Los resultados binarios quedan en `vegeta_results.bin` (ignorado por git) para
  análisis posterior:

```bash
vegeta report -type=json vegeta_results.bin | jq .
vegeta plot vegeta_results.bin > plot.html
```

## Nota sobre recursos

Cada réplica del `document-service` está limitada a `1.0 CPU / 512M` (sección
`deploy` de `docker-compose.yml`), por lo que las métricas reflejan contención
real de hardware comparable entre corridas.
