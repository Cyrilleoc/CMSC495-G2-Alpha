# Technical Debt Register — Group G-2 (Unit 5 revision)

Items below distinguish implemented mitigation from outstanding work. Priorities apply before any production deployment.

| ID | Finding / impact | Status | Next mitigation | Priority | Verification / proposed owner |
|---|---|---|---|---|---|
| TD-01 | Demo identity headers are spoofable | OPEN | Replace with signed OIDC/JWT identities, object authorization and token tests | Critical | Authorization tests; Lead Architect and Interface Designer |
| TD-02 | SQLite cannot support reliable multi-instance scale | OPEN | PostgreSQL and migrations | High | Concurrency and backup tests; Lead Architect |
| TD-03 | Synchronous AI processing; previously coupled routing/provider | PARTIAL: separated provider adapter | Add job queue, outbox, timeouts/retries | High | Provider failure and blank response tests; Integration Lead |
| TD-04 | Repeated FAQ tokenization on every request | IMPLEMENTED: cached FAQ vectors | Rebuild index for changing data; diverse retrieval tests | High | Old/new algorithm equivalence and benchmark; Integration Lead |
| TD-05 | External LLM not verified with real credentials | OPEN | Approved sandbox integration test | High | Real sandbox provider run; Integration Lead |
| TD-06 | In-memory limiter does not work across replicas | OPEN | Shared Redis quota service | Medium | Multi-instance tests; Lead Architect |
| TD-07 | Basic PII masking can leak sensitive inputs | PARTIAL: phone and email examples expanded and tested | Enterprise DLP/privacy controls for real data | Critical | Parameterized redaction, fake provider prompt and logs; Whole team |
| TD-08 | Missing operational telemetry and load tests | OPEN | Observability, staging load tests and SLOs | Medium | Load-test evidence; Whole team |
| TD-09 | Cache response policy duplicated between normal and early 429 paths | IMPLEMENTED: reusable no_store() helper | Continue status code coverage | Medium | Tests for 401, 403, 429 and non-API routes; Interface Designer |
| TD-10 | Six English-only sample FAQ entries | OPEN | Multilingual, grounded evaluation and human escalation | High | Evaluation across representative questions; Whole team |

## Professional review process

1. Verify module authorship before crediting a teammate's contribution.
2. Record peer review on the current revision PR for readability, security, performance, integration and documentation.
3. Address feasible review comments, add tests and update this register with verifiable links.
4. Merge only after CI success and actual teammate approval. Keep individual 250-word reports separate.
5. Do not represent redaction as comprehensive DLP, mocked provider tests as real hosted-model evidence, or a seven-question fixture as production accuracy.
