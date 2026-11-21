# CMSC 495 · Group G-2 · Customer Service Final Portfolio (Local Prototype)

**Team:** Nonvignon Oussou (Lead Architect), Dylan Albert (Interface Designer), Lo Morton (Integration Lead).  
**Status:** Group G-2 shared Alpha prototype, with PR-based peer review and CI checks. Not production-ready.  
**Course:** CMSC 495 · Unit 8 Final Project Portfolio.

> **Group repository:** https://github.com/Cyrilleoc/CMSC495-G2-Alpha. Review the latest pull requests, commits, and Actions checks for current evidence. This remains a local coursework prototype, not a deployed production service.

## Unit 8 final portfolio — start here

The integrated educational application now has repeatable customer-to-agent demonstrations, **51 passing tests**, a 90% CI statement-coverage gate (**96.28% observed in the verified Unit 8 branch CI**), a local-demo Docker image and an ephemeral CI container smoke test. These are **not a public deployment** or proof of production security.

- [Final portfolio plan, evidence matrix and video outline](docs/UNIT8_PORTFOLIO.md)
- [Quality metrics and coverage limits](docs/QUALITY_REPORT.md)
- [API reference](docs/API_REFERENCE.md) · [End-user manual](docs/USER_GUIDE.md)
- [Installation and local deployment](docs/INSTALL_AND_DEPLOY.md)
- [Technical stakeholder video storyboard](docs/VIDEO_DEMO_STORYBOARD.md)
- [Technical debt and remaining security gates](docs/TECHNICAL_DEBT.md)
- [Verified vs. pending team contributions](docs/CONTRIBUTIONS.md)

To reproduce tests and quality evidence locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=90
python scripts/demo_flow.py
python scripts/benchmark_retrieval.py
python scripts/benchmark_api.py
```

**Security:** This coursework system trusts fake demo role headers and must remain on localhost. Before any external release, replace them with real verified authentication and complete security, privacy and scale validation.

---

## 1. Working Alpha scope

- Customer opens a conversation and sends a question.
- A separate `app.ai` module retrieves an approved example FAQ entry using lexical similarity; answers cite a source ID. This is a **retrieval-based prototype**, not a trained generative model.
- Unrecognized or explicit human-support requests create tickets; agent lists tickets, claims with optimistic-version protection, and replies.
- The feedback endpoint records helpful/not-helpful assessments for manual review. The UI includes feedback buttons.
- Structured input validation, object-owner checks, duplicate message handling, 429 demonstration, and RFC 9457-style errors.
- Local browser demo at `/`, interactive OpenAPI docs at `/docs`, isolated backend tests, GitHub Actions workflow.
- Optional **LLM-backed answer paraphrase** uses OpenAI's Responses API, but only if explicitly configured with a real API key and an available model. Without credentials, the working retrieval mode is used instead. Model integration is not proven by the local tests.

This Alpha uses **synthetic** FAQ content. No existing CRM, production customer records, real OIDC authentication, SSE, message broker, or 10,000-concurrent-user performance test has been implemented.

## 2. Install and run locally (WSL/Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/** to try the customer and agent demo.

For Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1` instead.

**Never bind this sample directly to a public network:** `X-Demo-Actor` / `X-Demo-Role` headers are spoofable and are intentionally used *only* in local test scenarios. A secure authentication and authorization layer is required before external deployment.

### Example demo

1. Click **Start conversation** and ask `How can I reset my password?` → chatbot responds with reviewed FAQ answer and `FAQ-001` source.
2. Ask `What is astrophysics?` → safe fallback creates an escalation ticket.
3. Click **Refresh tickets**, claim the ticket, and reply as `agent-one`.
4. Click **Refresh messages** to see the agent response.
5. Ask the password question again and click **Helpful answer** to store feedback.

### Optional hosted-model integration (not required for local demo)

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY='<your own secret, NEVER commit>'
export OPENAI_MODEL='gpt-5.5'  # change to a model available to your account
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The model is instructed only to paraphrase retrieved, approved FAQ content. On provider failure, the application escalates instead of inventing answers. Do not record a model demonstration as passed unless you have executed it with actual credentials and checked its response. Using an external model may incur API charges.

## 3. Project structure

```text
app/
  main.py          Core HTTP API, conversation, tickets, feedback
  db.py            SQLite persistence adapter
  ai.py            Chatbot orchestration and optional hosted model
  knowledge.py     Approved FAQ dataset and retrieval scoring
  static/index.html Local demo customer + agent UI
.github/workflows/ci.yml  CI build/test workflow (example)
tests/test_alpha.py       Unit and API integration tests
docs/                    Architecture notes, peer review and technical debt
```

## 4. API routes (base `/v1`)

| Method | Route | Prototype behavior |
|---|---|---|
| POST | `/conversations` | Create conversation for demo customer |
| POST | `/conversations/{id}/messages` | Persist question, answer or escalate; status 202 |
| GET | `/conversations/{id}/messages` | Customer-only history |
| POST | `/conversations/{id}/escalations` | Manual human escalation |
| GET | `/agent/tickets` | Agent ticket queue |
| POST | `/agent/tickets/{id}/claim` | Agent claim, optimistic version |
| POST | `/agent/tickets/{id}/replies` | Reply in claimed conversation |
| POST | `/conversations/{id}/feedback` | Queue feedback for review |
| GET | `/healthz`, `/docs` | Health and OpenAPI schema |

API calls use JSON; `POST /messages` requires an `Idempotency-Key` UUID header and `client_message_id` UUID in the body. Other end points enforce basic Pydantic validation. All demo business routes use `X-Demo-Actor` and `X-Demo-Role` headers **as an insecure local stub**.

