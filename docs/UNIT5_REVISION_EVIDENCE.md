# Group G-2 — Unit 5 Professor-Feedback Revision Evidence

**Members:** Nonvignon Oussou (Lead Architect), Dylan Albert (Interface Designer), Lo Morton (Integration Lead).
**Prior score:** 150/180 on November 20, 2026 (Functionality 25/40; Integration 35/40; CI 30/35; Peer Review 30/35; Technical Debt 30/30).

## Changes and how to verify them

| Feedback | Implementation | Verification |
|---|---|---|
| Complete Alpha journey | Scripted customer-to-chatbot-to-agent HTTP demonstration | python scripts/demo_flow.py |
| API integration | TestClient requests through API, retrieval, answer, escalation, agent reply and feedback | python -m pytest -q (51 local tests) |
| Security/privacy | Parameterized email and US phone redaction, 401/403/429 cache headers, simulated provider payload/log inspection | tests/test_revision.py |
| External provider failure | Provider call isolated into provider_paraphrase() with safe fallback | Exception, blank and empty response tests |
| FAQ performance | Cached tokenized FAQ vectors | Equivalence tests, 7 curated questions, benchmark_retrieval.py |
| Technical debt | Updated ledger with status, impact, priority and verification method | docs/TECHNICAL_DEBT.md |

## Three required demo scenarios

1. **Supported:** customer creates conversation (HTTP 201); asks about a password reset (HTTP 202); FAQ-001 answer returned; helpful feedback stored (HTTP 201).
2. **Unsupported:** customer asks unrelated astrophysics question (HTTP 202); bot creates a ticket; agent lists, claims (HTTP 200), replies (HTTP 201); customer retrieves agent reply.
3. **Provider failure:** simulated external provider raises exception; customer request returns HTTP 202 with status escalated, reason provider_unavailable and support ticket.

The external provider is STUBBED; no live model calls or credentials are used.

## Performance and integrity evidence

Preparation-environment results: **51 tests passed**, three HTTP demos passed, curated 7/7 exact/paraphrase/unrelated checks matched expected outputs. Old implementation median ~30–32 microseconds/query versus optimized ~12 microseconds/query (~2.6x illustrative speedup). Timing depends on runtime/hardware. Seven synthetic items do NOT prove model fairness, multilingual accuracy, or production throughput.

## Capture fresh evidence in WSL and GitHub

From repository root run, in order:

1. python -m pip install -r requirements.txt
2. python -m pytest -q
3. python scripts/demo_flow.py
4. python scripts/benchmark_retrieval.py

Screenshot each completed command and the new GitHub Actions workflow triggered by the revision PR. Ask a teammate to review the PR, link comments and update individual reports accurately.

## Open limitations

This demo trusts caller-supplied identity headers and must not be publicly deployed. Regex masking is not production DLP. FAQ contents are synthetic English examples. SQLite, synchronous model calls and in-memory throttling are not production architecture. Hosted LLM performance is not verified here.
