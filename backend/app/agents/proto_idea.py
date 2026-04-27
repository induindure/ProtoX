"""
proto_idea.py — ProtoIdea Agentic Pipeline
Replaces single LangChain LLM call with a multi-step agent loop:
  Step 1 — PLAN    : Understand the domain and decide generation strategy
  Step 2 — GENERATE: Call Groq LLM to produce raw ideas
  Step 3 — REFLECT : Validate ideas for quality, diversity, and completeness
  Step 4 — REFINE  : If reflection fails, regenerate with targeted feedback
  Step 5 — PARSE   : Return clean IdeaModel objects for scorer
No LangChain. Pure Groq API + custom agent logic.
"""

import json
import re
from typing import List, Optional
from groq import AsyncGroq

from app.config import settings
from app.models.schemas import IdeaModel


# ── Constants ────────────────────────────────────────────────────────────────

MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 2  # how many times agent will try to refine before giving up


# ── Prompts ──────────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """You are a product strategy planner. 
Given a domain, app type, and constraints, output a brief generation strategy.
Be concise — 3 to 5 bullet points max.
Focus on: target audience gaps, underserved problems, and what makes ideas in this space succeed.
No JSON. Plain text bullets only."""

GENERATOR_SYSTEM = """You are ProtoIdea, an expert software architect and product strategist.
Generate creative but practical application ideas based on the user's inputs and the provided strategy.

Return ONLY a valid JSON array. No markdown, no explanation, no text outside the JSON.
Each object must have exactly these keys:
  - title        : short catchy name (string)
  - description  : 2-3 sentence overview (string)
  - features     : list of 4-6 core features (array of strings)
  - tech_hints   : recommended technologies (array of strings)
  - target_users : who will use this app (string)

Return between 3 and 5 ideas. Each must be buildable by a small team within a few months."""

REFLECTOR_SYSTEM = """You are a strict product idea reviewer.
Given a list of app ideas as JSON, evaluate them and return a JSON object with:
  - passed: true or false
  - issues: list of strings describing problems (empty list if passed)
  - feedback: one sentence of actionable improvement advice (empty string if passed)

Check for:
  1. Are all ideas distinct from each other? (no near-duplicates)
  2. Does each idea clearly solve a real problem?
  3. Are all required fields present and non-empty?
  4. Are tech_hints realistic for the described app?

Return ONLY valid JSON. No markdown, no extra text."""

REFINER_SYSTEM = """You are ProtoIdea. Your previous ideas were reviewed and found lacking.
You will be given the original ideas and specific feedback.
Generate an improved set of 3 to 5 ideas addressing the feedback.

Return ONLY a valid JSON array with the same schema as before:
  - title, description, features, tech_hints, target_users

No markdown. No explanation. Just the JSON array."""


# ── Groq Client ──────────────────────────────────────────────────────────────

def _get_client() -> AsyncGroq:
    return AsyncGroq(api_key=settings.groq_api_key)


# ── Agent Steps ──────────────────────────────────────────────────────────────

async def _plan(client: AsyncGroq, domain: str, app_type: str, constraints: str) -> str:
    """Step 1 — PLAN: Generate a strategy before jumping into ideas."""
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0.4,  # low temp — we want focused strategic thinking
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": (
                f"Domain: {domain}\n"
                f"App Type: {app_type}\n"
                f"Constraints: {constraints or 'None'}\n\n"
                "What strategy should guide idea generation here?"
            )}
        ]
    )
    strategy = response.choices[0].message.content.strip()
    return strategy


async def _generate(
    client: AsyncGroq,
    domain: str,
    app_type: str,
    constraints: str,
    strategy: str,
    feedback: Optional[str] = None,
    previous_ideas_raw: Optional[str] = None,
) -> str:
    """Step 2 — GENERATE (or Step 4 — REFINE if feedback provided)."""

    if feedback and previous_ideas_raw:
        # Refine mode
        system = REFINER_SYSTEM
        user_content = (
            f"Domain: {domain}\n"
            f"App Type: {app_type}\n"
            f"Constraints: {constraints or 'None'}\n\n"
            f"Previous ideas:\n{previous_ideas_raw}\n\n"
            f"Reviewer feedback: {feedback}\n\n"
            "Generate improved ideas now."
        )
    else:
        # Fresh generation
        system = GENERATOR_SYSTEM
        user_content = (
            f"Domain: {domain}\n"
            f"App Type: {app_type}\n"
            f"Constraints: {constraints or 'None'}\n\n"
            f"Generation strategy to follow:\n{strategy}\n\n"
            "Generate the ideas now."
        )

    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0.8,  # higher temp — we want creative ideas
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]
    )
    return response.choices[0].message.content.strip()


async def _reflect(client: AsyncGroq, raw_ideas: str) -> dict:
    """Step 3 — REFLECT: Ask LLM to validate its own output."""
    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0.1,  # very low temp — we want consistent, critical evaluation
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": f"Review these ideas:\n{raw_ideas}"}
        ]
    )
    raw = response.choices[0].message.content.strip()
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # If reflector itself returns bad JSON, just pass through
        return {"passed": True, "issues": [], "feedback": ""}


# ── Parser ───────────────────────────────────────────────────────────────────

def _parse_ideas(raw: str) -> List[IdeaModel]:
    """Clean and parse raw LLM JSON output into IdeaModel list."""
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw:\n{raw}")

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got: {type(data)}")

    ideas = []
    for item in data:
        try:
            ideas.append(IdeaModel(**item))
        except Exception as e:
            raise ValueError(f"Invalid idea object: {e}\nItem: {item}")
    return ideas


# ── Main Agent Class ──────────────────────────────────────────────────────────

class ProtoIdeaAgent:
    """
    Multi-step agentic pipeline for idea generation.
    
    Loop:
      PLAN → GENERATE → REFLECT → (REFINE if needed, up to MAX_RETRIES) → PARSE
    """

    async def generate(self, domain: str, app_type: str, constraints: str = "") -> List[IdeaModel]:
        client = _get_client()

        # ── Step 1: PLAN ──────────────────────────────────────────────────────
        strategy = await _plan(client, domain, app_type, constraints)

        # ── Step 2: GENERATE ──────────────────────────────────────────────────
        raw_ideas = await _generate(client, domain, app_type, constraints, strategy)

        # ── Step 3 + 4: REFLECT → REFINE loop ────────────────────────────────
        feedback = None
        for attempt in range(MAX_RETRIES):
            reflection = await _reflect(client, raw_ideas)

            if reflection.get("passed", True):
                break  # ideas are good, move on

            feedback = reflection.get("feedback", "Improve the ideas.")
            issues = reflection.get("issues", [])
            print(f"[agent] Reflection attempt {attempt + 1} failed. Issues: {issues}")
            print(f"[agent] Refining with feedback: {feedback}")

            # ── Step 4: REFINE ────────────────────────────────────────────────
            raw_ideas = await _generate(
                client, domain, app_type, constraints,
                strategy=strategy,
                feedback=feedback,
                previous_ideas_raw=raw_ideas,
            )

        # ── Step 5: PARSE ─────────────────────────────────────────────────────
        return _parse_ideas(raw_ideas)


proto_idea_agent = ProtoIdeaAgent()