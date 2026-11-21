# Group G-2 — Local User Manual

## Purpose

This educational customer-service application supports a customer question, FAQ answer, human escalation, and feedback in one local browser. Use **synthetic data only**.

## Get started

1. Follow [Installation & Demo Deployment](INSTALL_AND_DEPLOY.md) to start the local server.
2. Open `http://127.0.0.1:8000/`.
3. Choose the demo customer identity shown by the interface. The identities are unverified and for local training only.
4. Select **Start conversation**, then ask `How do I reset my password?`.
5. The bot returns the approved FAQ answer with a traceable source ID.
6. Ask `What is astrophysics?`. This should create an escalation ticket because no suitable FAQ exists.
7. In the agent section, refresh the tickets, claim the queued ticket, and send a human response.
8. Refresh the customer's message history to see the agent reply.
9. Ask a supported FAQ question again and submit helpful/not-helpful feedback.

## What happens when AI is unavailable?

A known FAQ answer can be served locally without an external language model. If the optional hosted provider is configured but fails, the application returns an escalation decision. The repository includes a **simulated** provider-failure demonstration; that test does not contact an outside model.

## Evidence commands

```bash
python -m pytest -q
python scripts/demo_flow.py
python scripts/benchmark_retrieval.py
```

The scripts use synthetic scenarios, not production accounts. The benchmark has only seven curated questions and must not be presented as generalized AI accuracy.

## Troubleshooting

- `No module named pytest`: activate the virtual environment and install `requirements.txt` and `requirements-dev.txt`.
- Address in use: start Uvicorn on another local port, for example `--port 8001`.
- Missing ticket: confirm your question is unsupported or explicitly requests a human.
- No hosted-model responses: the default `AI_PROVIDER=local` deliberately uses approved FAQ retrieval.
- HTTP 401: the demo actor header is missing.
- HTTP 403: the demo role is not allowed for the route.

## Accessibility, privacy and security

The six FAQs are English-only; paraphrases and accessibility needs may be underserved. Never paste personal/customer data. The prototype does not have production authentication, sensitive-data handling, hosted storage, or monitoring. All local customer records are synthetic.
