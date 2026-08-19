"""
Reconstructs a ProtoCode-generated project onto disk in a temp directory,
so it can actually be executed (pytest / jest) instead of just read as text.
"""

import tempfile
from pathlib import Path
from typing import List


def build_project_dir(files: List) -> Path:
    """
    files: list of file objects with .path and .content (request.files from TestRequest)
    Returns the Path to the temp directory the project was written into.
    Caller is responsible for cleanup (shutil.rmtree) once done.
    """
    tmp_root = Path(tempfile.mkdtemp(prefix="prototest_"))

    for file in files:
        rel_path = file.path
        content = file.content

        # guard against path traversal from generated code (../../etc)
        target = (tmp_root / rel_path).resolve()
        if not str(target).startswith(str(tmp_root.resolve())):
            continue  # skip anything trying to escape the temp dir

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return tmp_root