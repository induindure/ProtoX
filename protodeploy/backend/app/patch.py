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