"""Fail if the Action distribution grows beyond its explicitly reviewed files."""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = "packages/adaptorch-client/src/adaptorch_client/"
ALLOWED = {
    ".github/workflows/ci.yml",
    ".gitignore",
    "LICENSE",
    "README.md",
    "action.yml",
    "github_action/main.py",
    "github_action/tests/mock_server.py",
    "github_action/tests/test_action.py",
    "scripts/check_public_boundary.py",
    *(CLIENT + name for name in (
        "__init__.py", "client.py", "config.py", "errors.py", "json_limits.py",
        "keepalive.py", "models.py", "polling.py", "provider.py", "py.typed",
        "report.py", "responses.py", "transport.py",
    )),
}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "provider key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "github token": re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    "adaptorch key": re.compile(r"\bado_(?:live|prod)_[A-Za-z0-9_-]{20,}\b"),
}


def main() -> int:
    errors: list[str] = []
    found: set[str] = set()
    for directory, subdirectories, filenames in os.walk(ROOT, followlinks=False):
        directory_path = Path(directory)
        for name in list(subdirectories):
            path = directory_path / name
            if path.is_symlink():
                errors.append(f"symlink directory: {path.relative_to(ROOT)}")
                subdirectories.remove(name)
            elif name in {".git", "__pycache__"}:
                subdirectories.remove(name)
        for name in filenames:
            path = directory_path / name
            relative = path.relative_to(ROOT).as_posix()
            if path.is_symlink():
                errors.append(f"symlink file: {relative}")
                continue
            found.add(relative)
            if relative not in ALLOWED:
                errors.append(f"unreviewed file: {relative}")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.append(f"unreadable or non-text file: {relative}")
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    errors.append(f"possible {label}: {relative}")
            if path.suffix != ".py":
                continue
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError:
                errors.append(f"invalid Python: {relative}")
                continue
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for module in names:
                    root = module.split(".", 1)[0]
                    if root != "adaptorch_client" and root not in sys.stdlib_module_names:
                        errors.append(f"non-client or non-stdlib import: {relative}")
    missing = ALLOWED - found
    errors.extend(f"missing reviewed file: {path}" for path in sorted(missing))
    if errors:
        for error in sorted(set(errors)):
            print(error, file=sys.stderr)
        return 1
    print(f"Public distribution boundary passed ({len(found)} reviewed files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
