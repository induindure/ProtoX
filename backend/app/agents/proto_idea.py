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


IDEA_REFINER_SYSTEM = """You are an expert product refinement specialist.
Given an existing app idea and user feedback, refine that specific idea to match the user's needs.

Return ONLY a valid JSON object (NOT an array) with these keys:
  - title        : updated name (string) - keep the core essence but improve if needed
  - description  : updated 2-3 sentence overview (string)
  - features     : updated list of 4-6 core features (array of strings)
  - tech_hints   : updated recommended technologies (array of strings)
  - target_users : updated target users (string)

Make specific improvements based on feedback. Be concise and practical.
No markdown. No explanation. Just the JSON object."""


# ── Groq Client ──────────────────────────────────────────────────────────────

def _get_client() -> AsyncGroq:
    return AsyncGroq(api_key=settings.groq_api_key)


# ── Agent Steps ──────────────────────────────────────────────────────────────

async def _plan(client: AsyncGroq, domain: str, app_type: str, constraints: str) -> str:
    """Step 1 — PLAN: Generate a strategy before jumping into ideas."""
    try:
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
    except Exception as e:
        print(f"[agent] Plan failed (likely invalid API key): {e}")
        return f"Generate ideas for {domain} {app_type} focusing on innovation and user needs."


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


# ── Demo Ideas Fallback (when API keys are invalid) ────────────────────────

DEMO_IDEAS = {
    "healthcare": [
        {
            "title": "TelemedicinePlus",
            "description": "Connect patients with specialists instantly via video consultation. Includes appointment scheduling, prescription management, and secure messaging.",
            "features": ["Video consultations", "Appointment booking", "Prescription management", "Patient history", "Doctor ratings", "Insurance integration"],
            "tech_hints": ["React", "WebRTC", "FastAPI", "PostgreSQL", "Stripe"],
            "target_users": "Patients seeking convenient healthcare, especially in rural areas"
        },
        {
            "title": "MedTrack",
            "description": "AI-powered health monitoring app that tracks vital signs, medications, and symptoms. Alerts doctors and family when anomalies are detected.",
            "features": ["Vital sign logging", "Medication reminders", "Symptom tracking", "AI anomaly detection", "Family alerts", "Health reports"],
            "tech_hints": ["React Native", "TensorFlow Lite", "Firebase", "Python backend"],
            "target_users": "Chronic disease patients and elderly individuals"
        },
        {
            "title": "HealthHub Community",
            "description": "Peer-to-peer health support network where patients share experiences, tips, and recovery journeys. Moderated by verified healthcare professionals.",
            "features": ["User profiles", "Discussion forums", "Experience sharing", "Expert Q&A", "Resource library", "Progress tracking"],
            "tech_hints": ["React", "Node.js", "MongoDB", "Socket.io"],
            "target_users": "Patients with chronic conditions seeking community support"
        }
    ],
    "education": [
        {
            "title": "SkillMatch",
            "description": "AI-powered skill assessment and personalized learning path generator. Matches students with ideal courses and mentors based on learning style.",
            "features": ["Skill assessment", "Personalized paths", "Mentor matching", "Progress tracking", "Micro-credentials", "Job matching"],
            "tech_hints": ["React", "ML model", "FastAPI", "PostgreSQL"],
            "target_users": "College students and career changers"
        },
        {
            "title": "CollabLearn",
            "description": "Virtual study groups with real-time code sharing, whiteboard collaboration, and AI tutor assistance. Groups form automatically based on course and timezone.",
            "features": ["Real-time collaboration", "Code sharing", "Whiteboard", "AI tutor", "Schedule sync", "Study materials"],
            "tech_hints": ["React", "Node.js", "WebSocket", "OpenAI API"],
            "target_users": "CS and STEM students"
        },
        {
            "title": "CareerCraft",
            "description": "Portfolio-building platform for students. Create project showcase, resume, and connect directly with recruiters. Includes interview prep tools.",
            "features": ["Portfolio builder", "Resume generator", "Recruiter messaging", "Interview prep", "Project showcase", "Skill endorsements"],
            "tech_hints": ["React", "Node.js", "PostgreSQL", "AWS S3"],
            "target_users": "College students preparing for internships and jobs"
        }
    ],
    "finance": [
        {
            "title": "BudgetAI",
            "description": "Smart personal finance assistant using ML to categorize spending, predict future needs, and suggest automated savings strategies.",
            "features": ["Transaction sync", "Auto-categorization", "Spending predictions", "Savings suggestions", "Bill reminders", "Investment tips"],
            "tech_hints": ["React", "Python ML", "Plaid API", "PostgreSQL"],
            "target_users": "Young professionals and students managing finances"
        },
        {
            "title": "MicroInvest",
            "description": "Fractional stock investing app. Start with $1. Auto-invest spare change from purchases. Gamified with challenges and social features.",
            "features": ["Fractional investing", "Round-up investing", "Stock picker", "Challenges", "Social portfolios", "Educational content"],
            "tech_hints": ["React", "Node.js", "Stripe", "Alpaca API"],
            "target_users": "First-time investors and Gen Z"
        },
        {
            "title": "DebtDefeat",
            "description": "Gamified debt payoff tracker. Visualize payoff timeline, get motivational milestones, and connect with accountability buddies.",
            "features": ["Debt tracking", "Payoff plans", "Progress visualization", "Buddy system", "Milestones", "Payoff calculator"],
            "tech_hints": ["React", "Firebase", "Node.js"],
            "target_users": "People with student loans or credit card debt"
        }
    ],
}


