## Overview of the next phase of work
The app currently has one mode - the "Chat mode", which allows the user to interact with the Project via Chat.

## Modes
The app consists of a few simple modes. I think each of them can be accomplished with the same ui, no need to use fancy prompt toolkit features like screens or dialogues.

The interface can look like a simple terminal, where inputs are printed to the screen, and are pushed up as new inputs are entered.  

Let's keep it very simple for now.

If input is requested from the user, we simply expect them to enter it as they currently do in the Chat Mode.  If the input is invalid, then we'll provide a message and ask them to try again.

### Chat Mode:
This is the mode that we've already built: allowing the user to chat with the AI. It consists of a simple terminal where Rich (python library) Panels are rendered to represent AI text, and a user prompt is at the bottom to give input to the AI

### App Startup Mode:
- User has already created projects?
	- Yes?
        - List all projects from the database in a numbered markdown list (inside a Rich panel)
		- If user enters one of the project numbers, Chat Mode will be started with that project
		- Last option: if user types `/create`, then they are taken to the `New project wizard`
	- No
		- if no project are available - inform and ask them if they want to start the New Project Wizard.  Valid options are `y / n`.  If user selects `n`, the app says `Goodbye!`

### New project wizard:
Walks the user through one choice at a time. User types in their choices. Interface proceeds to the next choice if the choice was valid, otherwise it reprints the user
- name = any name that's under 40 characters is valid
- ingestion path = wizard immediately validates the path (and that it's a directory and NOT a file) and warns the user if it is not

## Slash commands that are available anywhere:
- /refresh - invokes the ingestion process on the project's *ingestion path* and re-ingests any files that have been modified.  If a project isn't currently active, then a warning message is displayed telling the user to open a project and try again.  


## Claude Plan

Work is split into two phases so Phase 1 can be tested independently before the entry point changes.

---

### Phase 1 — Enrich Chat Mode

Changes to existing files only. `main.py` stays hardcoded at `project_id=1`.

| File | Change |
|---|---|
| `src/yara/db/pgvector.py` | Add `list_projects()` and `get_project()` |
| `src/yara/cli/commands.py` | Add `project: dict \| None` to `CommandContext`; add `/refresh` command |
| `src/yara/cli/chat_ui.py` | Fetch project via `get_project()`, pass into `CommandContext` |

#### `pgvector.py` — new functions

```python
def list_projects() -> list[RealDictRow]:
    return get_dict("SELECT id, name, ingestion_path, last_ingested FROM project ORDER BY id;")

def get_project(project_id: int) -> RealDictRow:
    rows = get_dict("SELECT id, name, ingestion_path, last_ingested FROM project WHERE id = %s;", (project_id,))
    return rows[0]
```

#### `commands.py` — `CommandContext` + `/refresh`

Add `project: dict | None = None` field to the `CommandContext` dataclass.

Add `/refresh` command: guard on `ctx.project`, show spinner with `Live(loading_panel())` while calling `ingest_files_to_db(path, project_id)`, print "Refresh complete." panel when done.

#### `chat_ui.py` — wire project into context

In `chat_loop()`, call `get_project(project_id)` and pass result to `CommandContext(project=project, ...)`.

#### Phase 1 Verification
- Run `python -m yara.main` (still uses `project_id=1`) → Chat Mode loads normally
- Type `/refresh` → spinner appears → "Refresh complete."
- Type `/help` → lists `exit`, `help`, `new`, `refresh`

---

### Phase 2 — Startup Flow

New file + entry point change.

| File | Change |
|---|---|
| `src/yara/cli/startup_ui.py` | **New file** — `startup_loop()` + `project_wizard()` |
| `src/yara/main.py` | Replace hardcoded `project_id=1` with `startup_loop()` |

#### `startup_ui.py` — `startup_loop() -> int`

1. Call `list_projects()`
2. **No projects:** Print info panel, prompt `y/n`. `n` → print "Goodbye!" and `sys.exit(0)`. `y` → call `project_wizard()`.
3. **Projects exist:** Render Rich panel with numbered list of project names + note below: *"Type a number to open a project, or `/create` to create a new one."*
4. Loop: valid number → return that project's id. `/create` → call `project_wizard()`. Otherwise reprint prompt.

#### `startup_ui.py` — `project_wizard() -> int`

1. Prompt for **name** (≤ 40 chars). Escape/Ctrl-C → raise `WizardCancelled`, caught by `startup_loop` to re-show project list.
2. Prompt for **ingestion path** — validate with `os.path.isdir()`. Invalid → print warning, re-ask.
3. `get_or_create_project(name, path)` → `project_id`
4. Show spinner (`loading_panel()` + `Live`) while calling `ingest_files_to_db(path, project_id)`
5. Return `project_id`

#### `main.py` — wire up startup

```python
from yara.cli.startup_ui import startup_loop

def main():
    ...
    project_id = startup_loop()
    chat_loop(project_id=project_id)
```

#### Phase 2 Verification
1. `docker compose up -d && python -m yara.db.setup_db`
2. Run with **no projects** → `y/n` prompt → `n` → "Goodbye!"
3. Run → `y` → wizard → name + valid path → spinner → Chat Mode
4. Exit and re-run → project list → enter `1` → Chat Mode
5. `/create` from list → wizard → new project → Chat Mode





