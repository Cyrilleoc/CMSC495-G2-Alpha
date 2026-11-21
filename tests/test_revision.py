"""Unit 5 instructor-feedback tests: end-to-end workflow, privacy, caching, AI reliability."""
import logging
import sys
import types
import uuid

import pytest
from fastapi.testclient import TestClient

from app.ai import redact
from app.main import create_app
from app.knowledge import FAQ, _cosine, retrieve, tokens

CUSTOMER = {'X-Demo-Actor': 'customer-one', 'X-Demo-Role': 'customer'}
AGENT = {'X-Demo-Actor': 'agent-one', 'X-Demo-Role': 'agent'}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'local')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('DEMO_RATE_LIMIT', '0')
    with TestClient(create_app(tmp_path / 'revision-test.sqlite')) as api:
        yield api


def send(api, conv_id, question):
    return api.post(f'/v1/conversations/{conv_id}/messages', headers={
        **CUSTOMER, 'Idempotency-Key': str(uuid.uuid4())
    }, json={'client_message_id': str(uuid.uuid4()), 'text': question})


def fake_provider(monkeypatch, *, result='Approved paraphrase', fail=False):
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            if fail:
                raise RuntimeError('simulated temporary outage; do not expose prompt')
            return types.SimpleNamespace(output_text=result)

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = FakeResponses()

    monkeypatch.setenv('AI_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-not-real')
    monkeypatch.setitem(sys.modules, 'openai', types.SimpleNamespace(OpenAI=FakeClient))
    return captured


@pytest.mark.parametrize('scenario,question,expected_reason', [
    ('supported', 'How do I reset my password?', None),
    ('unsupported', 'What is astrophysics?', 'low_confidence'),
    ('provider_failure', 'How do I reset my password?', 'provider_unavailable'),
])
def test_full_api_customer_to_ai_to_agent_flow(client, monkeypatch, scenario, question, expected_reason):
    """Integration enters through HTTP API, not direct answer()/retrieve() calls."""
    if scenario == 'provider_failure':
        fake_provider(monkeypatch, fail=True)
    create = client.post('/v1/conversations', headers=CUSTOMER)
    assert create.status_code == 201
    conv = create.json()['conversation_id']
    msg = send(client, conv, question)
    assert msg.status_code == 202
    payload = msg.json()
    assert payload['message_id']
    assert payload['status'] == ('answered' if scenario == 'supported' else 'escalated')
    assert msg.headers['cache-control'] == 'no-store'
    if scenario == 'supported':
        assert payload['source_ids'] == ['FAQ-001']
        assert payload['assistant_message_id']
        assert 'reset' in payload['reply'].lower()
        feedback = client.post(f'/v1/conversations/{conv}/feedback', headers=CUSTOMER,
                               json={'message_id': payload['assistant_message_id'], 'rating': 'helpful'})
        assert feedback.status_code == 201
        assert feedback.json()['review_status'] == 'queued'
        roles = [entry['role'] for entry in client.get(
            f'/v1/conversations/{conv}/messages', headers=CUSTOMER).json()['items']]
        assert roles == ['customer', 'assistant']
    else:
        assert payload['reply'] is None
        assert payload['ticket_id']
        tickets = client.get('/v1/agent/tickets', headers=AGENT)
        assert tickets.status_code == 200
        assert any(t['id'] == payload['ticket_id'] and t['reason'] == expected_reason
                   for t in tickets.json()['items'])
        claim = client.post(f"/v1/agent/tickets/{payload['ticket_id']}/claim",
                            headers=AGENT, json={'version': 0})
        assert claim.status_code == 200
        response = client.post(f"/v1/agent/tickets/{payload['ticket_id']}/replies",
                               headers=AGENT, json={'text': 'Our team will help you.'})
        assert response.status_code == 201
        history = client.get(f'/v1/conversations/{conv}/messages', headers=CUSTOMER)
        assert history.status_code == 200
        assert [msg['role'] for msg in history.json()['items']] == ['customer', 'agent']


@pytest.mark.parametrize('path,headers,status', [
    ('/v1/conversations', {}, 401),
    ('/v1/agent/tickets', CUSTOMER, 403),
])
def test_security_error_responses_not_cacheable(client, path, headers, status):
    response = client.post(path, headers=headers) if path.endswith('/conversations') else client.get(path, headers=headers)
    assert response.status_code == status
    assert response.headers['cache-control'] == 'no-store'


def test_only_api_routes_get_no_store(client):
    assert client.get('/healthz').status_code == 200
    assert 'no-store' not in client.get('/healthz').headers.get('cache-control', '')
    assert client.get('/').status_code == 200
    assert 'no-store' not in client.get('/').headers.get('cache-control', '')