Example using `curl`:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/conversations \
  -H 'X-Demo-Actor: customer-one' -H 'X-Demo-Role: customer'
```

Use the returned conversation UUID with `/v1/conversations/{id}/messages`. A completed example is available in the browser UI.

### API Response Caching Policy

All customer and agent API responses under `/v1/` include `Cache-Control: no-store`. This directs compliant browsers and intermediary caches not to store potentially sensitive conversation, ticket, or error-response information, including HTTP 429 rate-limit responses.

Automated tests cover API 401, 403 and 429 caching policy and confirm `/healthz` and `/` are not automatically marked `no-store`.

This header is an additional privacy safeguard; it does not replace authentication, authorization, secure transport, or responsible data and log handling.

## 5. Continuous integration and local deployment validation

`.github/workflows/ci.yml` triggers on pushes and pull requests. It installs Python dependencies, compiles source, runs pytest with a **90% minimum statement-coverage gate**, uploads HTML/XML coverage artifacts, verifies all three end-to-end HTTP scenarios, runs FAQ and API microbenchmarks, screens tracked filenames for obvious secrets, and builds/smoke-tests an ephemeral container on the runner.

**Verified Unit 8 branch:** 51 tests passed; 96.28% statement coverage; container API and HTML smoke tests passed. See the latest [GitHub Actions workflow](https://github.com/Cyrilleoc/CMSC495-G2-Alpha/actions) and [quality report](docs/QUALITY_REPORT.md). This is not automatic deployment to an external host.

## 6. Security and technical-debt honesty

Not production-ready. Identified gaps:

- **Critical: Demo identity headers are spoofable.** Replace with OIDC/JWT verification, per-object role/tenant authorization and security tests before public exposure.
- **SQLite/single instance:** Migrate to PostgreSQL and a migration system; use real connection management, scale tests and proper backups.
- **Synchronous AI calls:** Add a durable job/outbox/queue, timeouts, retries, and idempotent worker processing consistent with the Unit 3 architecture.
- **Simplistic FAQ ranking:** Replace lexical scoring with a curated retrieval approach and measured evaluation set, grounding checks, and feedback review. Avoid treating the reported lexical score as calibrated AI confidence.
- **Optional LLM calls:** Hosted-model path remains untested without real credentials; redact sensitive data using robust enterprise controls, not only the email/phone examples in this starter.
- **Rate limiting:** The optional in-memory limiter is not valid across multiple replicas. Use a shared store (Redis) and sensible quotas.
- **Coverage:** Expand tests for database outages, concurrent duplicate requests, AI provider behavior, permissions, accessibility, and load.
- **No real CRM adapter or SSE:** Add documented adapters and streamed events in later iterations.

See `docs/TECHNICAL_DEBT.md` for mitigation priorities.

## 7. GitHub submission instructions

**Use the shared Group G-2 repository linked above.** Develop changes on feature branches, use PR review, and confirm automated checks before merging. Example workflow:

```bash
# In the actual team clone:
git checkout -b feature/unit5-alpha
# copy/merge reviewed files from this starter into the existing repository
python -m pytest -q
git add .
git commit -m 'feat(alpha): integrate customer chat FAQ escalation and feedback'
git push -u origin feature/unit5-alpha
```

Open a pull request for peer review, address comments, merge when green, and capture a screenshot of the successful workflow. Provide the actual repository URL in the Team Component submission. Confirm everyone has the required access.

## 8. Division of work / evidence

- **Nonvignon Oussou / Lead Architect:** oversee architecture compatibility, review database and service boundaries, resolve integration risks.
- **Dylan Albert / Interface Designer:** evaluate API contracts, UI accessibility, validation and error-response consistency.
- **Lo Morton / Integration Lead:** evaluate AI retrieval, source grounding, provider failures, escalation and feedback integration.

These are role-aligned responsibilities, **not claims that a member completed them**. Actual commits and reviews should record who performed which activity.

## 9. Unit 5 individual requirement

Each person must review **one teammate's real module** and submit an **exactly 250-word Refinement Report** containing evidence: file/PR, findings, changes actually made in response, technical debt, mitigation, and impact. See `docs/PEER_REVIEW_WORKSHEET.md`. Do not present hypothetical examples as completed reviews.

## Sources

- FastAPI TestClient: https://fastapi.tiangolo.com/tutorial/testing/
- GitHub Actions Python setup: https://github.com/actions/setup-python
- OpenAI Python Responses API: https://developers.openai.com/api/reference/python

## Unit 5 instructor-feedback revision (November 2026)

Following Dr. Shaalan's feedback, the group prepared a stronger API-level demonstration, privacy/error-path tests, a precomputed FAQ retrieval index, and a separate optional hosted-model provider adapter. The original demonstration-only identity system remains insecure; **do not deploy publicly**.

From the repository root, after installing dependencies, execute these commands:

- `python -m pytest -q`
- `python scripts/demo_flow.py`
- `python scripts/benchmark_retrieval.py`

See [Unit 5 Revision Evidence](docs/UNIT5_REVISION_EVIDENCE.md) for specific supported, unsupported and simulated provider-failure scenarios. See [Technical Debt](docs/TECHNICAL_DEBT.md) for implemented versus outstanding mitigations.

In a local preparation environment, 51 tests passed and the six-entry FAQ retrieval benchmark showed an illustrative ~2.6x speedup while retaining expected results on seven curated questions. **These are not production reliability, fairness or real hosted-model results.** Check the current revision pull request and GitHub Actions for fresh remote CI results. Earlier 22/23-test counts elsewhere in this document refer to the original Alpha.
