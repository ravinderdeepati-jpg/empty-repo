"""
Private, local, dependency-free persistent memory.

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original used mem0 + Chroma, which spins up a vector DB and — critically —
makes an EXTRA LLM call on every `.add()` to extract "facts". On a CPU-bound
4 GB laptop that roughly doubles the latency of every turn.

For a single-user fashion assistant we don't need that. This stores memories as
plain JSON on disk and retrieves them with the same lightweight TF-IDF used for
offline document search. Zero services, fully private, instant.

If you later want semantic recall, you can swap `recall_memory` to call an
embedding model — the interface stays the same.
"""

import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List

import config

_MEMORY_FILE = config.MEMORY_DIR / "memories.json"
_WORD = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _WORD.findall(text.lower())


def _load() -> List[Dict]:
    if not _MEMORY_FILE.is_file():
        return []
    try:
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: List[Dict]) -> None:
    _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MEMORY_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def save_memory(text: str) -> str:
    """Append a memory. Deduplicates exact repeats."""
    text = (text or "").strip()
    if not text:
        return "Nothing to remember."
    entries = _load()
    if any(e.get("text") == text for e in entries):
        return f"Already remembered: {text}"
    entries.append({"text": text, "ts": time.time()})
    _save(entries)
    return f"Remembered: {text}"


def recall_memory(query: str, limit: int = 5) -> str:
    """Return the most relevant stored memories for a query (TF-IDF ranked)."""
    entries = _load()
    if not entries:
        return "No memories stored yet."

    texts = [e["text"] for e in entries]
    q_terms = _tokenize(query)
    if not q_terms:
        # No usable query terms: return the most recent memories.
        recent = sorted(entries, key=lambda e: e.get("ts", 0), reverse=True)[:limit]
        return "\n".join(f"- {e['text']}" for e in recent)

    tokenized = [_tokenize(t) for t in texts]
    df = Counter()
    for toks in tokenized:
        for term in set(toks):
            df[term] += 1
    n = len(texts)

    def score(toks: List[str]) -> float:
        if not toks:
            return 0.0
        tf = Counter(toks)
        s = 0.0
        for term in q_terms:
            if term in tf:
                idf = math.log((n + 1) / (df[term] + 1)) + 1.0
                s += (tf[term] / len(toks)) * idf
        return s

    ranked = sorted(range(n), key=lambda i: score(tokenized[i]), reverse=True)
    hits = [i for i in ranked if score(tokenized[i]) > 0][:limit]
    if not hits:
        return "No relevant memories found."
    return "\n".join(f"- {texts[i]}" for i in hits)


def all_memories() -> str:
    """Dump every stored memory (most recent first)."""
    entries = sorted(_load(), key=lambda e: e.get("ts", 0), reverse=True)
    if not entries:
        return "No memories stored yet."
    return "\n".join(f"- {e['text']}" for e in entries)
