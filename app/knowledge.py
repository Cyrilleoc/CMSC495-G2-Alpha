"""Synthetic, approved FAQ examples for the local demonstration (not a real CRM)."""
import re
from collections import Counter
from math import sqrt

FAQ = [
    {"id": "FAQ-001", "question": "How do I reset my password?", "answer": "Select 'Forgot password' on the sign-in page and follow the reset email instructions."},
    {"id": "FAQ-002", "question": "Where can I find my invoice or receipt?", "answer": "Open Billing > Invoices in your account to view or download available invoices."},
    {"id": "FAQ-003", "question": "How can I track my shipment or delivery?", "answer": "Open Orders > Tracking in your account to see the latest tracking information."},
    {"id": "FAQ-004", "question": "What is the refund policy?", "answer": "Refund eligibility depends on the order. Review the posted refund policy and contact an agent for a decision about your order."},
    {"id": "FAQ-005", "question": "How do I contact a support agent?", "answer": "Ask for a human agent in this chat, and a support ticket will be created."},
    {"id": "FAQ-006", "question": "What are the support team hours?", "answer": "Current operating hours are not supplied in this demonstration. Ask an agent for confirmed support hours."},
]
STOPWORDS = set('a an are can could do does for from get how i in is it me my of on or our the to we what when where who will with you your'.split())


def tokens(text: str) -> Counter:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(w for w in words if w not in STOPWORDS)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    numerator = sum(v * b.get(k, 0) for k, v in a.items())
    norm_a = sqrt(sum(x * x for x in a.values()))
    norm_b = sqrt(sum(x * x for x in b.values()))
    return numerator / (norm_a * norm_b)


def retrieve(question: str, threshold: float = 0.38) -> dict | None:
    """Small lexical-retrieval prototype; not a trained language model."""
    q = tokens(question)
    ranked = sorted((( _cosine(q, tokens(item['question'])), item) for item in FAQ),
                    key=lambda pair: pair[0], reverse=True)
    confidence, record = ranked[0]
    return {**record, "confidence": round(confidence, 4)} if confidence >= threshold else None
