"""Whitespace-separated word-count check for the required 250-word Refinement Report."""
import pathlib
import sys
if len(sys.argv) != 2:
    raise SystemExit('Usage: python scripts/word_count.py path/to/report.txt')
words = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').split()
print(f'{len(words)} words; '+('exactly 250' if len(words)==250 else f'needs {250-len(words):+d} words'))
raise SystemExit(0 if len(words)==250 else 1)
