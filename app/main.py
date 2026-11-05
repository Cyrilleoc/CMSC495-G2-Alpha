"""Group G-2 customer-service Alpha: local development only; demo headers are NOT authentication."""
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.ai import answer
from app.db import connect, initialize


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def uid() -> str:
    return str(uuid.uuid4())


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class NewMessage(StrictModel):
    client_message_id: uuid.UUID
    text: str = Field(min_length=1, max_length=2000)
    locale: str = Field(default='en-US', min_length=2, max_length=35)

    @field_validator('text')
    @classmethod
    def non_blank(cls, value):
        if not value.strip():
            raise ValueError('text must not be blank')
        return value.strip()


class Escalation(StrictModel):
    reason: Literal['user_request', 'low_confidence', 'policy_blocked', 'provider_unavailable'] = 'user_request'
    summary: str | None = Field(default=None, max_length=500)


class Claim(StrictModel):
    version: int = Field(ge=0)


class AgentReply(StrictModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator('text')
    @classmethod
    def non_blank(cls, value):
        if not value.strip():
            raise ValueError('text must not be blank')
        return value.strip()


class Feedback(StrictModel):
    message_id: uuid.UUID
    rating: Literal['helpful', 'not_helpful']
    comment: str | None = Field(default=None, max_length=500)


def error(status: int, code: str, detail: str):
    raise HTTPException(status_code=status, detail={'code': code, 'message': detail})


def identity(request: Request):
    # Deliberately an insecure teaching stub, not a production identity provider.
    actor = request.headers.get('X-Demo-Actor', '').strip()
    role = request.headers.get('X-Demo-Role', 'customer').strip()
    if not actor or len(actor) > 64 or role not in {'customer', 'agent'}:
        error(401, 'AUTH_REQUIRED', 'Provide a demo actor and a valid demo role')
    return actor, role


def as_agent(actor_role=Depends(identity)):
    actor, role = actor_role
    if role != 'agent':
        error(403, 'FORBIDDEN', 'Agent role is required')
    return actor


def connection_for(request: Request):
    db = connect(request.app.state.db_path)
    try:
        yield db
    finally:
        db.close()


def require_conversation(db, conv_id: str, actor: str):
    row = db.execute('SELECT * FROM conversations WHERE id=?', (conv_id,)).fetchone()
    if not row or row['owner'] != actor:
        error(404, 'NOT_FOUND', 'Conversation not found')
    return row


def get_ticket(db, ticket_id):
    row = db.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,)).fetchone()
    if not row:
        error(404, 'NOT_FOUND', 'Ticket not found')
    return row


