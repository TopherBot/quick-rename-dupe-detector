#!/usr/bin/env python3
"""quick‑rename‑dupe‑detector
A tiny CLI utility that:
  1. Scans a directory recursively.
  2. Auto‑renames files to avoid name collisions (adds _1, _2 …).
  3. Detects exact duplicates by SHA‑256 and moves them to `.duplicates`.
  4. Saves a log (`rename.log`) for instant rollback.

Usage examples (run `python renamer.py --help` for full docs):
  python renamer.py .                # normal run on current folder
  python renamer.py . --dry-run      # preview only
  python renamer.py . --restore      # undo last rename operation
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

LOG_FILE = "rename.log"
DUP_DIR = ".duplicates"

def sha256_path(p: Path) -> str:
    """Return SHA‑256 hex digest of file *p* (fast streaming)."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_rename(src: Path, target: Path) -> Path:
    """Rename *src* to *target*, adding numeric suffixes until free.
    Returns the actual new path.
    """
    if not target.exists():
        src.rename(target)
        return target
    stem, suffix = target.stem, target.suffix
    i = 1
    while True:
        new_name = f"{stem}_{i}{suffix}"
        new_path = target.with_name(new_name)
        if not new_path.exists():
            src.rename(new_path)
            return new_path
        i += 1

def collect_files(root: Path, exclude: List[str]) -> List[Path]:
    """Return a list of all files under *root* respecting *exclude* globs."""
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            if any(path.match(p) for p in exclude):
                continue
            files.append(path)
    return files

def detect_and_move_duplicates(files: List[Path], dry: bool) -> Tuple[Dict[str, str], List[Tuple[Path, Path]]]:
    """Detect exact duplicate files.
    Returns a mapping of duplicate hash -> retained path, and a list of
    (duplicate, retained) moves.
    """
    hash_map: Dict[str, Path] = {}
    dup_actions: List[Tuple[Path, Path]] = []
    for f in files:
        h = sha256_path(f)
        if h in hash_map:
            # Duplicate found – move to .duplicates preserving relative path
            dup_dir = f.parent / DUP_DIR
            dup_dir.mkdir(exist_ok=True)
            target = dup_dir / f.name
            dup_actions.append((f, target))
        else:
            hash_map[h] = f
    # Perform moves (or dry‑run)
    for src, dst in dup_actions:
        if dry:
            print(f"[DRY] Move duplicate {src} → {dst}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
    return {h: str(p) for h, p in hash_map.items()}, dup_actions

def resolve_collisions(files: List[Path], dry: bool) -> List[Tuple[Path, Path]]:
    """Rename files that would clash after normalising names.
    Returns a list of (old_path, new_path) actions.
    """
    seen: Dict[str, Path] = {}
    actions: List[Tuple[Path, Path]] = []
    for f in files:
        # Normalised name: lower‑case, spaces → underscores
        norm = f.name.lower().replace(" ", "_")
        target = f.with_name(norm)
        if norm in seen:
            # Name collision – generate a safe unique name
            new_path = safe_rename(f, target) if not dry else target
            actions.append((f, new_path))
        else:
            if f != target:
                # Rename to normalized version if needed
                new_path = safe_rename(f, target) if not dry else target
                actions.append((f, new_path))
            seen[norm] = f
    # Execute actions when not dry
    if not dry:
        for src, dst in actions:
            if src != dst:
                # already renamed inside safe_rename, nothing more to do
                pass
    else:
        for src, dst in actions:
            print(f"[DRY] Rename {src} → {dst}")
    return actions

def write_log(actions: List[Tuple[Path, Path]]) -> None:
    """Write a JSON log of rename actions for rollback."""
    log = [{"src": str(src), "dst": str(dst)} for src, dst in actions]
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(f"Log written to {LOG_FILE}")

def restore_from_log() -> None:
    if not Path(LOG_FILE).exists():
        print("No log file found; cannot restore.")
        sys.exit(1)
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log = json.load(f)
    for entry in reversed(log):
        src = Path(entry["dst"]).resolve()
        dst = Path(entry["src"]).resolve()
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            print(f"Restored {src} → {dst}")
    Path(LOG_FILE).unlink(missing_ok=True)
    print("Restore complete; log removed.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Quickly rename files to avoid collisions and deduplicate them.")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan (default: current)")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without making changes")
    parser.add_argument("--restore", action="store_true", help="Undo the last rename operation using the log file")
    parser.add_argument("--exclude", action="append", default=[], help="Glob pattern to exclude (can be repeated)")
    parser.add_argument("-v", "--verbose", action="store_true", help="More output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.")
        sys.exit(1)

    if args.restore:
        restore_from_log()
        return

    all_files = collect_files(root, args.exclude)
    if args.verbose:
        print(f"Scanning {len(all_files)} files under {root}")

    # Step 1: duplicate detection & move
    _, dup_moves = detect_and_move_duplicates(all_files, args.dry_run)

    # Refresh file list after possible duplicate moves
    all_files = collect_files(root, args.exclude)

    # Step 2: resolve name collisions
    rename_actions = resolve_collisions(all_files, args.dry_run)

    if rename_actions and not args.dry_run:
        write_log(rename_actions)

    if args.verbose:
        print("Done.")

if __name__ == "__main__":
    main()
