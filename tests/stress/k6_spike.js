// =============================================================================
// Test de SPIKE con k6 - POST /extract
//
// Perfil de carga:
//   - 10s: rampa agresiva 0 -> 100 VUs
//   - 20s: meseta sostenida en 100 VUs
//   - 10s: descenso 100 -> 0 VUs
//
// Rotación de archivos: round-robin por iteración entre los fixtures PDF.
//
// Clasificación de respuestas coherente con el diseño actual de MS2:
//   - 200: extracción exitosa.
//   - 413: rechazo esperado, el PDF supera el límite de 5 MB.
//   - 503: rechazo esperado, se alcanzó la capacidad de admisión.
//   - Otros códigos: respuesta inesperada del servicio.
//
// BASE_URL parametrizable (12-Factor: la config vive en el entorno):
//   - Instancia directa publicada por docker-compose.single.yml (default):
//       k6 run tests/stress/k6_spike.js
//   - Single instance (docker-compose.single.yml):
//       k6 run -e BASE_URL=http://localhost:8088 tests/stress/k6_spike.js
// =============================================================================
import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate } from 'k6/metrics';

// Clasificación explícita de cada respuesta. Las cuatro métricas se registran
// en TODAS las solicitudes, de modo que cada Rate representa la proporción
// sobre el total y cada Counter la cantidad absoluta de su categoría.
const extractionOk = new Counter('extract_200');
const extractionOkRate = new Rate('extract_200_rate');
const rejectedBySize = new Counter('extract_413');
const rejectedBySizeRate = new Rate('extract_413_rate');
const rejectedBySaturation = new Counter('extract_503');
const rejectedBySaturationRate = new Rate('extract_503_rate');
const unexpectedStatus = new Counter('extract_unexpected_status');
const unexpectedStatusRate = new Rate('extract_unexpected_status_rate');

// Un 503 por saturación y un 413 por tamaño son respuestas esperadas del
// servicio: no deben computar como fallos en http_req_failed. Los códigos
// fuera de {200, 413, 503} y los errores de red (incluido el timeout) siguen
// contando como fallos.
http.setResponseCallback(http.expectedStatuses(200, 413, 503));

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Los archivos se abren en el "init context": k6 los carga una sola vez al
// inicializar el script, antes de iniciar los VUs, y esos datos quedan
// disponibles para todas las iteraciones de todos los VUs.
const FIXTURES = [
  { name: 'sample_1p.pdf', data: open('./fixtures/sample_1p.pdf', 'b') },
  { name: 'sample_5p.pdf', data: open('./fixtures/sample_5p.pdf', 'b') },
  { name: 'sample_10p.pdf', data: open('./fixtures/sample_10p.pdf', 'b') },
];

export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 100 }, // Spike: 0 -> 100 VUs
        { duration: '20s', target: 100 }, // Sostenido: 100 VUs
        { duration: '10s', target: 0 },   // Descenso: 100 -> 0 VUs
      ],
    },
  },
  thresholds: {
    // Solo los fallos inesperados pueden romper el umbral: la callback de
    // estados esperados ya excluye 503 (saturación) y 413 (tamaño) de
    // http_req_failed.
    http_req_failed: ['rate<0.05'],
    // p95 por debajo de 5s bajo spike.
    http_req_duration: ['p(95)<5000'],
    // Señal explícita de respuestas inesperadas: es el criterio principal
    // de fallo. 200/413/503 se observan con sus métricas sin umbral: sus
    // proporciones no hacen fallar la prueba por sí solas.
    unexpected_status_rate: ['rate<0.05'],
  },
};

// Registra la respuesta en las métricas de clasificación.
function classify(res) {
  const is200 = res.status === 200;
  const is413 = res.status === 413;
  const is503 = res.status === 503;
  const isUnexpected = !is200 && !is413 && !is503;

  extractionOkRate.add(is200);
  rejectedBySizeRate.add(is413);
  rejectedBySaturationRate.add(is503);
  unexpectedStatusRate.add(isUnexpected);

  if (is200) extractionOk.add(1);
  if (is413) rejectedBySize.add(1);
  if (is503) rejectedBySaturation.add(1);
  if (isUnexpected) unexpectedStatus.add(1);
}

export default function () {
  // Rotación round-robin de archivos por iteración
  const fixture = FIXTURES[__ITER % FIXTURES.length];

  // Enviar los bytes directos del PDF con Content-Type: application/pdf
  // Esto soporta el envío binario directo requerido por el profesor
  const res = http.post(`${BASE_URL}/extract`, fixture.data, {
    headers: { 'Content-Type': 'application/pdf' },
    timeout: '30s',
  });

  classify(res);

  if (res.status === 200) {
    // El contrato de extracción solo se interpreta sobre respuestas 200.
    check(res, {
      'status 200': (r) => r.status === 200,
      'contrato: page_count > 0': (r) => r.json('page_count') > 0,
      'contrato: content no vacío': (r) => (r.json('content') || '').length > 0,
    });
  } else {
    // 413 y 503 son rechazos esperados; su cuerpo NO se interpreta como
    // JSON de extracción. Un código distinto de 413/503 hace fallar este
    // check y queda registrado en las métricas de inesperados.
    check(res, {
      'rechazo esperado (413/503)': (r) => r.status === 413 || r.status === 503,
    });
  }
}
