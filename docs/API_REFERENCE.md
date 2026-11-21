# Customer Service API Reference — Group G-2

**Scope:** Local educational prototype. Base URL: `http://127.0.0.1:8000`. Interactive schema: `/docs` and OpenAPI JSON: `/openapi.json`.

## Demonstration identity

For local testing, supply `X-Demo-Actor: customer-one` and `X-Demo-Role: customer`; agent calls use `X-Demo-Actor: agent-one` and `X-Demo-Role: agent`. **These caller-controlled headers are not authentication. Do not expose the application publicly.**

## Routes

| Method | Path | Meaning | Successful HTTP |
|---|---|---|---|
| GET | `/healthz` | Liveness check | 200 |
| GET | `/` | Local customer/agent web UI | 200 |
| POST | `/v1/conversations` | Open conversation for customer | 201 |
| POST | `/v1/conversations/{uuid}/messages` | Submit question; answer or create ticket | 202 |
| GET | `/v1/conversations/{uuid}/messages` | Customer's message history | 200 |
| POST | `/v1/conversations/{uuid}/escalations` | Request human help | 201 |
| GET | `/v1/agent/tickets` | Agent ticket queue | 200 |
| POST | `/v1/agent/tickets/{uuid}/claim` | Assign queued ticket | 200 |
| POST | `/v1/agent/tickets/{uuid}/replies` | Post response to claimed ticket | 201 |
| POST | `/v1/conversations/{uuid}/feedback` | Submit assistant-message rating | 201 |

## Sample interaction

Start a conversation:

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/conversations \
  -H 'X-Demo-Actor: customer-one' -H 'X-Demo-Role: customer'
```

Copy the returned `conversation_id` and supply a new UUID for each request:

```bash
curl -sS -X POST "http://127.0.0.1:8000/v1/conversations/REPLACE_UUID/messages" \
  -H 'Content-Type: application/json' \
  -H 'X-Demo-Actor: customer-one' -H 'X-Demo-Role: customer' \
  -H "Idempotency-Key: $(python -c 'import uuid;print(uuid.uuid4())')" \
  -d "{\"client_message_id\":\"$(python -c 'import uuid;print(uuid.uuid4())')\",\"text\":\"How do I reset my password?\"}"
```

For a supported question, the body includes `status: answered`, `reply`, `source_ids`, and `assistant_message_id`; unsupported queries return `status: escalated` and a `ticket_id`. The `confidence` is lexical similarity, **not** a calibrated probability.

## Input and errors

Message length: 1–2,000 characters. `client_message_id` and `Idempotency-Key` are UUIDs. Optional `locale` defaults to `en-US`; **multilingual retrieval is not implemented**. Claim request body uses a nonnegative integer `version`. Feedback requires an assistant `message_id` and `rating` of `helpful` or `not_helpful`.

Errors may use 401 (missing demo identity), 403 (role), 404 (not found or not owned), 409 (stale ticket claim), 422 (invalid input), and 429 (optional demonstration rate limiter). API error bodies use `application/problem+json`. All `/v1/` responses include `Cache-Control: no-store`.

## Implementation limits

SQLite is single-instance and does not establish high availability. The lexical FAQ contains only six synthetic English examples; optional hosted-model paraphrasing is **not verified with live credentials**. For exact schema and field definitions use the runtime `/openapi.json`.