def create_app(db_path=None):
    app = FastAPI(title='CMSC495 G-2 Support Alpha', version='0.1.0',
                  description='Demo-only identity and SQLite; not production ready.')
    app.state.db_path = str(db_path or os.getenv('ALPHA_DB_PATH', 'data/alpha.db'))
    initialize(app.state.db_path)
    app.state.rate_lock = threading.Lock()
    app.state.rate_events = {}

    @app.middleware('http')
    async def rate_limit(request: Request, call_next):
        quota = int(os.getenv('DEMO_RATE_LIMIT', '0'))  # disabled unless explicitly enabled
        if quota > 0 and request.url.path.startswith('/v1/'):
            key = request.headers.get('X-Demo-Actor', 'anonymous')
            with app.state.rate_lock:
                t = time.monotonic()
                events = [x for x in app.state.rate_events.get(key, []) if t - x < 60.0]
                if len(events) >= quota:
                    return JSONResponse(status_code=429, media_type='application/problem+json',
                                        headers={'Retry-After': '60'},
                                        content={'type': 'about:blank', 'title': 'Too Many Requests',
                                                 'status': 429, 'code': 'RATE_LIMITED',
                                                 'detail': 'Demo request quota exceeded'})
                events.append(t)
                app.state.rate_events[key] = events
        return await call_next(request)

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {'code': 'ERROR', 'message': str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, media_type='application/problem+json',
                            content={'type': 'about:blank', 'title': detail.get('code', 'Error'),
                                     'status': exc.status_code, 'detail': detail.get('message', ''),
                                     'code': detail.get('code', 'ERROR')})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        issues = [{'field': '.'.join(map(str, e['loc'])), 'message': e['msg']} for e in exc.errors()]
        return JSONResponse(status_code=422, media_type='application/problem+json',
                            content={'type': 'about:blank', 'title': 'Invalid Input',
                                     'status': 422, 'code': 'INVALID_INPUT', 'detail': 'Invalid request',
                                     'errors': issues})

    @app.get('/healthz')
    def health():
        return {'status': 'ok', 'version': '0.1.0'}

    @app.get('/', include_in_schema=False)
    def ui():
        return FileResponse(Path(__file__).parent / 'static' / 'index.html')

    @app.post('/v1/conversations', status_code=201)
    def create_conversation(actor_role=Depends(identity), db=Depends(connection_for)):
        actor, role = actor_role
        if role != 'customer':
            error(403, 'FORBIDDEN', 'Customer role required')
        conv_id = uid()
        with db:
            db.execute('INSERT INTO conversations VALUES(?,?,?)', (conv_id, actor, now()))
        return {'conversation_id': conv_id, 'owner': actor}

    @app.post('/v1/conversations/{conv_id}/messages', status_code=202)
    def post_message(conv_id: uuid.UUID, body: NewMessage, request: Request,
                     idempotency_key: uuid.UUID = Header(alias='Idempotency-Key'),
                     actor_role=Depends(identity), db=Depends(connection_for)):
        actor, role = actor_role
        if role != 'customer':
            error(403, 'FORBIDDEN', 'Customer role required')
        conv = str(conv_id)
        require_conversation(db, conv, actor)
        existing = db.execute('SELECT id FROM messages WHERE conversation_id=? AND client_message_id=?',
                              (conv, str(body.client_message_id))).fetchone()
        if existing:
            ticket = db.execute('SELECT id FROM tickets WHERE source_message_id=?', (existing['id'],)).fetchone()
            return {'message_id': existing['id'], 'status': 'duplicate',
                    'ticket_id': ticket['id'] if ticket else None}
        decision = answer(body.text)
        message_id = uid()
        bot_id = None
        ticket_id = None
        with db:
            db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?)',
                       (message_id, conv, str(body.client_message_id), 'customer', body.text, '[]', now()))
            if decision['decision'] == 'answer':
                bot_id = uid()
                db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?)',
                           (bot_id, conv, None, 'assistant', decision['reply'],
                            json.dumps(decision['source_ids']), now()))
            else:
                ticket_id = uid()
                db.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?,?,?)',
                           (ticket_id, conv, message_id, decision['reason'], 'queued', None, 0, now()))
        return {'message_id': message_id, 'status': 'answered' if bot_id else 'escalated',
                'assistant_message_id': bot_id, 'reply': decision['reply'],
                'source_ids': decision['source_ids'], 'confidence': decision['confidence'],
                'ticket_id': ticket_id}

    @app.get('/v1/conversations/{conv_id}/messages')
    def list_messages(conv_id: uuid.UUID, actor_role=Depends(identity), db=Depends(connection_for)):
        actor, role = actor_role
        if role != 'customer':
            error(403, 'FORBIDDEN', 'Customer role required')
        require_conversation(db, str(conv_id), actor)
        rows = db.execute('SELECT id, role, text, source_ids, created_at FROM messages '
                          'WHERE conversation_id=? ORDER BY created_at, rowid', (str(conv_id),)).fetchall()
        return {'items': [{**dict(r), 'source_ids': json.loads(r['source_ids'])} for r in rows]}

    @app.post('/v1/conversations/{conv_id}/escalations', status_code=201)
    def manual_escalation(conv_id: uuid.UUID, body: Escalation, actor_role=Depends(identity),
                          db=Depends(connection_for)):
        actor, role = actor_role
        if role != 'customer':
            error(403, 'FORBIDDEN', 'Customer role required')
        conv = str(conv_id)
        require_conversation(db, conv, actor)
        ticket_id = uid()
        with db:
            db.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?,?,?)',
                       (ticket_id, conv, None, body.reason, 'queued', None, 0, now()))
        return {'ticket_id': ticket_id, 'status': 'queued'}

    @app.get('/v1/agent/tickets')
    def list_tickets(agent=Depends(as_agent), db=Depends(connection_for)):
        rows = db.execute('SELECT id, conversation_id, reason, status, agent, version FROM tickets '
                          'ORDER BY created_at, rowid').fetchall()
        return {'items': [dict(row) for row in rows]}

    @app.post('/v1/agent/tickets/{ticket_id}/claim')
    def claim(ticket_id: uuid.UUID, body: Claim, agent=Depends(as_agent), db=Depends(connection_for)):
        ticket_id = str(ticket_id)
        with db:
            updated = db.execute("UPDATE tickets SET status='assigned', agent=?, version=version+1 "
                                 "WHERE id=? AND status='queued' AND version=?",
                                 (agent, ticket_id, body.version))
            if updated.rowcount == 0:
                get_ticket(db, ticket_id)
                error(409, 'CONFLICT', 'Ticket was already claimed or version is stale')
        return {'ticket_id': ticket_id, 'status': 'assigned', 'agent': agent, 'version': body.version + 1}

    @app.post('/v1/agent/tickets/{ticket_id}/replies', status_code=201)
    def agent_reply(ticket_id: uuid.UUID, body: AgentReply, agent=Depends(as_agent),
                    db=Depends(connection_for)):
        ticket = get_ticket(db, str(ticket_id))
        if ticket['status'] != 'assigned' or ticket['agent'] != agent:
            error(403, 'FORBIDDEN', 'Ticket must be assigned to this agent')
        msg_id = uid()
        with db:
            db.execute('INSERT INTO messages VALUES(?,?,?,?,?,?,?)',
                       (msg_id, ticket['conversation_id'], None, 'agent', body.text.strip(), '[]', now()))
        return {'message_id': msg_id, 'ticket_id': str(ticket_id)}

    @app.post('/v1/conversations/{conv_id}/feedback', status_code=201)
    def submit_feedback(conv_id: uuid.UUID, body: Feedback, actor_role=Depends(identity),
                        db=Depends(connection_for)):
        actor, role = actor_role
        if role != 'customer':
            error(403, 'FORBIDDEN', 'Customer role required')
        require_conversation(db, str(conv_id), actor)
        msg = db.execute('SELECT id FROM messages WHERE id=? AND conversation_id=? AND role=?',
                         (str(body.message_id), str(conv_id), 'assistant')).fetchone()
        if not msg:
            error(404, 'NOT_FOUND', 'Assistant message not found in conversation')
        feedback_id = uid()
        with db:
            db.execute('INSERT INTO feedback VALUES(?,?,?,?,?,?,?)',
                       (feedback_id, str(conv_id), str(body.message_id), body.rating,
                        body.comment, 'queued', now()))
        return {'feedback_id': feedback_id, 'review_status': 'queued'}

    return app


app = create_app()
