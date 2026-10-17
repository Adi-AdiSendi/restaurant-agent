"""Fail if any source or agent-instruction file exceeds its line limit.

Limits and exemptions are defined in docs/decisions/0007-line-limits.md.
Usage: python scripts/check_line_limits.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE_LIMIT = 100
TEST_LIMIT = 150

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".css"}

# Agent instruction files, checked against SOURCE_LIMIT.
INSTRUCTION_GLOBS = ["CLAUDE.md", "**/CLAUDE.md", ".claude/rules/*.md", ".claude/agents/*.md"]

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "dist", "build",
    "__pycache__", ".pytest_cache", ".ruff_cache", "migrations",
}

# Generated or config files that are exempt by design.
EXEMPT_NAMES = {"vite-env.d.ts", "vite.config.ts", "eslint.config.js"}


def is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)


def is_test(path: Path) -> bool:
    name = path.name
    in_tests_dir = "tests" in path.relative_to(ROOT).parts
    return in_tests_dir or name.startswith("test_") or ".test." in name


def limit_for(path: Path) -> int:
    return TEST_LIMIT if is_test(path) else SOURCE_LIMIT


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def source_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in SOURCE_SUFFIXES
        and path.name not in EXEMPT_NAMES
        and not is_skipped(path)
    ]


def instruction_files() -> list[Path]:
    found: set[Path] = set()
    for pattern in INSTRUCTION_GLOBS:
        found.update(p for p in ROOT.glob(pattern) if p.is_file() and not is_skipped(p))
    return sorted(found)


def find_violations() -> list[str]:
    violations: list[str] = []
    for path in source_files():
        lines, limit = count_lines(path), limit_for(path)
        if lines > limit:
            violations.append(f"{path.relative_to(ROOT)}: {lines} lines (limit {limit})")
    for path in instruction_files():
        lines = count_lines(path)
        if lines > SOURCE_LIMIT:
            violations.append(f"{path.relative_to(ROOT)}: {lines} lines (limit {SOURCE_LIMIT})")
    return sorted(violations)


def main() -> int:
    violations = find_violations()
    if violations:
        print("Line limit exceeded. Split these files by responsibility:")
        for violation in violations:
            print(f"  {violation}")
        return 1
    print("Line limits OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
