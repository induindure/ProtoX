"""Shared helpers for parsing raw LLM completions used by test_generator and code_fixer."""


def strip_code_fences(raw: str) -> str:
    """Strips a leading/trailing markdown code fence (```python, ```js, etc.) from an LLM response."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("python") or raw.startswith("javascript") or raw.startswith("js") or raw.startswith("json"):
            raw = raw.split("\n", 1)[1]

    raw = raw.strip()
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    return raw.strip()
