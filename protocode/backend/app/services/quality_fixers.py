"""
Deterministic post-processing fixers. Same contract as the other fix_* functions:
take the list of {"path", "content"} dicts and return the list.
"""

import re

from app.services.completeness_checker import _norm

_FRONT_EXT = (".vue", ".jsx", ".tsx", ".js", ".ts")

# window.location.href = '/login'  ->  window.location.href = import.meta.env.BASE_URL + 'login'
_ABS_REDIRECT = re.compile(
    r"""(?P<fn>(?:window\.)?location\.(?:href|assign|replace))"""
    r"""(?P<op>\s*=\s*|\s*\(\s*)"""
    r"""(?P<q>['"`])/(?P<path>[^'"`$]*)(?P=q)"""
)


def _redirect_repl(m):
    path = m.group("path").replace("'", "\\'")
    return f"{m.group('fn')}{m.group('op')}import.meta.env.BASE_URL + '{path}'"


def fix_absolute_redirects(files):
    out = []
    for f in files:
        path = _norm(f["path"])
        content = f["content"]
        if path.startswith("frontend/") and path.endswith(_FRONT_EXT):
            content = _ABS_REDIRECT.sub(_redirect_repl, content)
        out.append({**f, "content": content})
    return out


# ---------------------------------------------------------------------------
# Seed data: demo rows must not be inserted automatically on startup
# ---------------------------------------------------------------------------

_SEED_NAME = re.compile(r"seed|sample|demo|populate|init_data", re.I)
_WRITES = re.compile(r"\.add\(|\.add_all\(|\.create\(|bulk_create")
_DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)\s*\(.*\)\s*(?:->\s*[^:]+)?:\s*$")
_AUTO_RUN = re.compile(r"""on_event\(\s*["']startup["']\s*\)|lifespan""")


def _indent_of(line):
    return len(line) - len(line.lstrip())


def _guard_seed_functions(content):
    lines = content.split("\n")
    out = []
    changed = False
    for i, line in enumerate(lines):
        out.append(line)
        m = _DEF.match(line)
        if not m or not _SEED_NAME.search(m.group(2)):
            continue
        base = len(m.group(1))
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or _indent_of(lines[j]) > base):
            j += 1
        body = lines[i + 1:j]
        first = next((l for l in body if l.strip()), None)
        if first is None or not _WRITES.search("\n".join(body)):
            continue
        pad = " " * _indent_of(first)
        out.append(f'{pad}if os.getenv("SEED_DEMO_DATA") != "true":')
        out.append(f"{pad}    return")
        changed = True
    return "\n".join(out), changed


def _ensure_import_os(content):
    if re.search(r"^import os\b", content, re.M):
        return content
    m = re.search(r"^(?:import\s|from\s(?!__future__))", content, re.M)
    if m:
        return content[:m.start()] + "import os\n" + content[m.start():]
    return "import os\n" + content


def fix_seed_guard(files):
    out = []
    for f in files:
        path = _norm(f["path"])
        content = f["content"]
        if (
            path.startswith("backend/")
            and path.endswith(".py")
            and "SEED_DEMO_DATA" not in content
            and _AUTO_RUN.search(content)
        ):
            new, changed = _guard_seed_functions(content)
            if changed:
                content = _ensure_import_os(new)
        out.append({**f, "content": content})
    return out