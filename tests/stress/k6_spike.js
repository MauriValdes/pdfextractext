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
// BASE_URL parametrizable (12-Factor: la config vive en el entorno):
//   - Cluster (5 réplicas detrás de Traefik, default):
//       k6 run tests/stress/k6_spike.js
//   - Single instance (docker-compose.single.yml):
//       k6 run -e BASE_URL=http://localhost:8000 tests/stress/k6_spike.js
//   - Con envío binario directo (Content-Type: application/pdf):
//       k6 run -e BASE_URL=http://extract.universidad.localhost tests/stress/k6_spike.js
// =============================================================================
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:80';

// Los archivos se abren en el "init context": k6 los carga UNA sola vez
// por VU y los reutiliza en todas las iteraciones (eficiente en memoria).
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
    // Umbrales iniciales (ajustables según los objetivos del TP)
    http_req_failed: ['rate<0.05'], // menos del 5% de errores
    http_req_duration: ['p(95)<5000'], // p95 por debajo de 5s bajo spike
  },
};

export default function () {
  // Rotación round-robin de archivos por iteración
  const fixture = FIXTURES[__ITER % FIXTURES.length];

  // Enviar los bytes directos del PDF con Content-Type: application/pdf
  // Esto soporta el envío binario directo requerido por el profesor
  const res = http.post(`${BASE_URL}/extract`, fixture.data, {
    headers: { 'Content-Type': 'application/pdf' },
    timeout: '30s',
  });

  check(res, {
    'status 200': (r) => r.status === 200,
    'contrato: page_count > 0': (r) => r.status === 200 && r.json('page_count') > 0,
    'contrato: content no vacío': (r) => r.status === 200 && (r.json('content') || '').length > 0,
  });
}
