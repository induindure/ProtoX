from pathlib import Path
import re
SKIP_DIRS = {"node_modules", ".git", "dist"}

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

def patch_route_tags(project_dir) -> list[str]:
    """Fix '<path path=...>' used instead of '<Route path=...>' inside <Routes>."""
    src = Path(project_dir) / "frontend" / "src"
    changed = []
    if not src.exists():
        return changed
    for f in src.rglob("*"):
        if not f.is_file() or f.suffix not in {".js", ".jsx", ".ts", ".tsx"}:
            continue
        if any(p in SKIP_DIRS for p in f.parts):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "<Routes" not in text or "<path" not in text:
            continue
        new = re.sub(r"<path(\s+path=)", r"<Route\1", text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed.append(str(f.relative_to(project_dir)).replace("\\", "/"))
    return changed