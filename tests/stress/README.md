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

## Fixtures

`fixtures/` contiene 3 PDFs deterministas (1, 5 y 10 páginas) usados en rotación.

Para regenerarlos:

```bash
python tests/stress/fixtures/regenerate_fixtures.py
```

## 1. Test de Spike (k6)

Perfil: **0 → 100 VUs en 10s**, **100 VUs sostenidos 20s**, **100 → 0 en 10s**.

```bash
# Instancia directa (default)
k6 run tests/stress/k6_spike.js

# Puerto host alternativo
k6 run -e BASE_URL=http://localhost:8088 tests/stress/k6_spike.js
```

Valida el contrato en cada request: status `200`, `page_count > 0` y `content` no vacío.

Umbrales iniciales (ajustables en el script): `<5%` de errores y `p(95) < 5s`.

## 2. Test de carga sostenida (Vegeta)

Inyección de **50 req/s durante 30s** con timeout de **30s** por request.

```bash
# Instancia directa (default)
tests/stress/vegeta_attack.sh

# Puerto host alternativo
BASE_URL=http://localhost:8088 tests/stress/vegeta_attack.sh
```

Notas:

- Vegeta no arma multipart por flag: el script pre-construye el cuerpo `multipart/form-data` con boundary fijo a partir de `fixtures/sample_5p.pdf`.
- Los resultados binarios quedan en `tests/stress/results.bin` (ignorado por git) para análisis posterior:

```bash
vegeta report -type=json tests/stress/results.bin | jq .
vegeta plot tests/stress/results.bin > tests/stress/results.html
```

## Nota sobre recursos

Cada réplica del `document-service` está limitada a `1.0 CPU / 1024M` (sección `deploy` de `docker-compose.yml`). El número de réplicas se define manualmente con `--scale`.
