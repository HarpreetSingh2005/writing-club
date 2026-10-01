"""
Minimal SearXNG web-search client for Expert Researchers.

SearXNG is a TOOL, not an employee or graph node. This module exposes a single
small function, `search_searxng`, that queries a local SearXNG instance via its
JSON API (/search?q=...&format=json) and returns normalized, deduplicated results.

Failure philosophy:
    SearXNG is an enhancement, never a hard dependency. Transport/format failures
    raise `SearchUnavailableError` so the caller can log "web search unavailable"
    and continue with purely analytical research. Valid JSON responses with zero
    results are NOT failures (return []).
"""

import httpx

from config.env import Env

SNIPPET_MAX = 200  # Truncate result snippets to this many characters.


class SearchUnavailableError(Exception):
    """Raised when SearXNG cannot serve a usable result (offline, timeout, HTML, invalid JSON)."""


def search_searxng(
    query: str,
    max_results: int = 5,
    timeout: float | None = None,
) -> list[dict]:
    """
    Query the configured SearXNG instance and return normalized result dicts.

    Args:
        query: The search query string.
        max_results: Maximum number of distinct results to return.
        timeout: Optional per-request timeout in seconds (defaults to Env.SEARXNG_TIMEOUT).

    Returns:
        A list of dicts with keys: title, url, snippet, engine, engines, score.
        Empty list means the search succeeded but returned no results.

    Raises:
        SearchUnavailableError: If the request failed (non-200), the response was
            HTML instead of JSON, the payload was invalid/parsable JSON, or the
            network failed entirely.
    """
    if not query.strip():
        return []

    if not Env.SEARXNG_URL.strip():
        raise SearchUnavailableError("SearXNG not configured (SEARXNG_URL is empty)")

    timeout = timeout if timeout is not None else Env.SEARXNG_TIMEOUT
    params = {
        "q": query,
        "format": "json",
        "safesearch": 1,
        "language": "en",
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(Env.SEARXNG_URL + "/search", params=params)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
        raise SearchUnavailableError(f"SearXNG request failed: {type(e).__name__}") from e

    if response.status_code != 200:
        raise SearchUnavailableError(f"SearXNG returned HTTP {response.status_code}")

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        raise SearchUnavailableError(f"SearXNG returned {content_type or 'non-JSON content'} (JSON format not enabled?)")

    try:
        payload = response.json()
    except ValueError as e:
        raise SearchUnavailableError(f"SearXNG returned invalid JSON: {e}") from e

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise SearchUnavailableError("SearXNG response missing a 'results' list")

    results = []
    seen = set()

    for item in raw_results:
        if not isinstance(item, dict):
            continue  # Skip malformed individual results without crashing

        url = item.get("url") or ""
        title = item.get("title") or ""
        snippet = (item.get("content") or "").strip()
        engines = item.get("engines") or []
        engine = item.get("engine") or (engines[0] if engines else "")

        # Require at least a URL; skip junk rows (malformed results are not fatal)
        if not url or url in seen:
            continue

        seen.add(url)
        try:
            score = float(item.get("score")) if item.get("score") is not None else 0.0
        except (TypeError, ValueError):
            score = 0.0

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet[:SNIPPET_MAX],
            "engine": engine,
            "engines": engines,
            "score": score,
        })

        if len(results) >= max_results:
            break

    return results