# CMSC 495 · Group G-2 · Customer Service Alpha (starter implementation)

**Team:** Nonvignon Oussou (Lead Architect), Dylan Albert (Interface Designer), Lo Morton (Integration Lead).  
**Status:** Verified **local prototype starter**, not a published or team-approved GitHub Alpha release.  
**Course:** CMSC 495 · Unit 5 Assignment 1.

> This package is a working reference implementation aligned with the Group G-2 Unit 3 design. It is not a substitute for the team's existing Unit 4 repository, genuine commits, peer reviews, or an actual green GitHub Actions run. Merge/adapt into that repository after reviewing team code.

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

## 5. Continuous integration

`.github/workflows/ci.yml` triggers on pushes and pull requests and performs:

1. Checkout and Python 3.13 setup.
2. Dependency installation.
3. Python source compilation.
4. Unit/integration tests with pytest.
5. A basic check that runtime secret files aren't tracked.

**Local verification:** 20 tests passed in the preparation environment. **GitHub status:** Not run; add the files to your shared team repo, push and verify that its Actions check is green. If your Unit 4 workflow already exists, preserve it and integrate these tests rather than overwriting it. Real CI status must be evidenced by a successful run in the shared repository.

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

**Use the team's real shared repository.** Do not invent a new URL in the assignment. Recommended process:

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
