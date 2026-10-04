"""Read-only binding of source bytes. Integrity is not truth or capability."""
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(root: Path, manifest: dict) -> list[str]:
    root = root.resolve()
    failures = []
    for item in manifest["sources"]:
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Source path escapes project root")
        if not path.is_file() or sha256(path) != item["sha256"]:
            failures.append(item["path"])
    return failures
