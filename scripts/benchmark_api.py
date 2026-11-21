"""Repeatable localhost-only TestClient timing of health and supported FAQ paths.

A microbenchmark, NOT a load test or production latency guarantee.
"""
import json
import os
import statistics
import tempfile
import uuid
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import create_app

HEADERS = {'X-Demo-Actor': 'perf-fixture', 'X-Demo-Role': 'customer'}


def summarize(values):
    ordered = sorted(values)
    return {
        'samples': len(ordered),
        'p50_ms': round(statistics.median(ordered), 3),
        'p95_ms': round(ordered[min(len(ordered)-1, int(len(ordered) * .95))], 3),
        'max_ms': round(ordered[-1], 3),
    }


def time_request(fn):
    start = perf_counter()
    response = fn()
    return response, (perf_counter() - start) * 1000


def main():
    os.environ['AI_PROVIDER'] = 'local'
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ['DEMO_RATE_LIMIT'] = '0'
    with tempfile.TemporaryDirectory() as temporary:
        with TestClient(create_app(Path(temporary) / 'api_benchmark.sqlite')) as client:
            health = []
            for _ in range(200):
                response, ms = time_request(lambda: client.get('/healthz'))
                assert response.status_code == 200
                health.append(ms)

            faq = []
            for _ in range(50):
                created = client.post('/v1/conversations', headers=HEADERS)
                assert created.status_code == 201
                conv = created.json()['conversation_id']
                msg_id = str(uuid.uuid4())

                def question():
                    return client.post(
                        f'/v1/conversations/{conv}/messages',
                        headers={**HEADERS, 'Idempotency-Key': str(uuid.uuid4())},
                        json={'client_message_id': msg_id, 'text': 'How do I reset my password?'},
                    )
                response, ms = time_request(question)
                assert response.status_code == 202 and response.json()['status'] == 'answered'
                faq.append(ms)
    report = {
        'scope': 'Single-process local FastAPI TestClient, synthetic FAQ, SQLite; NOT load testing',
        'healthz': summarize(health),
        'supported_faq_post': summarize(faq),
        'external_llm_called': False,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    main()
