"""
Migration: user accounts + email verification for ProtoX.

Our tables use a "protox_" prefix so they never collide with tables that
generated/previewed apps create in the same database (e.g. their own "users").

Safe to run more than once. Run from protoidea/backend:
    .venv\\Scripts\\python migrate_auth.py
"""
from sqlalchemy import text

from app.db.database import engine

STATEMENTS = [
    # 1. ProtoX user accounts (passwords stored only as Argon2 hashes)
    """
    CREATE TABLE IF NOT EXISTS protox_users (
        id             UUID PRIMARY KEY,
        email          TEXT NOT NULL UNIQUE,
        password_hash  TEXT NOT NULL,
        is_verified    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        verified_at    TIMESTAMPTZ
    )
    """,

    # 2. One-time email tokens (only a SHA-256 hash of each token is stored)
    """
    CREATE TABLE IF NOT EXISTS protox_email_tokens (
        id          UUID PRIMARY KEY,
        user_id     UUID NOT NULL REFERENCES protox_users(id) ON DELETE CASCADE,
        token_hash  TEXT NOT NULL UNIQUE,
        purpose     TEXT NOT NULL,
        expires_at  TIMESTAMPTZ NOT NULL,
        used_at     TIMESTAMPTZ,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_protox_email_tokens_user ON protox_email_tokens(user_id)",
    "ALTER TABLE protox_email_tokens ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0",

    # 3. ideas.user_id: make sure the column exists, then point it at protox_users
    #    (the first version of this script wrongly linked it to the old "users" table)
    "ALTER TABLE ideas ADD COLUMN IF NOT EXISTS user_id UUID",
    "UPDATE ideas SET user_id = NULL WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM protox_users)",
    "ALTER TABLE ideas DROP CONSTRAINT IF EXISTS ideas_user_id_fkey",
    "ALTER TABLE ideas DROP CONSTRAINT IF EXISTS ideas_user_id_protox_fkey",
    """
    ALTER TABLE ideas
        ADD CONSTRAINT ideas_user_id_protox_fkey
        FOREIGN KEY (user_id) REFERENCES protox_users(id) ON DELETE CASCADE
    """,
    "CREATE INDEX IF NOT EXISTS idx_ideas_user_created ON ideas(user_id, created_at DESC)",
]


def main() -> None:
    with engine.begin() as conn:
        for statement in STATEMENTS:
            conn.execute(text(statement))

        cols = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'protox_users' ORDER BY ordinal_position"
        )).scalars().all()

        fk_target = conn.execute(text("""
            SELECT ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'ideas' AND tc.constraint_type = 'FOREIGN KEY'
        """)).scalars().all()

    print("protox_users columns:", ", ".join(cols))
    print("ideas.user_id points to:", ", ".join(fk_target) or "nothing")
    print("Auth migration finished.")


if __name__ == "__main__":
    main()