def test_429_no_store_on_every_rate_limited_response(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_RATE_LIMIT', '1')
    with TestClient(create_app(tmp_path / 'ratelimited.sqlite')) as api:
        first = api.post('/v1/conversations', headers=CUSTOMER)
        assert first.status_code == 201 and first.headers['cache-control'] == 'no-store'
        for _ in range(2):
            denied = api.post('/v1/conversations', headers=CUSTOMER)
            assert denied.status_code == 429
            assert denied.headers['cache-control'] == 'no-store'
            assert denied.headers['retry-after'] == '60'


@pytest.mark.parametrize('raw,private_values,expected_marker,expected_count', [
    ('Contact alice@example.org today', ('alice@example.org',), '[email redacted]', 1),
    ('Emails: first@example.com and second@test.co please',
     ('first@example.com', 'second@test.co'), '[email redacted]', 2),
    ('Call (615) 555-0123', ('(615) 555-0123',), '[phone redacted]', 1),
    ('Call +1 (615) 555-0123', ('+1 (615) 555-0123',), '[phone redacted]', 1),
    ('Call 615-555-0123', ('615-555-0123',), '[phone redacted]', 1),
    ('Call 615.555.0123', ('615.555.0123',), '[phone redacted]', 1),
    ('Call 615 555 0123', ('615 555 0123',), '[phone redacted]', 1),
    ('Call 1-615-555-0123', ('1-615-555-0123',), '[phone redacted]', 1),
])
def test_parameterized_redaction(raw, private_values, expected_marker, expected_count):
    masked = redact(raw)
    for private_value in private_values:
        assert private_value not in masked
    assert masked.count(expected_marker) == expected_count
    other_marker = '[phone redacted]' if expected_marker == '[email redacted]' else '[email redacted]'
    assert other_marker not in masked


def test_redact_multiple_emails_and_phone_numbers():
    original = ('Hello, contact alice@example.org, help@my-company.com and team@example.net. '
                'Numbers: (615) 555-0123, +1 615-555-0140, 615.555.0188. '
                'I need help resetting my password. Thank you.')
    masked = redact(original)
    assert masked.count('[email redacted]') == 3
    assert masked.count('[phone redacted]') == 3
    assert 'password' in masked


def test_sensitive_data_never_reaches_fake_model_or_application_logs(client, monkeypatch, caplog, capsys):
    captured = fake_provider(monkeypatch)
    private = ['alice@example.org', 'other@example.com', '+1 (615) 555-0101']
    question = ('How do I reset my password? Can I reset my password again? '
                'Please help with reset password: ' + ' '.join(private))
    with caplog.at_level(logging.DEBUG):
        conv = client.post('/v1/conversations', headers=CUSTOMER).json()['conversation_id']
        r = send(client, conv, question)
    assert r.status_code == 202 and r.json()['status'] == 'answered'
    assert captured['input']
    for secret in private:
        assert secret not in captured['input']
    assert '[email redacted]' in captured['input']
    assert '[phone redacted]' in captured['input']
    record_text = '\n'.join(record.getMessage() for record in caplog.records)
    stdout, stderr = capsys.readouterr()
    for secret in private:
        assert secret not in record_text + stdout + stderr


@pytest.mark.parametrize('kind', ['exception', 'empty', 'blank'])
def test_provider_failures_through_api_are_escalated(client, monkeypatch, kind):
    fake_provider(monkeypatch, fail=(kind == 'exception'), result= '' if kind == 'empty' else '  ')
    conv = client.post('/v1/conversations', headers=CUSTOMER).json()['conversation_id']
    response = send(client, conv, 'How can I reset my password?')
    assert response.status_code == 202
    result = response.json()
    assert result['status'] == 'escalated'
    assert result['ticket_id']
    assert result['reply'] is None


@pytest.mark.parametrize('question,expected_id', [
    ('How can I reset my password?', 'FAQ-001'),
    ('reset password', 'FAQ-001'),
    ('invoice or receipt', 'FAQ-002'),
    ('track delivery', 'FAQ-003'),
    ('refund policy', 'FAQ-004'),
    ('quantum astrophysics', None),
    ('banana photography microscope', None),
])
def test_faq_accuracy_against_curated_dataset(question, expected_id):
    output = retrieve(question)
    assert (output['id'] if output else None) == expected_id


def test_precomputed_retrieval_matches_original_algorithm():
    def old_retrieve(question, threshold=0.38):
        query = tokens(question)
        ranked = sorted(((_cosine(query, tokens(item['question'])), item) for item in FAQ),
                        key=lambda pair: pair[0], reverse=True)
        score, item = ranked[0]
        return {**item, 'confidence': round(score, 4)} if score >= threshold else None

    for question in ('How can I reset my password?', 'reset password', 'invoice or receipt',
                     'track delivery', 'refund policy', 'quantum astrophysics'):
        assert retrieve(question) == old_retrieve(question)
