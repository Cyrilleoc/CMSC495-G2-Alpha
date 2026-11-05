# Verified local demo flow (generated from a real TestClient execution)

The values below reflect actual request/response behavior of this standalone prototype. They do not claim a production deployment, human peer review, or a successful GitHub run.

| Step | Actual observed result |
|---|---|
| Create conversation | UUID returned (f387f751...) |
| Send supported FAQ question | `answered`; `source_ids=['FAQ-001']` |
| Send unsupported question | `escalated`; queued ticket created |
| Agent claims ticket | `assigned`; version `1` |
| Agent posts reply | HTTP `201` |
| Submit helpful feedback | `queued` |
| Retrieve history | `4` messages; roles: customer, assistant, customer, agent |

Status: LOCAL PASS. Runtime: FastAPI TestClient + SQLite. GitHub CI: NOT VERIFIED.
