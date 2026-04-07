"""
IdeaScorer — ProtoIdea's custom scoring engine.
Scores each AI-generated idea across 3 dimensions using rule-based heuristics:
  - Feasibility  : can a small team build this?
  - Novelty      : does it sound fresh / non-generic?
  - Market Fit   : does it target a real, specific user group?
Final score = weighted average. Ideas are returned ranked best-first.
"""

import re
from app.models.schemas import IdeaModel, RankedIdea, IdeaScores

# ── Heuristic word lists (your contribution) ──────────────────────────────────

# More features = more scope = harder to build alone
HIGH_COMPLEXITY_KEYWORDS = [
    "blockchain", "ai", "machine learning", "real-time", "3d", "ar", "vr",
    "payment", "streaming", "multi-tenant", "distributed", "iot", "hardware",
]

# Generic ideas that aren't very novel
GENERIC_KEYWORDS = [
    "todo", "to-do", "task manager", "notes", "note-taking", "reminder",
    "calendar", "weather", "news", "blog", "portfolio", "chat", "messaging",
]

# Signals that the target audience is specific and real
SPECIFIC_USER_SIGNALS = [
    "patient", "doctor", "student", "teacher", "farmer", "nurse", "driver",
    "freelancer", "startup", "small business", "elderly", "parent", "developer",
    "researcher", "athlete", "therapist", "caregiver",
]


# ── Scoring functions (each returns 0.0 – 1.0) ───────────────────────────────

def _score_feasibility(idea: IdeaModel) -> float:
    """
    Lower complexity = higher feasibility.
    Penalise ideas with many complex tech hints or high-complexity keywords in description.
    """
    text = (idea.description + " " + " ".join(idea.tech_hints)).lower()
    penalty = sum(1 for kw in HIGH_COMPLEXITY_KEYWORDS if kw in text)
    feature_penalty = max(0, len(idea.features) - 5) * 0.1  # >5 features = scope creep

    score = 1.0 - (penalty * 0.12) - feature_penalty
    return round(max(0.0, min(1.0, score)), 3)


def _score_novelty(idea: IdeaModel) -> float:
    """
    Penalise generic/overused idea types.
    Reward longer, more specific descriptions (more thought = more novel).
    """
    text = (idea.title + " " + idea.description).lower()
    penalty = sum(1 for kw in GENERIC_KEYWORDS if kw in text)

    # Reward specificity — longer description = more unique concept
    description_bonus = min(len(idea.description) / 600, 0.3)

    score = 0.7 - (penalty * 0.2) + description_bonus
    return round(max(0.0, min(1.0, score)), 3)


def _score_market_fit(idea: IdeaModel) -> float:
    """
    Reward ideas that name a specific target user group.
    Vague targets like 'everyone' or 'users' score low.
    """
    target = idea.target_users.lower()

    # Vague targets
    if any(w in target for w in ["everyone", "anybody", "all users", "general"]):
        return 0.3

    # Specific named user group
    specificity_bonus = sum(1 for kw in SPECIFIC_USER_SIGNALS if kw in target)

    # Reward concise, non-empty targeting
    length_bonus = 0.2 if 5 < len(target) < 80 else 0.0

    score = 0.5 + (specificity_bonus * 0.2) + length_bonus
    return round(max(0.0, min(1.0, score)), 3)


# ── Main scorer ───────────────────────────────────────────────────────────────

WEIGHTS = {
    "feasibility": 0.40,   # most important for solo/small team projects
    "novelty":     0.30,
    "market_fit":  0.30,
}


def score_and_rank(ideas: list[IdeaModel]) -> list[RankedIdea]:
    scored = []
    for idea in ideas:
        feasibility = _score_feasibility(idea)
        novelty     = _score_novelty(idea)
        market_fit  = _score_market_fit(idea)

        total = (
            feasibility * WEIGHTS["feasibility"] +
            novelty     * WEIGHTS["novelty"] +
            market_fit  * WEIGHTS["market_fit"]
        )

        scored.append(RankedIdea(       # ✅ proper Pydantic object, not raw dict
            idea=idea,
            scores=IdeaScores(
                feasibility=round(feasibility * 100),
                novelty=round(novelty * 100),
                market_fit=round(market_fit * 100),
                total=round(total * 100),
            )
        ))

    scored.sort(key=lambda x: x.scores.total, reverse=True)  # ✅ attribute access not dict
    return scored