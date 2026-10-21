"""
Vue projects sometimes get React-only libraries (most often lucide-react),
which can't render inside Vue components and leave pages blank.
Swaps them for their Vue equivalents.
"""

import json
import re

from app.services.completeness_checker import _norm

# React-only package -> Vue equivalent (same export names)
_REACT_TO_VUE = {
    "lucide-react": "lucide-vue-next",
}


def fix_vue_react_libs(files: list[dict]) -> list[dict]:
    by_path = {_norm(f["path"]): f for f in files}
    pkg_file = by_path.get("frontend/package.json")
    if pkg_file is None:
        return files
    try:
        pkg = json.loads(pkg_file["content"])
    except Exception:
        return files

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    if "vue" not in deps:
        return files  # not a Vue project

    for react_lib, vue_lib in _REACT_TO_VUE.items():
        pattern = re.compile(rf"""(['"]){re.escape(react_lib)}\1""")

        for path, f in by_path.items():
            if path.startswith("frontend/") and path.endswith((".vue", ".js", ".ts")):
                new_text = pattern.sub(rf"\1{vue_lib}\1", f["content"])
                if new_text != f["content"]:
                    f["content"] = new_text
                    print(f"[vue-fixer] {path}: {react_lib} -> {vue_lib}")

        for section in ("dependencies", "devDependencies"):
            if react_lib in pkg.get(section, {}):
                del pkg[section][react_lib]
                pkg.setdefault("dependencies", {})[vue_lib] = "latest"
                print(f"[vue-fixer] package.json: {react_lib} -> {vue_lib}")

    pkg_file["content"] = json.dumps(pkg, indent=2) + "\n"
    return files

def fix_vue_jsx(files: list[dict]) -> list[dict]:
    """
    Vue projects that contain .jsx/.tsx files need @vitejs/plugin-vue-jsx,
    otherwise Vite compiles the JSX as React ('React is not defined').
    Adds the package and registers the plugin in vite.config.
    """
    by_path = {_norm(f["path"]): f for f in files}
    pkg_file = by_path.get("frontend/package.json")
    if pkg_file is None:
        return files
    try:
        pkg = json.loads(pkg_file["content"])
    except Exception:
        return files

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    if "vue" not in deps:
        return files

    uses_jsx = any(
        p.startswith("frontend/src/") and p.endswith((".jsx", ".tsx"))
        for p in by_path
    )
    if not uses_jsx or "@vitejs/plugin-vue-jsx" in deps:
        return files

    # 1. Add the plugin package.
    pkg.setdefault("devDependencies", {})["@vitejs/plugin-vue-jsx"] = "^4.1.1"
    pkg_file["content"] = json.dumps(pkg, indent=2) + "\n"

    # 2. Register it in vite.config.
    config_path = next(
        (p for p in ("frontend/vite.config.js", "frontend/vite.config.ts", "frontend/vite.config.mjs")
         if p in by_path),
        None,
    )
    if config_path:
        cfg = by_path[config_path]
        text = cfg["content"]
        if "plugins:" in text and "vueJsx" not in text:
            text = re.sub(r"plugins\s*:\s*\[", "plugins: [vueJsx(), ", text, count=1)
            text = "import vueJsx from '@vitejs/plugin-vue-jsx'\n" + text
            cfg["content"] = text
    else:
        # No config at all: create a minimal one.
        files.append({
            "path": "frontend/vite.config.js",
            "content": (
                "import { defineConfig } from 'vite'\n"
                "import vue from '@vitejs/plugin-vue'\n"
                "import vueJsx from '@vitejs/plugin-vue-jsx'\n\n"
                "export default defineConfig({\n"
                "  plugins: [vue(), vueJsx()],\n"
                "})\n"
            ),
        })
        pkg.setdefault("devDependencies", {}).setdefault("@vitejs/plugin-vue", "^5.2.0")
        pkg_file["content"] = json.dumps(pkg, indent=2) + "\n"

    print("[vue-fixer] Vue project uses JSX: added @vitejs/plugin-vue-jsx")
    return files