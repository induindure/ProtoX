"""
Frontend completeness check (React / Vue / Next.js).

Finds imports between project files that can't work, e.g.
    import { useAuth } from './api/auth'
when api/auth.js doesn't export useAuth (or doesn't exist at all),
and asks the LLM to add the missing exports or write the missing file.
Missing CSS files are created empty without calling the LLM.
"""

import posixpath
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.completeness_checker import _norm, _parse_json

CODE_EXTS = (".js", ".jsx", ".ts", ".tsx", ".vue")
ASSET_EXTS = (".css", ".scss", ".sass", ".less", ".svg", ".png",
              ".jpg", ".jpeg", ".gif", ".webp", ".json")
RESOLVE_SUFFIXES = ["", ".js", ".jsx", ".ts", ".tsx", ".vue",
                    "/index.js", "/index.jsx", "/index.ts", "/index.tsx"]

# import X from '...' / import { a, b as c } from '...' / import X, { a } from '...'
_IMPORT_FROM = re.compile(
    r"""^\s*import\s+(?:type\s+)?([\w$]+)?\s*,?\s*(\{[^}]*\})?\s*from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
# import './index.css'
_IMPORT_BARE = re.compile(r"""^\s*import\s+['"]([^'"]+)['"]""", re.MULTILINE)

_EXPORT_DEFAULT = re.compile(r"\bexport\s+default\b")
_EXPORT_DECL = re.compile(
    r"\bexport\s+(?:declare\s+)?(?:async\s+)?"
    r"(?:const|let|var|function\*?|class|interface|type|enum)\s+([\w$]+)"
)
_EXPORT_LIST = re.compile(r"\bexport\s+(?:type\s+)?\{([^}]*)\}")
_EXPORT_STAR = re.compile(r"\bexport\s+\*\s+from\b")
_COMMONJS = re.compile(r"\bmodule\.exports\b|\bexports\.[\w$]+\s*=")

_SYSTEM = """You fix a generated frontend project (React, Vue or Next.js) whose files don't fit together.
Some files import names that the target file doesn't export, or import files that don't exist.

For each target file:
- If it EXISTS: return the COMPLETE updated file. Keep everything already in it,
  and add the missing exports, implemented properly based on how the importing files use them.
- If it is MISSING: write the complete file, exporting exactly what the importers need.

Use the same language, framework and style as the rest of the project.
Respond with ONLY a JSON object, no explanation, no markdown fences:
{"files": [{"path": "<exact path given>", "content": "<full file content>"}]}
"""


def _exports(text: str):
    """Returns (named_exports, has_default), or None if we can't tell."""
    if _EXPORT_STAR.search(text) or _COMMONJS.search(text):
        return None
    names = {m.group(1) for m in _EXPORT_DECL.finditer(text)}
    has_default = bool(_EXPORT_DEFAULT.search(text))
    for m in _EXPORT_LIST.finditer(text):
        for item in m.group(1).split(","):
            item = re.sub(r"^type\s+", "", item.strip())
            if not item:
                continue
            exported = item.split(" as ")[-1].strip()
            if exported == "default":
                has_default = True
            else:
                names.add(exported)
    return names, has_default


def _resolve(importer: str, spec: str, paths: set):
    """Returns (path, exists). path is None for third-party packages."""
    if spec.startswith("@/"):
        root = importer.split("/")[0]
        bases = [f"{root}/src/{spec[2:]}", f"{root}/{spec[2:]}"]
    elif spec.startswith("."):
        bases = [posixpath.normpath(posixpath.join(posixpath.dirname(importer), spec))]
    else:
        return None, False

    for base in bases:
        for suffix in RESOLVE_SUFFIXES:
            if base + suffix in paths:
                return base + suffix, True
    return bases[0], False


def _new_file_path(base: str, importer: str, default_name: str | None) -> str:
    if posixpath.splitext(base)[1] in CODE_EXTS:
        return base
    ts = importer.endswith((".ts", ".tsx"))
    is_component = bool(default_name) and default_name[0].isupper()
    if importer.endswith(".vue") and is_component:
        return base + ".vue"
    if is_component:
        return base + (".tsx" if ts else ".jsx")
    return base + (".ts" if ts else ".js")


def find_frontend_problems(files: list[dict]):
    contents = {_norm(f["path"]): f["content"] for f in files}
    paths = set(contents)
    problems: dict[str, dict] = {}
    missing_css: list[str] = []

    for path, text in contents.items():
        if not path.startswith("frontend/") or not path.endswith(CODE_EXTS):
            continue

        # Side-effect imports like `import './App.css'`
        for m in _IMPORT_BARE.finditer(text):
            target, ok = _resolve(path, m.group(1), paths)
            if target and not ok and target.endswith((".css", ".scss")):
                missing_css.append(target)

        for m in _IMPORT_FROM.finditer(text):
            default_name, braces, spec = m.groups()
            if spec.endswith(ASSET_EXTS):
                continue

            target, ok = _resolve(path, spec, paths)
            if target is None:
                continue  # third-party package

            needed = set()
            if braces:
                for item in braces.strip("{}").split(","):
                    item = re.sub(r"^type\s+", "", item.strip())
                    if item:
                        needed.add(item.split(" as ")[0].strip())

            if ok:
                if target.endswith(".vue"):
                    continue  # .vue files always have a default export
                exp = _exports(contents[target])
                if exp is None:
                    continue
                names, has_default = exp
                missing_names = needed - names
                missing_default = bool(default_name) and not has_default
                if not missing_names and not missing_default:
                    continue
            else:
                missing_names = needed
                missing_default = bool(default_name)
                target = _new_file_path(target, path, default_name)

            p = problems.setdefault(
                target, {"exists": ok, "names": set(), "default": False, "importers": {}}
            )
            p["names"] |= missing_names
            p["default"] = p["default"] or missing_default
            p["importers"].setdefault(path, []).append(m.group(0).strip())

    return problems, missing_css


def fill_missing_frontend_exports(files: list[dict], llm, max_rounds: int = 2) -> list[dict]:
    for _ in range(max_rounds):
        problems, missing_css = find_frontend_problems(files)

        existing = {_norm(f["path"]) for f in files}
        for css in missing_css:
            if css not in existing:
                files.append({"path": css, "content": "/* file was missing; created empty */\n"})
                existing.add(css)
                print(f"[frontend-check] created empty {css}")

        if not problems:
            return files

        print(f"[frontend-check] fixing: {list(problems)}")

        contents = {_norm(f["path"]): f["content"] for f in files}
        sections = []
        for target, p in problems.items():
            needs = []
            if p["default"]:
                needs.append("a default export")
            if p["names"]:
                needs.append("named exports: " + ", ".join(sorted(p["names"])))
            status = "EXISTS" if p["exists"] else "MISSING"

            section = f"## Target: {target} ({status})\nMust provide: {'; '.join(needs)}\n"
            if p["exists"]:
                section += f"\nCurrent content of {target}:\n{contents[target][:6000]}\n"
            for imp, lines in list(p["importers"].items())[:5]:
                section += (
                    f"\nUsed by {imp} (imports: {' | '.join(lines)}):\n"
                    f"{contents[imp][:6000]}\n"
                )
            sections.append(section)

        all_paths = "\n".join(sorted(existing))
        prompt = f"All files in the project:\n{all_paths}\n\n" + "\n\n".join(sections)

        try:
            response = llm.invoke(
                [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
            )
            new_files = _parse_json(response.content)
        except Exception as e:
            print(f"[frontend-check] could not fix: {e}")
            return files

        by_path = {_norm(f["path"]): f for f in files}
        changed = 0
        for nf in new_files:
            p = _norm(nf.get("path", ""))
            if p not in problems or not nf.get("content"):
                continue
            if p in by_path:
                by_path[p]["content"] = nf["content"]
                print(f"[frontend-check] updated {p}")
            else:
                files.append({"path": p, "content": nf["content"]})
                print(f"[frontend-check] added {p}")
            changed += 1

        if changed == 0:
            return files

    return files