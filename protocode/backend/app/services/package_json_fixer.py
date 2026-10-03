"""
Makes sure every npm package imported in the generated code is listed in
the matching package.json (frontend/ and Node/Express backends), and pins
older major versions when the code uses an older library syntax.
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

# Libraries whose newer major versions broke syntax that AI models often write.
# (package, pattern that detects the OLD syntax, version that supports it)
_VERSION_PINS = [
    (
        "jwt-decode",
        re.compile(r"""import\s+[\w$]+\s+from\s+['"]jwt-decode['"]"""),
        "^3.1.2",
    ),
    (
        "@tanstack/react-query",
        # useQuery(['key'], fn) / useQuery('key', fn) / useMutation(fn)
        re.compile(
            r"""\buse(?:Query|InfiniteQuery|Mutation)\(\s*(?:\[|['"]|(?:async\s*)?\(|[\w$.]+\s*[,)])"""
        ),
        "^4.36.1",
    ),
]

# Companion packages that must match the pinned major version.
_COMPANIONS = {
    "@tanstack/react-query": ["@tanstack/react-query-devtools"],
}


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

    used: dict[str, set] = {}     # root folder -> package names imported
    pins: dict[str, dict] = {}    # root folder -> {package: version}

    for path, f in by_path.items():
        if not path.endswith(CODE_EXTS) or "/" not in path:
            continue
        root = path.split("/")[0]
        text = f["content"]

        for m in _IMPORT_SPEC.finditer(text):
            name = _package_name(m.group(1))
            if name:
                used.setdefault(root, set()).add(name)

        for pkg_name, pattern, version in _VERSION_PINS:
            if pattern.search(text):
                pins.setdefault(root, {})[pkg_name] = version

    for root in set(used) | set(pins):
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
        listed = (
            set(deps)
            | set(pkg.get("devDependencies", {}))
            | set(pkg.get("peerDependencies", {}))
        )

        added = []
        for name in sorted(used.get(root, set()) - listed):
            deps[name] = "latest"
            added.append(name)

        pinned = []
        for name, version in pins.get(root, {}).items():
            for target in [name] + _COMPANIONS.get(name, []):
                section = next(
                    (s for s in ("dependencies", "devDependencies") if target in pkg.get(s, {})),
                    None,
                )
                if section is None:
                    if target != name:
                        continue  # companion not used, nothing to pin
                    section = "dependencies"
                if pkg[section].get(target) != version:
                    pkg[section][target] = version
                    pinned.append(f"{target}@{version}")

        if added or pinned:
            pkg_file["content"] = json.dumps(pkg, indent=2) + "\n"
            if added:
                print(f"[package-fixer] {pkg_path}: added {', '.join(added)}")
            if pinned:
                print(f"[package-fixer] {pkg_path}: pinned {', '.join(pinned)} (code uses older syntax)")

    return files