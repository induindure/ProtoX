import io
import tempfile
import zipfile
from pathlib import Path


def extract_project(data: bytes) -> tuple[Path, Path]:
    """Extract ZIP bytes. Returns (project_root, temp_dir_to_delete)."""
    tmp = Path(tempfile.mkdtemp())
    base = tmp.resolve()

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():  # block zip-slip
                if not str((tmp / name).resolve()).startswith(str(base)):
                    raise ValueError("Unsafe path inside ZIP")
            z.extractall(tmp)
    except zipfile.BadZipFile:
        raise ValueError("File is not a valid ZIP")

    # ZIPs often wrap everything in one top-level folder, so unwrap it
    root = tmp
    for _ in range(3):
        if (root / "frontend").is_dir() and (root / "backend").is_dir():
            return root, tmp
        items = [p for p in root.iterdir() if p.name != "__MACOSX"]
        if len(items) == 1 and items[0].is_dir():
            root = items[0]
        else:
            break

    raise ValueError("ZIP must contain frontend/ and backend/ folders")