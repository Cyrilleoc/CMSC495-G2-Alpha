"""SQLite data adapter for a single-instance local Alpha; PostgreSQL planned for scaling."""
import sqlite3
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY, owner TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
    client_message_id TEXT, role TEXT NOT NULL, text TEXT NOT NULL, source_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    UNIQUE(conversation_id, client_message_id)
);
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
    source_message_id TEXT UNIQUE, reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
    agent TEXT, version INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
    message_id TEXT NOT NULL REFERENCES messages(id), rating TEXT NOT NULL,
    comment TEXT, review_status TEXT NOT NULL DEFAULT 'queued', created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets(status);
"""


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def initialize(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.executescript(DDL)
