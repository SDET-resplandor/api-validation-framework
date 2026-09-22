import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.05'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/products?limit=10');
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}