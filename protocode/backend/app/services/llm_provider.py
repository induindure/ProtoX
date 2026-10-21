"""
One place that decides which AI model ProtoCode uses.
Default: Groq, falling back to Gemini automatically if Groq fails
(e.g. daily token limit reached). Set LLM_PROVIDER=gemini in .env to flip it.
"""

import os

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(max_tokens: int = 32000, temperature: float = 0.5, small: bool = False):
    groq = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-20b" if small else "openai/gpt-oss-120b",
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort="low",
        max_retries=1,  # fail fast so the fallback kicks in quickly
    )

    if not os.getenv("GOOGLE_API_KEY"):
        return groq  # Gemini not configured: Groq only


    gemini = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
    )

    if os.getenv("LLM_PROVIDER", "groq") == "gemini":
        return gemini.with_fallbacks([groq])
    return groq.with_fallbacks([gemini])

def message_text(response) -> str:
    """
    Returns the AI's answer as plain text, whichever provider answered.
    Groq returns a string; Gemini can return a list of parts
    (text blocks, plus 'thinking' blocks we ignore).
    """
    content = response.content
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict) and part.get("type") == "text":
            parts.append(part.get("text", ""))
    return "".join(parts)

import json
import re


def parse_json_loose(text: str):
    """
    Parses the JSON object in an AI reply. If it's invalid because of
    unescaped backslashes (common when the JSON contains code), repairs
    them and tries again. Returns None if it still can't be read.
    """
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    candidate = text[start:end + 1]
    repaired = re.sub(r'\\(?![\\"/bfnrtu])', r"\\\\", candidate)
    for attempt in (candidate, repaired):
        try:
            return json.loads(attempt, strict=False)
        except json.JSONDecodeError:
            continue
    return None