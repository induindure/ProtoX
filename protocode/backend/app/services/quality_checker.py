import re
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", ".venv", "venv", "__pycache__", ".git", "staticfiles"}
FRONT_EXT = {".vue", ".jsx", ".tsx"}
ATTRS = r"((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)"          # attribute text, tolerates '=>' and quotes
BUTTON_RE = re.compile(r"<button\b" + ATTRS + r">(.*?)</button>", re.S | re.I)
HANDLER_RE = re.compile(r"(@click|v-on:click|onClick|\btype\s*=\s*[\"']submit[\"'])", re.I)
ABS_REDIRECT_RE = re.compile(r"(location\.href|location\.assign|location\.replace)\s*[=(]\s*[`'\"]/")


def _files(root: Path, exts):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in exts and not (set(p.parts) & SKIP_DIRS):
            yield p


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_project(root: Path) -> list[dict]:
    issues = []

    # --- frontend checks ---
    for f in _files(root / "frontend", FRONT_EXT | {".js", ".ts"}):
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel = str(f.relative_to(root))

        if f.suffix in FRONT_EXT:
            has_form = "<form" in text.lower()
            for m in BUTTON_RE.finditer(text):
                attrs = m.group(1)
                if not HANDLER_RE.search(attrs) and not (has_form and "type" not in attrs.lower()):
                    label = re.sub(r"<[^>]+>|\s+", " ", m.group(2)).strip()[:40]
                    issues.append({"file": rel, "line": _line_of(text, m.start()),
                                   "type": "dead_button",
                                   "message": f'Button "{label}" has no click handler'})

        for m in ABS_REDIRECT_RE.finditer(text):
            issues.append({"file": rel, "line": _line_of(text, m.start()),
                           "type": "absolute_redirect",
                           "message": "Absolute redirect breaks under a subpath (GitHub Pages). "
                                      "Use the router or import.meta.env.BASE_URL"})

    # --- backend checks ---
    for f in _files(root / "backend", {".py"}):
        text = f.read_text(encoding="utf-8", errors="ignore")
        rel = str(f.relative_to(root))
        seeds = ("startup" in text or "lifespan" in text) and re.search(r"\.add\(|objects\.create\(", text)
        if seeds and "SEED_DEMO_DATA" not in text:
            issues.append({"file": rel, "line": 1, "type": "auto_seed",
                           "message": "Startup code inserts data without a SEED_DEMO_DATA guard"})

    return issues