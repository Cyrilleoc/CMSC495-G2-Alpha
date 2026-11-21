# Unit 8 — Code Quality and Performance Evidence

**Group G-2; draft for peer review (November 2026).** All figures below have deliberately narrow scopes.

## Verified automated tests and statement coverage

- Last confirmed student Ubuntu WSL run: **51 tests passed**; a Starlette deprecation warning was non-fatal.
- Independent local replay of the Unit 5 source: **51/51 tests passed** and **96% application statement coverage** (267 executable statements, 10 missed before the database cleanup).
- After correcting SQLite initialization connection disposal, independent local replay: **51/51 tests passed**, **96.28% statement coverage** (269 statements, 10 missed). A 90% minimum quality gate was met.
- Confirmed Unit 8 GitHub Actions run: **51 passed, 1 non-fatal warning, 96.28% statement coverage** with a 90% gate, plus successful Docker build and ephemeral container API/UI smoke tests. See [the verified workflow run](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/actions/runs/44929268023).
- The run uploaded `alpha-coverage` (XML and HTML coverage), available from the workflow's Artifacts section.
- Coverage is **statement coverage**, not branch coverage; 96% does not imply secure or fully tested behavior.

Commands:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-fail-under=90
python scripts/demo_flow.py
python scripts/benchmark_retrieval.py
```

## End-to-end integration

`scripts/demo_flow.py` exercises three real HTTP paths using FastAPI TestClient: supported FAQ -> answer -> feedback; unsupported question -> ticket -> agent claim/reply; simulated external-model failure -> safe escalation. The provider failure is **mocked**, not an outage of a live external provider.

## Retrieval evaluation and benchmark

- Seven synthetic exact/paraphrased/unrelated queries: **7/7 matched the predefined expectation**.
- Previous local student WSL run: original retrieval **47.288 microseconds/query**; optimized retrieval **21.548 microseconds/query**, about **2.19x** faster on that machine.
- This measures **in-process lexical FAQ lookup**, not HTTP latency, model token latency, fairness, precision/recall over real users, or system capacity.
- The six-entry FAQ is English-only. Varying hardware and load will change timings.

## Local API microbenchmark (not a load test)

A separate Python 3.13 local replay (single-process FastAPI TestClient, in-memory request execution plus SQLite) measured:
- `GET /healthz`, n=200: p50 **0.542 ms**, p95 **0.854 ms**.
- Supported FAQ message POST, n=50: p50 **3.029 ms**, p95 **4.232 ms**.

The verified CI environment has different timing; do not combine distributions or claim these as network or production latencies. Rerun `python scripts/benchmark_api.py` for environment-specific results.

## Peer review and version control

- [PR #1: cache-control hardening](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/pull/1).
- [PR #3: integration, privacy and AI improvements](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/pull/3), including Dylan Albert's substantive review comment and follow-up correction.
- [Successful post-merge CI run (Unit 5)](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/actions/runs/44923611561).
- Unit 8 work is proposed in a distinct pull request; **do not count it as reviewed or merged until those events occur**.

## CI/CD and deployment evidence

The original workflow tested code; it did not deploy. The Unit 8 branch adds Docker image build plus HTTP health and browser-HTML smoke tests in an **ephemeral CI container**, but **not an external/staging/production deployment**. The successful run is linked above; capture its green result and downloadable coverage artifact for the final portfolio. A live public service remains unsafe due to spoofable demo headers.

## Release risks

Critical: no real authentication. High: SQLite single-instance persistence, regex-only PII handling, English-only FAQ, synchronous provider calls, no real external-model verification, no load-test results. The reliability and security evidence supports a **demonstrated educational final prototype**, not production readiness.

See [Technical Debt](TECHNICAL_DEBT.md), [Architecture](ARCHITECTURE.md), and [Deployment Guide](INSTALL_AND_DEPLOY.md).
