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