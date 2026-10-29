import re
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "dist"}
EXTS = {".js", ".jsx", ".ts", ".tsx", ".vue"}

BASE = "import.meta.env.BASE_URL"


def patch_router_basename(project_dir: str) -> list[str]:
    """Add the GitHub Pages base path to the router in frontend/src.
    Returns the list of files that were changed."""
    src = Path(project_dir) / "frontend" / "src"
    changed: list[str] = []
    if not src.exists():
        return changed

    for f in src.rglob("*"):
        if not f.is_file() or f.suffix not in EXTS:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue

        text = f.read_text(encoding="utf-8", errors="ignore")
        if "basename" in text and "BrowserRouter" in text:
            continue  # already handled by the generated code

        new = text
        # React Router: <BrowserRouter>
        new = re.sub(r"<BrowserRouter\s*>", f"<BrowserRouter basename={{{BASE}}}>", new)
        # React Router: createBrowserRouter(routes)
        new = re.sub(
            r"createBrowserRouter\(\s*([A-Za-z_]\w*)\s*\)",
            rf"createBrowserRouter(\1, {{ basename: {BASE} }})",
            new,
        )
        # Vue Router: createWebHistory()
        new = re.sub(r"createWebHistory\(\s*\)", f"createWebHistory({BASE})", new)

        if new != text:
            f.write_text(new, encoding="utf-8")
            changed.append(str(f.relative_to(project_dir)))

    return changed

VITE_VUE_CONFIG = """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
})
"""

POSTCSS_CONFIG = """export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
"""

TAILWIND_CONFIG = """export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
"""


def patch_vue_config(project_dir) -> list[str]:
    """Vue projects: make sure vite/postcss/tailwind configs exist."""
    fe = Path(project_dir) / "frontend"
    pkg = fe / "package.json"
    if not pkg.exists():
        return []
    text = pkg.read_text(encoding="utf-8", errors="ignore")
    if '"vue"' not in text:
        return []

    added = []

    def missing(stem):
        return not any((fe / f"{stem}{ext}").exists() for ext in (".js", ".ts", ".mjs", ".cjs"))

    if missing("vite.config") and "@vitejs/plugin-vue" in text:
        (fe / "vite.config.js").write_text(VITE_VUE_CONFIG, encoding="utf-8")
        added.append("frontend/vite.config.js")
    if "tailwindcss" in text:
        if missing("postcss.config"):
            (fe / "postcss.config.js").write_text(POSTCSS_CONFIG, encoding="utf-8")
            added.append("frontend/postcss.config.js")
        if missing("tailwind.config"):
            (fe / "tailwind.config.js").write_text(TAILWIND_CONFIG, encoding="utf-8")
            added.append("frontend/tailwind.config.js")
    return added

PSYCOPG_LINE = re.compile(r"^\s*psycopg(\[|[=<>~! ]|$)", re.IGNORECASE | re.MULTILINE)


def patch_requirements(project_dir) -> list[str]:
    """If the backend uses the psycopg (v3) driver but requirements.txt
    doesn't list it, add it. Returns what was added."""
    backend = Path(project_dir) / "backend"
    req = backend / "requirements.txt"
    if not req.exists():
        return []

    uses_psycopg3 = False
    for f in backend.rglob("*"):
        if not f.is_file() or any(p in SKIP_DIRS | {"venv", ".venv"} for p in f.parts):
            continue
        if f.suffix in {".py", ".env", ".example", ".toml", ".ini"} or f.name.startswith(".env"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "postgresql+psycopg" in content and "postgresql+psycopg2" not in content:
                uses_psycopg3 = True
                break

    text = req.read_text(encoding="utf-8", errors="ignore")
    if uses_psycopg3 and not PSYCOPG_LINE.search(text):
        req.write_text(text.rstrip() + "\npsycopg[binary]\n", encoding="utf-8")
        return ["psycopg[binary]"]
    return []