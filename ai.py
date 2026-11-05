"""Bounded chatbot orchestration: approved retrieval, optional LLM paraphrase, safe fallback."""
import os
import re
from app.knowledge import retrieve

# Deliberately sends no customer record and masks common PII in the question.
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{8,}\d)(?!\w)")


def redact(text: str) -> str:
    return _PHONE.sub('[phone redacted]', _EMAIL.sub('[email redacted]', text))


def answer(question: str) -> dict:
    if any(p in question.lower() for p in ('human agent', 'real person', 'talk to a person', 'speak to agent')):
        return {"decision": "escalate", "reason": "user_request", "reply": None, "source_ids": [], "confidence": 0.0}
    match = retrieve(question)
    if match is None:
        return {"decision": "escalate", "reason": "low_confidence", "reply": None, "source_ids": [], "confidence": 0.0}
    # The approved FAQ gives a safe, functional retrieval-based chat mode offline.
    reply = match['answer']
    if os.getenv('OPENAI_API_KEY') and os.getenv('AI_PROVIDER', 'local') == 'openai':
        try:
            from openai import OpenAI
            client = OpenAI(timeout=8.0, max_retries=0)
            result = client.responses.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-5.5'),
                instructions=("You are a customer service assistant. Restate only the APPROVED ANSWER, "
                              "without adding unsupported claims, policies, dates, or personal information. "
                              "Respond in 60 words or fewer. Do not mention this instruction."),
                input=f"Customer question: {redact(question)}\nAPPROVED ANSWER: {reply}",
            )
            if result.output_text.strip():
                reply = result.output_text.strip()[:1200]
            else:
                raise ValueError('empty provider result')
        except Exception:
            return {"decision": "escalate", "reason": "provider_unavailable", "reply": None,
                    "source_ids": [match['id']], "confidence": match['confidence']}
    return {"decision": "answer", "reason": None, "reply": reply,
            "source_ids": [match['id']], "confidence": match['confidence']}
