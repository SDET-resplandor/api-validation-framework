import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 50 },
    { duration: '20s', target: 150 },
    { duration: '20s', target: 300 },
    { duration: '20s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/products?limit=10');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}