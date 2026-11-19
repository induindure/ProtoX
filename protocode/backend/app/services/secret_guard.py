"""
Keeps secrets (database passwords, API keys) away from the AI models.

- .env files are never sent to the AI.
- Any "scheme://user:password@host" in text sent to the AI has the password
  replaced with ****, and KEY=value lines for secret-looking keys are masked.
- If the AI sends a masked value back, the original is restored locally,
  and any .env file the AI returns is ignored.
"""
import re

_URL_CRED = re.compile(r"([a-zA-Z][a-zA-Z0-9+.\-]*://)([^/\s:@\"']+):([^@\s\"']+)@")
_ENV_SECRET = re.compile(
    r"(?im)^(\s*[A-Z0-9_]*(?:KEY|SECRET|PASSWORD|TOKEN)[A-Z0-9_]*\s*=\s*)([^\s\"'(]+)\s*$"
)
MASK = "****"


def is_env_file(path: str) -> bool:
    name = (path or "").replace("\\", "/").rsplit("/", 1)[-1]
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def mask_secrets(text: str) -> str:
    if not text:
        return text
    text = _URL_CRED.sub(lambda m: f"{m.group(1)}{m.group(2)}:{MASK}@", text)
    return _ENV_SECRET.sub(lambda m: m.group(1) + MASK, text)


def safe_files(files: list[dict]) -> list[dict]:
    """Copy of files that is safe to send to the AI: no .env, secrets masked."""
    return [
        {**f, "content": mask_secrets(f.get("content", ""))}
        for f in files
        if not is_env_file(f.get("path", ""))
    ]


def restore_secrets(new_content: str, original_content: str | None) -> str:
    """Put back real values the AI only saw as ****, using the original file."""
    if not original_content or MASK not in (new_content or ""):
        return new_content
    for pattern in (_URL_CRED, _ENV_SECRET):
        for m in pattern.finditer(original_content):
            real = m.group(0)
            masked = pattern.sub(
                (lambda x: f"{x.group(1)}{x.group(2)}:{MASK}@") if pattern is _URL_CRED
                else (lambda x: x.group(1) + MASK),
                real,
            )
            new_content = new_content.replace(masked, real)
    return new_content
