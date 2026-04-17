"""
scorer.py — ProtoIdea's ML-powered scoring engine.
Replaces rule-based heuristics with models trained on 44,000+ real Product Hunt launches.
Scores each AI-generated idea across 3 dimensions:
  - Feasibility  : can a small team build this?
  - Novelty      : does it sound fresh / non-generic?
  - Market Fit   : does it target a real, specific user group?
Final score = weighted average. Ideas are returned ranked best-first.
"""

import pickle
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_model(name):
    path = os.path.join(BASE_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{name}.pkl not found. Please run train_scorer.py first."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


# Load models once when module is imported
try:
    _market_fit_model  = _load_model("market_fit_model")
    _novelty_model     = _load_model("novelty_model")
    _feasibility_model = _load_model("feasibility_model")
    MODELS_LOADED = True
except FileNotFoundError as e:
    print(f"[scorer] Warning: {e} — falling back to neutral scores.")
    MODELS_LOADED = False


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clamp(value: float, lo=0.0, hi=100.0) -> int:
    return int(round(max(lo, min(hi, value))))


def _score_idea(idea) -> tuple[int, int, int]:
    """
    Takes an IdeaModel and returns (feasibility, novelty, market_fit) as 0-100 ints.
    Combines description + target_users + tech_hints for richer input.
    """
    if not MODELS_LOADED:
        return 50, 50, 50

    # Build a rich text input from all available idea fields
    text_parts = [
        idea.description,
        idea.target_users,
        " ".join(idea.tech_hints) if idea.tech_hints else "",
        " ".join(idea.features) if idea.features else "",
    ]
    combined = _clean_text(" ".join(text_parts))

    if not combined:
        return 50, 50, 50

    feasibility = _clamp(_feasibility_model.predict([combined])[0])
    novelty     = _clamp(_novelty_model.predict([combined])[0])
    market_fit  = _clamp(_market_fit_model.predict([combined])[0])

    return feasibility, novelty, market_fit


# ── Weights (same as before) ──────────────────────────────────────────────────
WEIGHTS = {
    "feasibility": 0.40,
    "novelty":     0.30,
    "market_fit":  0.30,
}


def score_and_rank(ideas):
    """
    Drop-in replacement for the old rule-based score_and_rank.
    Takes a list[IdeaModel], returns a list[RankedIdea] sorted best-first.
    """
    from app.models.schemas import RankedIdea, IdeaScores

    scored = []
    for idea in ideas:
        feasibility, novelty, market_fit = _score_idea(idea)

        total = int(
            feasibility * WEIGHTS["feasibility"] +
            novelty     * WEIGHTS["novelty"] +
            market_fit  * WEIGHTS["market_fit"]
        )

        scored.append(RankedIdea(
            idea=idea,
            scores=IdeaScores(
                feasibility=feasibility,
                novelty=novelty,
                market_fit=market_fit,
                total=total,
            )
        ))

    scored.sort(key=lambda x: x.scores.total, reverse=True)
    return scored