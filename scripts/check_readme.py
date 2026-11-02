"""Check README.md against the repository.

Fails (exit 1) when:
  * an `AUTO:` placeholder is left in the README,
  * a relative link points to a file or directory that does not exist,
  * a `make <target>` command mentioned in the README has no target in the Makefile.

Remaining `TODO(tim)` and `TODO(ljudi)` markers are allowed; they are printed
as a to-do list for the team.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MAKEFILE = ROOT / "Makefile"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
MAKE_RE = re.compile(r"\bmake\s+([a-z][a-z0-9_-]*)")
TARGET_RE = re.compile(r"^([a-zA-Z0-9_-]+)\s*:(?!=)", re.MULTILINE)
TODO_RE = re.compile(r"TODO\((tim|ljudi)\)[^\n]*")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = README.read_text(encoding="utf-8")
    errors: list[str] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        if "AUTO:" in line:
            errors.append(f"README.md:{lineno}: preostala oznaka AUTO:")

    for target in LINK_RE.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        if path and not (ROOT / path).exists():
            errors.append(f"poveznica na nepostojeću datoteku: {target}")

    targets = set(TARGET_RE.findall(MAKEFILE.read_text(encoding="utf-8")))
    for target in sorted(set(MAKE_RE.findall(text))):
        if target not in targets:
            errors.append(f"naredba `make {target}` ne postoji u Makefileu")

    todos = [m.group(0).strip() for m in TODO_RE.finditer(text)]
    if todos:
        print("Preostalo za ljude:")
        for todo in todos:
            print(f"  - {todo}")

    if errors:
        print("README nije usklađen:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("README je usklađen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
