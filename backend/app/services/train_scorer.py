"""
train_scorer.py
Place this file in backend/app/services/
Run once: python train_scorer.py
It will generate 3 model files in the same folder:
  - market_fit_model.pkl
  - novelty_model.pkl
  - feasibility_model.pkl

Make sure your CSV is in the same folder as this script,
or update CSV_PATH below.
"""

import pandas as pd
import numpy as np
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# ── CONFIG ──────────────────────────────────────────────────────────────────
CSV_PATH = "product-hunt-prouducts-1-1-2014-to-12-31-2021.csv"
# ────────────────────────────────────────────────────────────────────────────


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_and_clean(path):
    print("Loading dataset...")
    df = pd.read_csv(path, low_memory=False)

    # Keep only what we need
    df = df[["name", "product_description", "category_tags", "upvotes", "product_ranking"]].copy()

    # Drop rows with no description or upvotes
    df = df.dropna(subset=["product_description", "upvotes"])
    df = df[df["product_description"].str.strip() != ""]

    # Clean types
    df["upvotes"] = pd.to_numeric(df["upvotes"], errors="coerce")
    df["product_ranking"] = pd.to_numeric(df["product_ranking"], errors="coerce")
    df = df.dropna(subset=["upvotes"])

    # Clean text
    df["clean_desc"] = df["product_description"].apply(clean_text)

    df = df.reset_index(drop=True)  # fix index gaps after dropping rows
    print(f"Dataset loaded: {len(df)} rows after cleaning")
    return df


# ── SCORE 1: MARKET FIT ─────────────────────────────────────────────────────
# Based on upvotes. More upvotes = higher market fit.
def build_market_fit_labels(df):
    scaler = MinMaxScaler(feature_range=(0, 100))
    log_upvotes = np.log1p(df["upvotes"].values).reshape(-1, 1)
    scores = scaler.fit_transform(log_upvotes).flatten()
    return scores


# ── SCORE 2: NOVELTY ────────────────────────────────────────────────────────
# Based on how unique the description is within its category.
# We measure TF-IDF cosine similarity to other items in same category.
# Lower similarity = more novel = higher score.
def build_novelty_labels(df):
    print("Computing novelty scores (this may take a moment)...")
    from sklearn.metrics.pairwise import cosine_similarity

    novelty_scores = np.zeros(len(df))

    # Parse category tags (stored as string like "['TAG1', 'TAG2']")
    def parse_tags(tag_str):
        if not isinstance(tag_str, str):
            return "UNKNOWN"
        tags = re.findall(r"[A-Z][A-Z0-9 ]+", tag_str)
        return tags[0] if tags else "UNKNOWN"

    df = df.copy()
    df["primary_category"] = df["category_tags"].apply(parse_tags)

    tfidf = TfidfVectorizer(max_features=500, stop_words="english")

    for category, group in df.groupby("primary_category"):
        if len(group) < 2:
            novelty_scores[group.index] = 50  # default for lone items
            continue

        try:
            matrix = tfidf.fit_transform(group["clean_desc"])
            sim_matrix = cosine_similarity(matrix)
            # Average similarity to others (excluding self)
            np.fill_diagonal(sim_matrix, 0)
            avg_sim = sim_matrix.mean(axis=1)
            # Invert: low similarity = high novelty
            novelty = 1 - avg_sim
            # Scale to 0-100
            if novelty.max() > novelty.min():
                novelty = (novelty - novelty.min()) / (novelty.max() - novelty.min()) * 100
            else:
                novelty = np.full_like(novelty, 50.0)
            novelty_scores[group.index] = novelty
        except Exception:
            novelty_scores[group.index] = 50

    return novelty_scores


# ── SCORE 3: FEASIBILITY ─────────────────────────────────────────────────────
# Rule-based: penalise descriptions with high-complexity keywords,
# reward descriptions with straightforward/simple keywords.
COMPLEX_KEYWORDS = [
    "blockchain", "ai", "machine learning", "neural", "quantum",
    "real-time", "realtime", "distributed", "decentralized",
    "computer vision", "nlp", "deep learning", "iot", "ar", "vr",
    "augmented reality", "virtual reality", "satellite", "drone",
    "hardware", "embedded", "robotics", "autonomous"
]

SIMPLE_KEYWORDS = [
    "simple", "easy", "quick", "lightweight", "minimal", "basic",
    "tool", "utility", "tracker", "todo", "notes", "reminder",
    "calculator", "converter", "generator", "dashboard", "form",
    "scheduler", "planner", "list", "organizer"
]


def build_feasibility_labels(df):
    scores = []
    for desc in df["clean_desc"]:
        score = 70  # base score
        for kw in COMPLEX_KEYWORDS:
            if kw in desc:
                score -= 5
        for kw in SIMPLE_KEYWORDS:
            if kw in desc:
                score += 3
        score = max(10, min(100, score))  # clamp between 10-100
        scores.append(score)
    return np.array(scores, dtype=float)


# ── TRAIN & SAVE MODELS ──────────────────────────────────────────────────────
def train_and_save(df, labels, model_name):
    print(f"Training {model_name}...")
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")),
        ("model", Ridge(alpha=1.0))
    ])
    X = df["clean_desc"]
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)

    score = pipeline.score(X_test, y_test)
    print(f"  {model_name} R² score: {score:.3f}")

    with open(f"{model_name}.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    print(f"  Saved {model_name}.pkl")


def main():
    df = load_and_clean(CSV_PATH)

    market_fit_labels = build_market_fit_labels(df)
    novelty_labels = build_novelty_labels(df)
    feasibility_labels = build_feasibility_labels(df)

    train_and_save(df, market_fit_labels, "market_fit_model")
    train_and_save(df, novelty_labels, "novelty_model")
    train_and_save(df, feasibility_labels, "feasibility_model")

    print("\nAll models trained and saved successfully!")
    print("Files created: market_fit_model.pkl, novelty_model.pkl, feasibility_model.pkl")


if __name__ == "__main__":
    main()