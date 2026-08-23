"""
Deterministically ensures a user-supplied database URL ends up in the
generated project's .env.example — doesn't rely on the LLM to copy it
into the right file under the right variable name.
"""


def apply_database_url(files: list, database_url: str | None) -> list:
    """
    files: list of {"path": str, "content": str} dicts
    Mutates and returns the same list. No-op if database_url is falsy.
    """
    if not database_url:
        return files

    env_file = next((f for f in files if f["path"].endswith(".env.example")), None)

    if env_file is None:
        backend_file = next((f for f in files if f["path"].startswith("backend/")), None)
        env_path = "backend/.env.example" if backend_file else ".env.example"
        files.append({"path": env_path, "content": f"DATABASE_URL={database_url}\n"})
        return files

    lines = env_file["content"].splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith("DATABASE_URL="):
            lines[i] = f"DATABASE_URL={database_url}"
            replaced = True
            break

    if not replaced:
        lines.append(f"DATABASE_URL={database_url}")

    env_file["content"] = "\n".join(lines) + "\n"
    return files
