#!/usr/bin/env python3
"""
IDShield AI - Universal Cross-Platform Project Sanitizer
Removes build caches, OS debris, misplaced dependencies, and runtime test artifacts.
Compatible with Windows, macOS, and Linux using Python 3 standard libraries only.
"""

import os
import sys
import shutil
import sqlite3
from pathlib import Path

# Directories to purge recursively wherever found
TARGET_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "~",
}

# Exact file names to delete recursively
TARGET_FILES = {
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "tsconfig.app.tsbuildinfo",
}

# Specific misplaced or generated files relative to this script
SPECIFIC_PURGES = [
    Path("backend") / "node_modules",
    Path("backend") / "package.json",
    Path("backend") / "package-lock.json",
    Path("~"),
    Path("backend") / "~",
    Path("idshield-ai") / "~",
]

# Runtime asset folders to empty while preserving the directory structure
EMPTY_ONLY_DIRS = [
    Path("backend") / "uploads",
    Path("backend") / "reports",
]

def clean_recursive(root_path: Path):
    """Walks the directory tree and purges targeted caches and stray files."""
    deleted_dirs = 0
    deleted_files = 0

    for path in sorted(root_path.rglob("*"), reverse=True):
        # Skip frontend root node_modules or virtual environment dependencies
        if "node_modules" in path.parts and not ("backend" in path.parts and "node_modules" in path.parts):
            continue
        if "venv" in path.parts or ".venv" in path.parts or ".git" in path.parts:
            continue

        try:
            if path.is_dir() and path.name in TARGET_DIRS:
                shutil.rmtree(path, ignore_errors=True)
                print(f"  [x] Removed directory: {path}")
                deleted_dirs += 1
            elif path.is_file():
                if path.name in TARGET_FILES or path.name.endswith(".pyc") or path.name.endswith(".pyo"):
                    path.unlink(missing_ok=True)
                    print(f"  [x] Removed file:      {path}")
                    deleted_files += 1
        except Exception as err:
            print(f"  [!] Skipped {path}: {err}", file=sys.stderr)

    return deleted_dirs, deleted_files

def clean_specific_targets(root_path: Path):
    """Removes known misplaced files and clears runtime upload/report directories."""
    for rel_path in SPECIFIC_PURGES:
        target = root_path / rel_path
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            else:
                target.unlink(missing_ok=True)
            print(f"  [x] Purged target:     {rel_path}")

    for rel_dir in EMPTY_ONLY_DIRS:
        target_dir = root_path / rel_dir
        if target_dir.exists() and target_dir.is_dir():
            for item in target_dir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        item.unlink(missing_ok=True)
                    print(f"  [x] Emptied runtime:   {rel_dir / item.name}")
                except Exception as err:
                    print(f"  [!] Failed removing {item}: {err}", file=sys.stderr)
        else:
            target_dir.mkdir(parents=True, exist_ok=True)

def reset_sqlite_db(root_path: Path):
    """Purges runtime test records while preserving SQLite schemas and watchlist entries."""
    db_path = root_path / "backend" / "idshield.db"
    if not db_path.exists():
        return

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents;")
        cursor.execute("DELETE FROM audit_logs;")
        conn.commit()
        conn.close()
        print("  [✓] Database sanitized: Cleared all test documents and audit records.")
    except sqlite3.Error as err:
        print(f"  [!] Database reset warning: {err}", file=sys.stderr)

def main():
    root = Path(__file__).resolve().parent
    print(f"[*] Starting universal sanitize across: {root}")

    # 1. Purge known misplaced artifacts
    clean_specific_targets(root)

    # 2. Walk directory tree for general debris
    d_count, f_count = clean_recursive(root)

    # 3. Reset database records
    reset_sqlite_db(root)

    print(f"\n[✓] Sanitization complete: {d_count} directories and {f_count} files removed.")

if __name__ == "__main__":
    main()