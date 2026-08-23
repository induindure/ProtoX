"""
Deterministically rewrites the Pydantic v1 `from pydantic import BaseSettings`
pattern to its Pydantic v2 location (`pydantic_settings`) — doesn't rely on the
LLM to remember that BaseSettings moved out of the main pydantic package.
Prompt training data still skews heavily toward the v1 import, and
requirements.txt always resolves to the latest (v2) pydantic release since
it's never version-pinned, so this breaks reliably without a deterministic fix.
"""

import re


def fix_pydantic_v2_settings_import(files: list) -> list:
    """
    files: list of {"path": str, "content": str} dicts
    Mutates and returns the same list.
    """
    for file in files:
        if not file["path"].endswith(".py"):
            continue

        content = file["content"]
        if "BaseSettings" not in content:
            continue

        new_content = re.sub(
            r'from pydantic import ([^\n]*\bBaseSettings\b[^\n]*)',
            _split_import,
            content,
        )
        if new_content != content:
            file["content"] = new_content

    return files


def _split_import(match: re.Match) -> str:
    names = [n.strip() for n in match.group(1).split(",")]
    remaining = [n for n in names if n and n != "BaseSettings"]

    lines = ["from pydantic_settings import BaseSettings"]
    if remaining:
        lines.append(f"from pydantic import {', '.join(remaining)}")
    return "\n".join(lines)
