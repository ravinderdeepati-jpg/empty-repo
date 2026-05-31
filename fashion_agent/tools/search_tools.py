"""
Search tools: online web search (SearXNG + page fetch) and offline document RAG.

WHY THIS IS DIFFERENT FROM THE ORIGINAL SCAFFOLD
-------------------------------------------------
The original scraped `html.duckduckgo.com` by CSS class. That is brittle (breaks
when DDG changes markup), gets rate-limited, and only ever returns titles +
snippets — never the page text. So the LLM could only summarize blurbs.

This module:
  * queries a self-hosted **SearXNG** instance via its JSON API (stable, no
    scraping, anonymized upstream queries),
  * actually FETCHES the top result pages and extracts readable text, giving the
    LLM real content to ground its answers in (retrieval-augmented),
  * detects connectivity and, when offline (or FORCE_OFFLINE=1), transparently
    falls back to a keyword search over your local documents in offline_docs/.

The agent therefore satisfies BOTH "search all over the internet" (online) and
"work without internet" (offline) — the two requirements that were in tension.
"""

import math
import re
import socket
from collections import Counter
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

import config


# --------------------------------------------------------------------------- #
# Connectivity
# --------------------------------------------------------------------------- #
def is_online() -> bool:
    """Quick TCP probe. Honors FORCE_OFFLINE to hard-disable networking."""
    if config.FORCE_OFFLINE:
        return False
    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except OSError:
            continue
    return False


def _searxng_available() -> bool:
    try:
        r = requests.get(config.SEARXNG_URL, timeout=4)
        return r.status_code < 500
    except requests.RequestException:
        return False


# --------------------------------------------------------------------------- #
# Online: SearXNG + page fetch
# --------------------------------------------------------------------------- #
def _searxng_query(query: str, max_results: int) -> List[Dict[str, str]]:
    """Hit SearXNG's JSON API and return a list of {title, url, content}."""
    params = {"q": query, "format": "json"}
    r = requests.get(
        f"{config.SEARXNG_URL}/search", params=params, timeout=config.NET_TIMEOUT
    )
    r.raise_for_status()
    data = r.json()
    out = []
    for item in data.get("results", [])[:max_results]:
        out.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),  # SearXNG's own snippet
            }
        )
    return out


_TAG_DROP = ("script", "style", "nav", "header", "footer", "aside", "form", "noscript")


def _fetch_readable(url: str, max_chars: int = 2500) -> str:
    """Download a page and extract a readable text excerpt."""
    try:
        r = requests.get(
            url,
            timeout=config.NET_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FashionAgent/1.0)"},
        )
        r.raise_for_status()
    except requests.RequestException:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(_TAG_DROP):
        tag.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()
    return text[:max_chars]


def web_search(query: str, num_results: int = 3) -> str:
    """
    Search the web and return real, citable content for the LLM to summarize.

    Falls back to offline document search automatically when there is no
    connectivity or SearXNG is unreachable.
    """
    if not is_online():
        return (
            "[OFFLINE MODE] No internet connection.\n"
            + offline_search(query, num_results)
        )

    if not _searxng_available():
        return (
            f"[SEARCH UNAVAILABLE] SearXNG not reachable at {config.SEARXNG_URL}.\n"
            "Start it (see README) or set SEARXNG_URL. Falling back to local docs:\n\n"
            + offline_search(query, num_results)
        )

    try:
        results = _searxng_query(query, num_results)
    except requests.RequestException as e:
        return f"[SEARCH ERROR] {e}\n\n" + offline_search(query, num_results)

    if not results:
        return f"No web results for: {query}"

    blocks = [f"Web results for: {query}\n"]
    for i, res in enumerate(results[: config.SEARCH_FETCH_PAGES], start=1):
        body = _fetch_readable(res["url"]) or res["content"]
        blocks.append(
            f"[{i}] {res['title']}\n"
            f"    URL: {res['url']}\n"
            f"    {body}\n"
        )
    # Any remaining results beyond the fetch budget: include snippet only.
    for i, res in enumerate(results[config.SEARCH_FETCH_PAGES:], start=config.SEARCH_FETCH_PAGES + 1):
        blocks.append(f"[{i}] {res['title']}\n    URL: {res['url']}\n    {res['content']}\n")

    return "\n".join(blocks)


# --------------------------------------------------------------------------- #
# Offline: local document RAG (TF-IDF, no heavy deps)
# --------------------------------------------------------------------------- #
def _read_document(path: Path) -> str:
    """Extract text from a .txt/.md or .pdf file."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""
    return ""


def _chunk(text: str, size: int = 600, overlap: int = 100) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + size])
        if chunk:
            chunks.append(chunk)
    return chunks


_WORD = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _WORD.findall(text.lower())


def offline_search(query: str, num_results: int = 3) -> str:
    """
    Keyword/TF-IDF search over documents in offline_docs/. Returns the most
    relevant passages so the LLM can answer without any internet access.

    Implemented with a tiny self-contained TF-IDF (no external vector DB) so it
    works on a fresh install with zero extra services running.
    """
    docs_dir = config.DOCS_DIR
    files = [
        p
        for p in docs_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in (".txt", ".md", ".pdf")
    ]
    if not files:
        return (
            f"[OFFLINE] No documents found in {docs_dir}. "
            "Drop .txt, .md, or .pdf files there to enable offline answers."
        )

    # Build chunk corpus.
    chunks: List[str] = []
    sources: List[str] = []
    for f in files:
        text = _read_document(f)
        for ch in _chunk(text):
            chunks.append(ch)
            sources.append(f.name)
    if not chunks:
        return f"[OFFLINE] Documents in {docs_dir} contained no extractable text."

    # TF-IDF scoring.
    q_terms = _tokenize(query)
    if not q_terms:
        return "[OFFLINE] Empty query."

    tokenized = [_tokenize(c) for c in chunks]
    df = Counter()
    for toks in tokenized:
        for term in set(toks):
            df[term] += 1
    n_docs = len(chunks)

    def score(toks: List[str]) -> float:
        if not toks:
            return 0.0
        tf = Counter(toks)
        s = 0.0
        for term in q_terms:
            if term in tf:
                idf = math.log((n_docs + 1) / (df[term] + 1)) + 1.0
                s += (tf[term] / len(toks)) * idf
        return s

    ranked = sorted(
        range(len(chunks)), key=lambda i: score(tokenized[i]), reverse=True
    )
    top = [i for i in ranked if score(tokenized[i]) > 0][:num_results]
    if not top:
        return f"[OFFLINE] No local passages matched: {query}"

    blocks = [f"Local document results for: {query}\n"]
    for rank, i in enumerate(top, start=1):
        excerpt = chunks[i][:600]
        blocks.append(f"[{rank}] (from {sources[i]})\n    {excerpt}\n")
    return "\n".join(blocks)
