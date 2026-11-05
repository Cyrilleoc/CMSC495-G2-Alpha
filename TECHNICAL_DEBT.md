# Technical-debt register · Alpha release

| ID | Debt / shortcut | Reliability or security impact | Next action | Priority | Owner proposal |
|---|---|---|---|---|---|
| TD-01 | Demo role/actor headers instead of signed identity tokens | Anyone can spoof the actor or agent in a public deployment | Add OIDC/JWT auth middleware, role checks, tenancy tests; block public deploy | **Critical** | Lead Architect + Interface Designer |
| TD-02 | SQLite instead of PostgreSQL and migrations | Poor multi-instance scaling and operational durability | Add PostgreSQL repository and managed migrations | High | Lead Architect |
| TD-03 | Synchronous AI processing, no durable events | Requests may block, duplicate processing under retries | Outbox and worker queue, idempotency, time budgets | High | Integration Lead |
| TD-04 | Lexical FAQ similarity as basic NLU | Incorrect matches and uncalibrated confidence | Curated evaluation set and measured retrieval threshold | High | Integration Lead |
| TD-05 | External LLM optional and unverified by local CI | Runtime integration may fail even when mocks pass | Sandbox integration test with real key, timeout and fallback evidence | High | Integration Lead |
| TD-06 | In-memory optional rate limiter | Does not enforce quotas across replicas | Redis shared rate limiter with tests and `Retry-After` | Medium | Lead Architect |
| TD-07 | Minimal PII redaction and example-only FAQ | Potential leakage of sensitive input and unsupported answer | Enforce approved-content policy, comprehensive PII review | Critical for real data | Whole team |
| TD-08 | No operational monitoring, load test, or 10k-user validation | No verified scaling, SLO or on-call visibility | Add observability and staged load test | Medium | Whole team |

## Review protocol

1. Review one teammate's module against readability, security, performance, integration, documentation.
2. Link the exact pull request and record reproducible findings in review comments.
3. Change the code and add a test; run CI. Record before/after evidence.
4. Describe unresolved debt and mitigation priority, rather than claiming all problems were fixed.
