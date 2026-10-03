"""
Makes sure every npm package imported in the generated code is listed in
the matching package.json (frontend/ and Node/Express backends).
"""

import json
import re

from app.services.completeness_checker import _norm

CODE_EXTS = (".js", ".jsx", ".ts", ".tsx", ".vue", ".mjs", ".cjs")

# import x from 'pkg' / import 'pkg' / require('pkg') / import('pkg')
_IMPORT_SPEC = re.compile(
    r"""(?:^\s*import\s+(?:[^'"]*?\s+from\s+)?|\brequire\(\s*|\bimport\(\s*)['"]([^'"]+)['"]""",
    re.MULTILINE,
)

NODE_BUILTINS = {
    "fs", "path", "http", "https", "crypto", "os", "url", "events", "util",
    "stream", "child_process", "zlib", "querystring", "buffer", "assert",
    "net", "tls", "dns", "readline", "timers", "worker_threads", "cluster",
}

# Packages where the version matters for how they're imported.
_JWT_DEFAULT_IMPORT = re.compile(r"""import\s+[\w$]+\s+from\s+['"]jwt-decode['"]""")


def _package_name(spec: str):
    if spec.startswith((".", "/", "@/", "~/", "virtual:", "node:", "http:", "https:")):
        return None
    parts = spec.split("/")
    name = "/".join(parts[:2]) if spec.startswith("@") else parts[0]
    if not name or name in NODE_BUILTINS:
        return None
    return name


def fix_package_json_dependencies(files: list[dict]) -> list[dict]:
    by_path = {_norm(f["path"]): f for f in files}

    # root folder ("frontend", "backend") -> {package names used}
    used: dict[str, set] = {}
    jwt_default_roots = set()

    for path, f in by_path.items():
        if not path.endswith(CODE_EXTS) or "/" not in path:
            continue
        root = path.split("/")[0]
        text = f["content"]
        for m in _IMPORT_SPEC.finditer(text):
            name = _package_name(m.group(1))
            if name:
                used.setdefault(root, set()).add(name)
        if _JWT_DEFAULT_IMPORT.search(text):
            jwt_default_roots.add(root)

    for root, names in used.items():
        pkg_path = f"{root}/package.json"
        pkg_file = by_path.get(pkg_path)
        if pkg_file is None:
            continue
        try:
            pkg = json.loads(pkg_file["content"])
        except Exception:
            print(f"[package-fixer] could not parse {pkg_path}, skipping")
            continue

        deps = pkg.setdefault("dependencies", {})
        listed = set(deps) | set(pkg.get("devDependencies", {})) | set(pkg.get("peerDependencies", {}))

        added = []
        for name in sorted(names - listed):
            deps[name] = "latest"
            added.append(name)

        # jwt-decode v4 has no default export; default-import code needs v3.
        if root in jwt_default_roots:
            for section in ("dependencies", "devDependencies"):
                if "jwt-decode" in pkg.get(section, {}):
                    pkg[section]["jwt-decode"] = "^3.1.2"

        if added or root in jwt_default_roots:
            pkg_file["content"] = json.dumps(pkg, indent=2) + "\n"
            if added:
                print(f"[package-fixer] {pkg_path}: added {', '.join(added)}")

    return files