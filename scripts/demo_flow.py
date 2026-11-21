"""Replay three complete Alpha HTTP scenarios with a simulated external model outage."""
import json
import os
import sys
import tempfile
import types
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import create_app

CUST = {'X-Demo-Actor': 'demo-customer', 'X-Demo-Role': 'customer'}
AGENT = {'X-Demo-Actor': 'demo-agent', 'X-Demo-Role': 'agent'}


def create(api):
    r = api.post('/v1/conversations', headers=CUST)
    assert r.status_code == 201
    return r.json()['conversation_id']


def send(api, conversation, question):
    response = api.post(f'/v1/conversations/{conversation}/messages', headers={
        **CUST, 'Idempotency-Key': str(uuid.uuid4())
    }, json={'client_message_id': str(uuid.uuid4()), 'text': question})
    assert response.status_code == 202
    return response.json()


def main():
    os.environ['AI_PROVIDER'] = 'local'
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ['DEMO_RATE_LIMIT'] = '0'
    record = {}
    with tempfile.TemporaryDirectory() as tmp:
        with TestClient(create_app(Path(tmp) / 'demo.sqlite')) as api:
            happy = create(api)
            supported = send(api, happy, 'How can I reset my password?')
            assert supported['status'] == 'answered' and supported['source_ids'] == ['FAQ-001']
            feedback = api.post(f'/v1/conversations/{happy}/feedback', headers=CUST,
                                json={'message_id': supported['assistant_message_id'], 'rating': 'helpful'})
            assert feedback.status_code == 201
            record['supported'] = {'http': 202, 'status': supported['status'],
                                   'sources': supported['source_ids'], 'feedback_http': feedback.status_code}

            unknown = create(api)
            unsupported = send(api, unknown, 'Explain astrophysics quantum mechanics')
            assert unsupported['status'] == 'escalated'
            ticket = unsupported['ticket_id']
            queued = api.get('/v1/agent/tickets', headers=AGENT)
            assert queued.status_code == 200 and any(t['id'] == ticket for t in queued.json()['items'])
            claim = api.post(f'/v1/agent/tickets/{ticket}/claim', headers=AGENT, json={'version': 0})
            reply = api.post(f'/v1/agent/tickets/{ticket}/replies', headers=AGENT,
                             json={'text': 'Our support agent will help you.'})
            history = api.get(f'/v1/conversations/{unknown}/messages', headers=CUST)
            assert claim.status_code == 200 and reply.status_code == 201
            assert [x['role'] for x in history.json()['items']] == ['customer', 'agent']
            record['unsupported'] = {'http': 202, 'status': unsupported['status'],
                                     'escalation': 'low_confidence', 'agent_claim_http': 200,
                                     'agent_reply_http': 201, 'customer_history_roles': ['customer', 'agent']}

            class BrokenClient:
                def __init__(self, **kwargs):
                    pass
                class responses:
                    @staticmethod
                    def create(**kwargs):
                        raise RuntimeError('simulated provider outage')
            sys.modules['openai'] = types.SimpleNamespace(OpenAI=BrokenClient)
            os.environ['AI_PROVIDER'] = 'openai'
            os.environ['OPENAI_API_KEY'] = 'test-only-not-real'
            failure = create(api)
            unavailable = send(api, failure, 'How do I reset my password?')
            assert unavailable['status'] == 'escalated' and unavailable['ticket_id']
            record['provider_failure'] = {'http': 202, 'status': unavailable['status'],
                                          'escalation': 'provider_unavailable', 'ticket_created': True,
                                          'provider': 'stubbed; no real external request'}
    print('GROUP G-2 ALPHA: ALL THREE END-TO-END SCENARIOS PASSED')
    print(json.dumps(record, indent=2))
    return record


if __name__ == '__main__':
    main()
