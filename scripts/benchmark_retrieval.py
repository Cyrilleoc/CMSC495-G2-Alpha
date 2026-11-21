"""Compare prior runtime FAQ tokenization with cached counters; timings are illustrative."""
import json
import sys
from pathlib import Path
from statistics import median
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.knowledge import FAQ, _cosine, retrieve, tokens

SAMPLES = [
    ('How can I reset my password?', 'FAQ-001'),
    ('reset password', 'FAQ-001'),
    ('invoice or receipt', 'FAQ-002'),
    ('track delivery', 'FAQ-003'),
    ('refund policy', 'FAQ-004'),
    ('quantum astrophysics', None),
    ('banana photography microscope', None),
]


def original_retrieve(question, threshold=0.38):
    q = tokens(question)
    pairs = sorted(((_cosine(q, tokens(item['question'])), item) for item in FAQ),
                   key=lambda pair: pair[0], reverse=True)
    confidence, record = pairs[0]
    return {**record, 'confidence': round(confidence, 4)} if confidence >= threshold else None


def measure(fn, repeats=2500, passes=5):
    times = []
    for _ in range(passes):
        start = perf_counter()
        for _ in range(repeats):
            for question, _ in SAMPLES:
                fn(question)
        times.append((perf_counter() - start) / (repeats * len(SAMPLES)) * 1e6)
    return round(median(times), 3)


def main():
    assert all(original_retrieve(q) == retrieve(q) for q, _ in SAMPLES)
    accuracy = sum((retrieve(q) or {}).get('id') == expected for q, expected in SAMPLES)
    for _ in range(100):
        for q, _ in SAMPLES:
            original_retrieve(q)
            retrieve(q)
    old_us = measure(original_retrieve)
    new_us = measure(retrieve)
    record = {
        'dataset': 'seven synthetic questions; not real-world AI accuracy data',
        'questions': len(SAMPLES),
        'correct_predictions': accuracy,
        'accuracy_fraction': round(accuracy / len(SAMPLES), 4),
        'behavior_identical_before_after': True,
        'old_median_microseconds_per_query': old_us,
        'new_median_microseconds_per_query': new_us,
        'illustrative_speedup': round(old_us / new_us, 2) if new_us else None,
        'note': 'Machine-specific; external LLM not called; multilingual fairness not measured.'
    }
    print(json.dumps(record, indent=2))
    return record


if __name__ == '__main__':
    main()
