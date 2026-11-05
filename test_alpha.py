"""G-2 Alpha tests: core workflow, safe fallback, validation, isolation, agent operations."""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.knowledge import retrieve
from app.ai import redact

CUSTOMER = {'X-Demo-Actor': 'customer-one', 'X-Demo-Role': 'customer'}
OTHER = {'X-Demo-Actor': 'customer-two', 'X-Demo-Role': 'customer'}
AGENT = {'X-Demo-Actor': 'agent-one', 'X-Demo-Role': 'agent'}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_RATE_LIMIT', '0')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('AI_PROVIDER', 'local')
    with TestClient(create_app(tmp_path / 'alpha-test.sqlite')) as c:
        yield c


def new_chat(c, headers=CUSTOMER):
    r = c.post('/v1/conversations', headers=headers)
    assert r.status_code == 201, r.text
    return r.json()['conversation_id']


def chat(c, conv, text, headers=CUSTOMER, client_id=None):
    return c.post(f'/v1/conversations/{conv}/messages',
                  headers={**headers, 'Idempotency-Key': str(uuid.uuid4())},
                  json={'client_message_id': client_id or str(uuid.uuid4()), 'text': text})


def test_health(client):
    assert client.get('/healthz').json()['status'] == 'ok'


def test_html_demo_served(client):
    r = client.get('/')
    assert r.status_code == 200 and 'Customer Service Alpha' in r.text


def test_requires_actor(client):
    assert client.post('/v1/conversations').status_code == 401


def test_create_conversation(client):
    assert uuid.UUID(new_chat(client))


def test_faq_answer_and_history(client):
    conv = new_chat(client)
    r = chat(client, conv, 'How can I reset my password?')
    assert r.status_code == 202, r.text
    result = r.json()
    assert result['status'] == 'answered'
    assert result['source_ids'] == ['FAQ-001']
    hist = client.get(f'/v1/conversations/{conv}/messages', headers=CUSTOMER)
    assert [m['role'] for m in hist.json()['items']] == ['customer', 'assistant']


def test_unknown_question_creates_ticket(client):
    conv = new_chat(client)
    result = chat(client, conv, 'Tell me about astrophysics').json()
    assert result['status'] == 'escalated'
    tickets = client.get('/v1/agent/tickets', headers=AGENT).json()['items']
    assert len(tickets) == 1 and tickets[0]['reason'] == 'low_confidence'


def test_human_request_escalates(client):
    conv = new_chat(client)
    result = chat(client, conv, 'I need a human agent').json()
    assert result['status'] == 'escalated'
    assert result['ticket_id'] is not None


def test_manual_escalation(client):
    conv = new_chat(client)
    r = client.post(f'/v1/conversations/{conv}/escalations', headers=CUSTOMER,
                    json={'reason': 'user_request'})
    assert r.status_code == 201 and r.json()['status'] == 'queued'


def test_agent_claim_and_reply(client):
    conv = new_chat(client)
    ticket_id = chat(client, conv, 'I need a human agent').json()['ticket_id']
    denied = client.post(f'/v1/agent/tickets/{ticket_id}/claim', headers=CUSTOMER, json={'version': 0})
    assert denied.status_code == 403
    claim = client.post(f'/v1/agent/tickets/{ticket_id}/claim', headers=AGENT, json={'version': 0})
    assert claim.status_code == 200 and claim.json()['version'] == 1
    stale = client.post(f'/v1/agent/tickets/{ticket_id}/claim', headers=AGENT, json={'version': 0})
    assert stale.status_code == 409
    response = client.post(f'/v1/agent/tickets/{ticket_id}/replies', headers=AGENT, json={'text': 'I can help.'})
    assert response.status_code == 201
    history = client.get(f'/v1/conversations/{conv}/messages', headers=CUSTOMER).json()['items']
    assert history[-1]['role'] == 'agent'


def test_user_cannot_read_other_conversation(client):
    conv = new_chat(client)
    r = client.get(f'/v1/conversations/{conv}/messages', headers=OTHER)
    assert r.status_code == 404


def test_blank_message_rejected(client):
    conv = new_chat(client)
    assert chat(client, conv, '   ').status_code == 422


def test_oversized_message_rejected(client):
    conv = new_chat(client)
    assert chat(client, conv, 'a' * 2001).status_code == 422


def test_invalid_uuid_rejected(client):
    r = client.get('/v1/conversations/not-a-uuid/messages', headers=CUSTOMER)
    assert r.status_code == 422


def test_problem_json_errors(client):
    r = client.post('/v1/conversations')
    assert r.headers['content-type'].startswith('application/problem+json')
    assert r.json()['code'] == 'AUTH_REQUIRED'


def test_message_idempotent(client):
    conv = new_chat(client)
    client_id = str(uuid.uuid4())
    first = chat(client, conv, 'How do I reset my password?', client_id=client_id)
    second = chat(client, conv, 'How do I reset my password?', client_id=client_id)
    assert first.status_code == 202
    assert second.json()['status'] == 'duplicate'
    history = client.get(f'/v1/conversations/{conv}/messages', headers=CUSTOMER).json()['items']
    assert len(history) == 2


def test_feedback_recorded_for_assistant_reply(client):
    conv = new_chat(client)
    answer_id = chat(client, conv, 'How do I reset my password?').json()['assistant_message_id']
    r = client.post(f'/v1/conversations/{conv}/feedback', headers=CUSTOMER,
                    json={'message_id': answer_id, 'rating': 'helpful'})
    assert r.status_code == 201
    assert r.json()['review_status'] == 'queued'


def test_feedback_rejects_invalid_message(client):
    conv = new_chat(client)
    r = client.post(f'/v1/conversations/{conv}/feedback', headers=CUSTOMER,
                    json={'message_id': str(uuid.uuid4()), 'rating': 'helpful'})
    assert r.status_code == 404


def test_retriever_unrecognized():
    assert retrieve('astrophysics quantum mechanics') is None


def test_redaction():
    assert '[email redacted]' in redact('Email me at alice@example.org')


def test_rate_limit(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_RATE_LIMIT', '1')
    with TestClient(create_app(tmp_path / 'rate.sqlite')) as c:
        assert c.post('/v1/conversations', headers=CUSTOMER).status_code == 201
        r = c.post('/v1/conversations', headers=CUSTOMER)
        assert r.status_code == 429
        assert r.headers['retry-after'] == '60'


def test_ai_provider_failure_uses_safe_escalation(monkeypatch, client):
    # No external network call: deliberately stub the provider so we can test failure handling.
    from app import ai
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder-not-real')
    monkeypatch.setenv('AI_PROVIDER', 'openai')
    import sys
    import types
    class BrokenClient:
        def __init__(self, **kwargs):
            pass
        class responses:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError('simulated provider outage')
    monkeypatch.setitem(sys.modules, 'openai', types.SimpleNamespace(OpenAI=BrokenClient))
    decision = ai.answer('How do I reset my password?')
    assert decision['decision'] == 'escalate'
    assert decision['reason'] == 'provider_unavailable'


def test_ai_provider_input_redacts_email(monkeypatch):
    from app import ai
    import sys
    import types
    captured = {}
    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output_text='Use the forgot password link.')
    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder-not-real')
    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setitem(sys.modules, 'openai', types.SimpleNamespace(OpenAI=FakeClient))
    decision = ai.answer('How do I reset my password? alice@example.org')
    assert decision['decision'] == 'answer'
    assert 'alice@example.org' not in captured['input']
    assert '[email redacted]' in captured['input']
