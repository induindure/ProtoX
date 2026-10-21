"""
One place that decides which AI model ProtoTest uses.
Groq or Gemini first (LLM_PROVIDER in .env), the other as automatic fallback.
"""

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq


def get_llm(max_tokens: int = 8000, temperature: float = 0.3):
    groq = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="openai/gpt-oss-120b",
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort="low",
        max_retries=1,
    )

    if not os.getenv("GOOGLE_API_KEY"):
        return groq

    from langchain_google_genai import ChatGoogleGenerativeAI

    gemini = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        max_output_tokens=max_tokens,
    )

    if os.getenv("LLM_PROVIDER", "groq") == "gemini":
        return gemini.with_fallbacks([groq])
    return groq.with_fallbacks([gemini])


def message_text(response) -> str:
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


def complete(system_prompt: str, user_prompt: str, max_tokens: int = 8000) -> str:
    """Ask the AI with a system + user prompt; returns plain text."""
    llm = get_llm(max_tokens=max_tokens)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    return message_text(response)