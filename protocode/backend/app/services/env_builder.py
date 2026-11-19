"""
Puts the user's database URL into the generated project WITHOUT the AI ever
seeing it. The real URL goes only into backend/.env (never sent to the AI,
deleted by ProtoDeploy before pushing to GitHub). .env.example only gets a
placeholder.
"""
from urllib.parse import urlsplit


def _placeholder(database_url: str) -> str:
    scheme = urlsplit(database_url).scheme or "postgresql"
    if scheme.startswith("sqlite"):
        return f"{scheme}:///./app.db"
    return f"{scheme}://USER:PASSWORD@HOST:5432/DATABASE"


def _set_line(content: str, value: str) -> str:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("DATABASE_URL="):
            lines[i] = f"DATABASE_URL={value}"
            break
    else:
        lines.append(f"DATABASE_URL={value}")
    return "\n".join(lines) + "\n"


def apply_database_url(files: list, database_url: str | None) -> list:
    """
    files: list of {"path": str, "content": str} dicts
    Mutates and returns the same list. No-op if database_url is falsy.
    """
    if not database_url:
        return files

    has_backend = any(f["path"].startswith("backend/") for f in files)
    prefix = "backend/" if has_backend else ""

    # .env.example: placeholder only
    example = next((f for f in files if f["path"].endswith(".env.example")), None)
    if example is None:
        files.append({"path": f"{prefix}.env.example", "content": ""})
        example = files[-1]
    example["content"] = _set_line(example["content"], _placeholder(database_url))

    # .env: the real value
    env_path = f"{prefix}.env"
    env = next((f for f in files if f["path"] == env_path), None)
    if env is None:
        files.append({"path": env_path, "content": ""})
        env = files[-1]
    env["content"] = _set_line(env["content"], database_url)
    return files
