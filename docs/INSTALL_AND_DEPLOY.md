# Installation, Local Demo Deployment, and Release Checklist

**Important:** This is a **local/demo deployment guide**, not a production release. Caller-controlled `X-Demo-Actor`/`X-Demo-Role` headers make any public network deployment unsafe.

## Option A: Python + Ubuntu WSL

```bash
git clone https://github.com/Cyrilleoc/CMSC495-G2-Alpha.git
cd CMSC495-G2-Alpha
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=90
python scripts/demo_flow.py
python scripts/benchmark_retrieval.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/docs`.

## Option B: Containerized local demo

```bash
docker build -t g2-alpha-demo .
docker run --rm --name g2-alpha-demo -p 127.0.0.1:8000:8000 -e AI_PROVIDER=local g2-alpha-demo
```

In another terminal: `curl --fail http://127.0.0.1:8000/healthz`. The Dockerfile runs as a non-root user, initializes a local SQLite file in the container, and exposes port 8000. Any data is temporary unless you deliberately mount a data volume; production backup/restore is **not provided**.

## CI and ephemeral deployment validation

GitHub Actions on pushes/PRs runs Python compilation, automated tests, statement coverage (minimum 90%), scripted full-API demonstration, lexical FAQ benchmark, an obvious-secret filename check, and a Docker build followed by an HTTP `/healthz` and web-UI smoke test. The container is exposed only to loopback on the CI runner and removed after the check.

**This is continuous integration with deployment validation, not continuous delivery to a hosted environment.** Do not claim a public live URL or a tested production deployment.

## Release gates for a real service (NOT completed)

- Implement verified OIDC/JWT credentials and object/tenant authorization.
- Add privacy-preserving logging, risk-approved data handling, and comprehensive PII protection.
- Add secure secret management, TLS, backups, migrations and externally managed databases.
- Replace single-process rate limiting with shared/distributed controls.
- Run accessibility testing, multilingual fairness evaluation, external-provider integration tests and scalability/load tests.
- Define deployment approvals, rollback and operational SLOs.

See [Technical Debt](TECHNICAL_DEBT.md).
