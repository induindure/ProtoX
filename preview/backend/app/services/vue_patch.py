from pathlib import Path

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