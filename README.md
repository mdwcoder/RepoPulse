# RepoPulse

RepoPulse is a desktop application built with Python + Flet to visually inspect the health of a local repository. It is designed as a floating companion app for macOS and Linux: open a repo, scan it, and see where to look first.

## What It Does

- Opens a folder with the native picker using `FilePicker.get_directory_path()`
- Detects whether it looks like a Git repository and still allows scanning a regular folder
- Calculates file hotspots with non-AI heuristics
- Summarizes the current Git state
- Detects heavy deletion since `HEAD`
- Suggests potentially missing entries in `.gitignore`
- Lets you refresh the analysis with `Refresh Scan`
- Saves settings, window geometry, and the last opened repo

## Stack

- Python 3.11+
- Flet
- `pathlib`
- `subprocess` for Git CLI
- JSON for settings and lightweight cache

## Requirements

- Python 3.11 or higher
- Git available in the terminal
- macOS or Linux
- On Linux desktop, Flet needs `zenity` for the native folder picker to work

## Installation

From the project root:

```bash
./init.sh
```

`init.sh` does the following:

1. Detects macOS or Linux
2. Checks for Python 3.11+
3. Creates `.venv` if it does not exist
4. Installs dependencies from `requirements.txt`
5. Creates an executable `repopulse` launcher
6. Tries to install it to `~/.local/bin/repopulse` and falls back to `~/bin/repopulse` if needed
7. Warns you if that path is not in your `PATH`

The script is idempotent. You can run it multiple times without breaking the environment.

## Usage

Quick local run:

```bash
./run.sh
```

If the launcher was added to your `PATH`:

```bash
repopulse
```

## Main Flow

1. Open RepoPulse
2. Click `Open Repository`
3. Select a folder with the native file explorer
4. If the folder contains `.git`, it is analyzed as a Git repository
5. If it does not contain `.git`, the app shows:
   - `This folder does not look like a Git repository.`
   - options `Cancel` and `Scan folder anyway`
6. Navigate through:
   - `Overview`
   - `Hotspots`
   - `Git`
   - `Ignore`
   - `Files`
7. Click `Refresh Scan` to recalculate the current state

## What It Detects

### Per-File Metrics

- line count
- size in bytes
- approximate complexity from control-flow tokens
- approximate maximum nesting
- approximate number of imports
- Git churn
- current Git status
- lines added and removed
- short content preview

### Structural Heuristics

- Large file
- Huge function estimate
- Deep nesting
- Too many conditionals
- Too many imports

### Duplication Heuristics

- Possible duplication block
- Similar repeated fragments across files

### Git Heuristics

- High churn hotspot
- Many uncommitted changes
- Heavy deletion since last commit
- Many untracked files
- Generated files tracked

### Repository Hygiene

- Suggested `.gitignore` entries
- Temporary/local file present
- Build/cache artifact detected

## Interface

The UI follows a compact, technical visual style:

- deep dark theme
- dense, readable cards
- clear severity colors
- lists that are quick to scan
- side panel in wide mode
- modal detail view in narrow mode

### Tabs

- `Overview`: overall score, summary, top hotspots, and recent warnings
- `Hotspots`: priority files and details for each file
- `Git`: current changes, heavy deletion, and recent commits
- `Ignore`: `.gitignore` suggestions
- `Files`: filterable and sortable file inventory

## Desktop Window

RepoPulse uses the Flet desktop API for:

- `page.window.width`
- `page.window.height`
- `page.window.left`
- `page.window.top`
- `page.window.always_on_top`
- `page.window.minimized`
- `page.window.minimizable`
- `page.window.resizable`
- `page.window.on_event`

Behavior:

- resizable and minimizable window
- always-on-top pin
- optional geometry restore
- usable in both narrow vertical and wide layouts
- initial anchoring:
  - Linux: left side
  - macOS: right side

## Settings

They are stored as JSON in the user configuration directory:

- `remember window geometry`
- `restore last repo`
- `always on top default`
- `max preview lines`
- `ignore hidden files`
- `ignore binary files`
- `file size cap for preview`
- `scan ignored directories`
- analysis thresholds

## Logging

Basic activity is logged in:

- scans
- Git calls
- read/execution errors

The default configuration path is:

```text
~/.config/repopulse/
```

## Project Structure

```text
repopulse/
  main.py
  init.sh
  run.sh
  requirements.txt
  README.md
  app/
    ui/
      main_window.py
      header.py
      overview_view.py
      hotspots_view.py
      git_view.py
      ignore_view.py
      files_view.py
      file_detail_panel.py
      settings_dialog.py
      theme.py
    controllers/
      app_controller.py
      scan_controller.py
      settings_controller.py
  core/
    models.py
    enums.py
    scanner.py
    analyzer.py
    git_service.py
    scoring.py
    duplication.py
    gitignore_checker.py
    preview.py
    window_service.py
    repository_validator.py
    utils/
      path_utils.py
      file_utils.py
      text_utils.py
      logger.py
      thresholds.py
  storage/
    settings_store.py
    cache_store.py
  assets/
    icon.png
```

## Limitations of This V1

- It does not use a complex AST or deep semantic analysis
- It does not interpret the full project architecture
- Duplication detection is conservative and approximate
- The health score is heuristic, not "scientific"
- It does not perform destructive Git actions
- It does not use a backend or AI

## Linux Note

For the native folder picker to work correctly on desktop with Flet, `zenity` must be available on the system.
