import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 10 },
    { duration: '5s', target: 300 },
    { duration: '20s', target: 300 },
    { duration: '5s', target: 10 },
    { duration: '10s', target: 10 },
  ],
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/products?limit=10');
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}