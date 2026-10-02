"""
Completeness check for generated backends.

Finds local imports that point at files the AI never generated
(e.g. `from ..database import get_db` with no database.py) and asks
the LLM to write just those missing files.
"""

import json
import re
from pathlib import PurePosixPath

from langchain_core.messages import HumanMessage, SystemMessage

_FROM_IMPORT = re.compile(
    r"^\s*from\s+(\.*)([\w.]*)\s+import\s+\(?([^)\n]+)", re.MULTILINE
)

_SYSTEM = """You complete a partially generated Python backend.
Some files are imported by other files but were never written.
Write ONLY the missing files you are asked for.

Rules:
- Each missing file must define every name that other files import from it.
- Match the existing code: same database style (sync or async SQLAlchemy),
  same models, same config/settings names, same import style.
- Use relative imports (`from . import x`, `from .x import y`) between project files.
- Respond with ONLY a JSON object, no explanation, no markdown fences:
  {"files": [{"path": "<exact path given>", "content": "<full file content>"}]}
"""


def _norm(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def find_missing_modules(files: list[dict]) -> dict:
    """Returns {missing_path: [(importing_file, import_line), ...]}."""
    paths = {_norm(f["path"]) for f in files}
    contents = {_norm(f["path"]): f["content"] for f in files}

    dirs = set()
    for p in paths:
        for parent in PurePosixPath(p).parents:
            if str(parent) != ".":
                dirs.add(str(parent))

    def exists(mod: PurePosixPath) -> bool:
        return f"{mod}.py" in paths or str(mod) in dirs

    backend_root = PurePosixPath("backend")
    top_level = {
        PurePosixPath(p).relative_to(backend_root).parts[0].removesuffix(".py")
        for p in paths if p.startswith("backend/")
    }

    missing: dict[str, list] = {}

    for path_str, text in contents.items():
        path = PurePosixPath(path_str)
        if path.suffix != ".py" or not path_str.startswith("backend/"):
            continue

        for m in _FROM_IMPORT.finditer(text):
            dots, module, names = m.groups()
            line = m.group(0).strip()

            if dots:
                base = path.parent
                for _ in range(len(dots) - 1):
                    base = base.parent
            else:
                if module.split(".")[0] not in top_level:
                    continue  # third-party package like fastapi
                base = backend_root

            if module:
                target = base.joinpath(*module.split("."))
                if not exists(target):
                    missing.setdefault(f"{target}.py", []).append((path_str, line))
            else:
                # `from . import a, b`: each name must be a module or be in __init__.py
                init_text = contents.get(f"{base}/__init__.py", "")
                for n in names.split(","):
                    n = n.split(" as ")[0].strip()
                    if not n:
                        continue
                    if exists(base / n) or re.search(rf"\b{re.escape(n)}\b", init_text):
                        continue
                    missing.setdefault(f"{base / n}.py", []).append((path_str, line))

    return missing


def _parse_json(text: str) -> list[dict]:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return []
    data = json.loads(text[start:end + 1])
    return data.get("files", [])


def fill_missing_files(files: list[dict], llm, max_rounds: int = 2) -> list[dict]:
    for _ in range(max_rounds):
        missing = find_missing_modules(files)
        if not missing:
            return files

        print(f"[completeness] missing files: {list(missing)}")

        involved = {imp for uses in missing.values() for imp, _ in uses}
        key_names = {"models.py", "schemas.py", "config.py", "main.py"}
        context_files = [
            f for f in files
            if _norm(f["path"]) in involved
            or PurePosixPath(_norm(f["path"])).name in key_names
        ]

        needs = "\n".join(
            f"- {p}  (needed by: " + "; ".join(f"{imp}: `{ln}`" for imp, ln in uses) + ")"
            for p, uses in missing.items()
        )
        context = "\n\n".join(
            f"### {_norm(f['path'])}\n{f['content'][:6000]}" for f in context_files
        )
        all_paths = "\n".join(sorted(_norm(f["path"]) for f in files))

        prompt = (
            f"All files in the project:\n{all_paths}\n\n"
            f"Missing files to write:\n{needs}\n\n"
            f"Relevant existing files:\n\n{context}"
        )

        try:
            response = llm.invoke(
                [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
            )
            new_files = _parse_json(response.content)
        except Exception as e:
            print(f"[completeness] could not generate missing files: {e}")
            return files

        added = 0
        for nf in new_files:
            p = _norm(nf.get("path", ""))
            if p in missing and nf.get("content"):
                files.append({"path": p, "content": nf["content"]})
                print(f"[completeness] added {p}")
                added += 1

        if added == 0:
            return files

    return files