def _get_demo_ideas(domain: str) -> List[IdeaModel]:
    """Return demo ideas for the given domain when API keys are invalid."""
    domain_lower = domain.lower()
    demo_set = DEMO_IDEAS.get(domain_lower, DEMO_IDEAS["education"])
    return [IdeaModel(**idea) for idea in demo_set]


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
        try:
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
        except Exception as e:
            print(f"[agent] Generation failed (likely invalid API key): {e}")
            print(f"[agent] Falling back to demo ideas for domain: {domain}")
            return _get_demo_ideas(domain)

    async def refine(
        self,
        title: str,
        description: str,
        features: list,
        tech_hints: list,
        target_users: str,
        feedback: str,
    ) -> IdeaModel:
        """
        Refine a single idea based on user feedback.
        Returns an updated IdeaModel.
        """
        try:
            client = _get_client()
            
            user_content = (
                f"Current idea:\n"
                f"  Title: {title}\n"
                f"  Description: {description}\n"
                f"  Features: {', '.join(features)}\n"
                f"  Tech Stack: {', '.join(tech_hints)}\n"
                f"  Target Users: {target_users}\n\n"
                f"User feedback: {feedback}\n\n"
                "Please refine this idea based on the feedback."
            )
            
            response = await client.chat.completions.create(
                model=MODEL,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": IDEA_REFINER_SYSTEM},
                    {"role": "user", "content": user_content},
                ]
            )
            
            raw = response.choices[0].message.content.strip()
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
            
            try:
                data = json.loads(cleaned)
                return IdeaModel(**data)
            except json.JSONDecodeError:
                # If LLM returns bad JSON, return the original idea with simple modifications
                return IdeaModel(
                    title=title,
                    description=f"{description} (Refined based on: {feedback[:50]}...)",
                    features=features,
                    tech_hints=tech_hints,
                    target_users=target_users,
                )
        except Exception as e:
            print(f"[agent] Refinement failed: {e}")
            # Fallback: return original idea
            return IdeaModel(
                title=title,
                description=description,
                features=features,
                tech_hints=tech_hints,
                target_users=target_users,
            )


proto_idea_agent = ProtoIdeaAgent()