"""
One-time migration: adds user accounts + email verification to the protox database.
Safe to run more than once (every statement uses IF NOT EXISTS).

Run from protoidea/backend:
    .venv\\Scripts\\python migrate_auth.py
"""
from sqlalchemy import text

from app.db.database import engine

STATEMENTS = [
    # 1. User accounts. Passwords are stored ONLY as Argon2 hashes, never in plain text.
    """
    CREATE TABLE IF NOT EXISTS users (
        id             UUID PRIMARY KEY,
        email          TEXT NOT NULL UNIQUE,
        password_hash  TEXT NOT NULL,
        is_verified    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        verified_at    TIMESTAMPTZ
    )
    """,

    # 2. One-time tokens for email verification (and password reset later).
    #    We store only a SHA-256 hash of the token, so even someone reading the
    #    database cannot use a token to verify or take over an account.
    """
    CREATE TABLE IF NOT EXISTS email_tokens (
        id          UUID PRIMARY KEY,
        user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash  TEXT NOT NULL UNIQUE,
        purpose     TEXT NOT NULL,
        expires_at  TIMESTAMPTZ NOT NULL,
        used_at     TIMESTAMPTZ,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_email_tokens_user ON email_tokens(user_id)",

    # 3. Make sure the ideas table exists (in case it was never created locally).
    """
    CREATE TABLE IF NOT EXISTS ideas (
        id          UUID PRIMARY KEY,
        session_id  TEXT NOT NULL,
        domain      TEXT NOT NULL,
        app_type    TEXT NOT NULL,
        constraints TEXT,
        ideas       JSONB NOT NULL,
        created_at  TIMESTAMP DEFAULT NOW()
    )
    """,

    # 4. Link each idea to the user who created it.
    "ALTER TABLE ideas ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE",
    "CREATE INDEX IF NOT EXISTS idx_ideas_user_created ON ideas(user_id, created_at DESC)",
]


def main() -> None:
    with engine.begin() as conn:
        for statement in STATEMENTS:
            conn.execute(text(statement))

        tables = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN ('users', 'email_tokens', 'ideas') "
            "ORDER BY table_name"
        )).scalars().all()

        has_user_id = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'ideas' AND column_name = 'user_id'"
        )).first() is not None

    print("Tables found:", ", ".join(tables))
    print("ideas.user_id column:", "OK" if has_user_id else "MISSING")
    print("Auth migration finished.")


if __name__ == "__main__":
    main()