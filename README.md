# quick‑rename‑dupe‑detector

**What it does**
- Scans a target directory (recursively) for files whose names clash after a sanitising step.
- Auto‑renames colliding files by appending an incrementing suffix (`_1`, `_2`, …).
- Detects exact duplicates (identical SHA‑256 hash) and moves them to a hidden `.duplicates` folder.
- Provides concise, colour‑coded console output and an **instant‑recovery** mode that restores original names from a generated log.

**Why it fits the TopherBot vibe**
- ⚡ *Quick actions*: single‑command run, finishes in sub‑second for typical directories.
- 🔄 *Auto‑rename*: no manual pattern editing required.
- 🕵️ *Duplicate detection*: built‑in hash comparison.
- 🪲 *Instant error recovery*: log file (`rename.log`) allows you to roll back.

**Installation**
```bash
# Requires Python 3.9+
python -m pip install --user quick-rename-dupe-detector
```
Or just clone and run the single script:
```bash
git clone https://github.com/yourname/quick-rename-dupe-detector.git
cd quick-rename-dupe-detector
python renamer.py --help
```

**Usage**
```bash
# Basic run on current directory
python renamer.py .

# Dry‑run (shows what would happen, makes no changes)
python renamer.py . --dry-run

# Restore original names from the last run
python renamer.py . --restore
```

**Options**
| Flag | Description |
|------|-------------|
| `--dry-run` | Show actions without modifying the filesystem |
| `--restore` | Revert renames using the last generated `rename.log` |
| `--exclude <pattern>` | Glob pattern(s) to skip (e.g., `*.png`) |
| `-v/--verbose` | More detailed logging |

**Contributing**
- Fork the repo, add a feature or fix, and open a PR.
- Please keep the CLI fast; avoid heavy dependencies.

**License**
MIT – see `LICENSE`.
