"""
LLM helpers: talk to Ollama, strip reasoning tags, and extract JSON robustly.

This module exists because the naive approach in the original scaffold
(`raw.replace("```json", "").replace("```", "")` then `json.loads`) breaks the
moment the model:

  * emits a <think>...</think> reasoning block (Qwen3 / DeepSeek-R1 style),
  * wraps JSON in prose ("Sure! Here is the JSON: {...}"),
  * adds a trailing comment after the closing brace, or
  * returns more than one fenced block.

We defend against all of those with tag stripping + a brace-matching scanner.
"""

import json
import re
from typing import Any, Dict, Optional

import config

try:
    from ollama import Client
except Exception:  # pragma: no cover - import guard for environments w/o ollama
    Client = None


# --------------------------------------------------------------------------- #
# Reasoning-tag handling
# --------------------------------------------------------------------------- #
# Match <think>...</think>, <thinking>...</thinking>, and a dangling opener with
# no closer (some builds forget to close the tag). DOTALL so it spans newlines.
_THINK_BLOCK = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL | re.IGNORECASE)
_THINK_DANGLING = re.compile(r"<think(?:ing)?>.*", re.DOTALL | re.IGNORECASE)
_THINK_STRAY_CLOSE = re.compile(r"</think(?:ing)?>", re.IGNORECASE)


def strip_think(text: str) -> str:
    """Remove chain-of-thought reasoning blocks from a model response."""
    if not text:
        return ""
    text = _THINK_BLOCK.sub("", text)
    # A lone "</think>" with no opener: drop everything up to and including it,
    # since reasoning models put the real answer *after* the closing tag.
    if _THINK_STRAY_CLOSE.search(text) and "<think" not in text.lower():
        text = _THINK_STRAY_CLOSE.split(text)[-1]
    # An opener with no closer: whatever follows is unfinished reasoning; drop it.
    text = _THINK_DANGLING.sub("", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# JSON extraction
# --------------------------------------------------------------------------- #
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _scan_balanced_json(text: str) -> Optional[str]:
    """
    Return the first balanced {...} object in `text`, respecting strings and
    escapes so that braces inside string values don't confuse the matcher.
    """
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
        # Unbalanced from this "{"; try the next one.
        start = text.find("{", start + 1)
    return None


def extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction of a single JSON object from an LLM response.

    Strategy (in order):
      1. strip <think> reasoning,
      2. try any fenced ```json block,
      3. try the whole cleaned string,
      4. brace-scan for the first balanced object.
    Returns a dict, or None if nothing parseable is found.
    """
    if not raw:
        return None

    cleaned = strip_think(raw)

    candidates = []
    for m in _FENCE.finditer(cleaned):
        candidates.append(m.group(1).strip())
    candidates.append(cleaned.strip())
    scanned = _scan_balanced_json(cleaned)
    if scanned:
        candidates.append(scanned)

    for cand in candidates:
        if not cand:
            continue
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, ValueError):
            continue
    return None


# --------------------------------------------------------------------------- #
# Ollama chat wrapper
# --------------------------------------------------------------------------- #
_client = None


def get_client():
    """Lazily construct (and cache) the Ollama client."""
    global _client
    if _client is None:
        if Client is None:
            raise RuntimeError(
                "The 'ollama' package is not installed. Run: pip install ollama"
            )
        _client = Client(host=config.OLLAMA_HOST, timeout=config.LLM_TIMEOUT)
    return _client


def chat(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
    """
    Send a single-turn chat to Ollama and return the raw assistant text.

    We pass `think=False` via options where supported; for models that ignore it
    we still strip <think> downstream, so this is belt-and-suspenders.
    """
    client = get_client()
    model = model or config.LLM_MODEL

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    options = {"temperature": 0.4}
    kwargs = {"model": model, "messages": messages, "options": options}

    # Newer Ollama supports a top-level `think` flag to disable reasoning output.
    if config.LLM_DISABLE_THINKING:
        try:
            resp = client.chat(think=False, **kwargs)
        except TypeError:
            # Older client signature without `think`.
            resp = client.chat(**kwargs)
    else:
        resp = client.chat(**kwargs)

    # The client may return an object or a dict depending on version.
    try:
        return resp["message"]["content"]
    except (TypeError, KeyError):
        return resp.message.content


def chat_json(
    system_prompt: str, user_prompt: str, model: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Convenience: chat() then extract_json()."""
    raw = chat(system_prompt, user_prompt, model=model)
    return extract_json(raw)
