# Misc UI improvements

## ERD
ERD: each `project` should have:
    -  an optional description (probably a Postgres TEXT data type), which is part of the Wizard at creation.  No need to write migration code.  I will nuke the DB and re-initialize with src/db/setup_db.py
    - active - boolean data type

## Slash commands
- `/home` slash command - sends you to the home screen, aka the `startup_loop()`

## Home Screen (Select a project page)
The following info should be displayed for each project in `gray50` letters
- description
- number of files

If possible, the contents of the panel will have a ~1 or 2 line margin between them and the panel edge, instead of the text being jammed too close to the edges.

The panel margin should be the same `grey50` as the other panel borders.  Maybe a variant of assistant_panel() from ui_helpers.py, written in the ui_helpers.py module?

`list_projects()` must be updated to include a file count.

Example:
```txt
     
     ╭──────────────────────Yara — Select a Project -------------───────────╮
     │                                                                      │
     │   1) Recipes - lorem ipsum (42)                                      │
     │   2) Software - lorem ipsum  (62)                                    │
     │   3) Electronics - lorem ipsum    (42)                               │
     │                                                                      │
     │   Type a number to open a project, or /create to create a new one.   │
     │                                                                      │
     ╰──────────────────────────────────────────────────────────────────────╯    
```




## Editing existing projects
The user should be able to rename projects or edit the description.  Maybe we can reuse the Project Wizard for this, and just exit the loop early if the project already exists and a ingestion path doesn't need to be specified?

Default input values should be set to the current values.

How about this flow? Use `/edit` slash command.  Only works from the home screen.  Prompts the user to select a project (by number).  Then uses the wizard flow to rename / edit description.

## delete existing project
`/delete` slash command from home screen.  Asks the user to select a project (same as editing existing projects) and marks the project as inactive.  The project is NOT deleted from the database.



## claude plan

> **Note:** The wizard observation (§project wizard) is outdated — `project_wizard()` already calls `ingest_files_to_db` with a `Live`/`loading_panel` spinner (`startup_ui.py:79-82`). No change needed there.

### Files to modify

| File | What changes |
|---|---|
| `src/yara/db/pgvector.py` | Schema columns, `list_projects`, `get_project`, `get_or_create_project`, new `update_project`, new `deactivate_project` |
| `src/yara/cli/ui_helpers.py` | New `home_panel()` helper with padding |
| `src/yara/cli/startup_ui.py` | Home screen rendering, description step in wizard, new `edit_wizard()` / `delete_confirm()` helpers |
| `src/yara/cli/commands.py` | Add `/home` command; remove unused `loading_panel` import |
| `src/yara/cli/chat_ui.py` | Handle `signal["home"]`; return `"home"` from `chat_loop()` |
| `src/yara/main.py` | Wrap startup+chat in a loop to support returning home |

---

### Step 1 — Schema (`pgvector.py` `setup()`)

Add to `CREATE TABLE IF NOT EXISTS project`:
```sql
description TEXT,
active BOOLEAN NOT NULL DEFAULT TRUE
```
User nukes + re-inits (`python -m yara.db.setup_db`) — no migration needed.

---

### Step 2 — DB layer (`pgvector.py`)

**`list_projects()`** — filter active, add description + file count:
```sql
SELECT p.id, p.name, p.description, p.ingestion_path, p.last_ingested,
       COUNT(DISTINCT c.filename) AS file_count
FROM project p
LEFT JOIN chunk c ON c.project_id = p.id
WHERE p.active = TRUE
GROUP BY p.id
ORDER BY p.id;
```

**`get_project()`** — add `description` to SELECT.

**`get_or_create_project(name, ingestion_path, description=None)`** — include `description` in INSERT.

**New `update_project(project_id, name, description)`**:
```sql
UPDATE project SET name = %s, description = %s WHERE id = %s;
```

**New `deactivate_project(project_id)`**:
```sql
UPDATE project SET active = FALSE WHERE id = %s;
```

---

### Step 3 — Panel helper (`ui_helpers.py`)

```python
def home_panel(content: str) -> Panel:
    return Panel(content, title="Yara — Select a Project",
                 border_style="bright_black", padding=(1, 3))
```
Same `bright_black` border style as `assistant_panel`.

---

### Step 4 — Home screen (`startup_ui.py`)

**`startup_loop()`:**
- Use `home_panel()` instead of bare `Panel()`
- Each project line: name in default color + `  {description}  ({file_count})` in `[grey50]`
- Handle `/edit` and `/delete` inline (like `/create` is already handled), calling `edit_wizard()` / `delete_confirm()`

**`project_wizard()`:** Add description prompt after name step:
```python
description = prompt(HTML("<ansiblue>Description (optional): </ansiblue>")).strip() or None
```
Pass `description` to `get_or_create_project()`.

**New `edit_wizard(project)`:** Prompts for name and description with current values as `default=` in `prompt()`. Calls `update_project()`. Does NOT re-prompt for ingestion path or re-ingest.

**New `delete_confirm(project)`:** Prints project name, asks `"Mark as inactive? [y/n]"`, calls `deactivate_project()` on confirm.

---

### Step 5 — `/home` command (`commands.py`)

```python
@register_command("home")
def cmd_home(ctx: CommandContext):
    ctx.signal["home"] = True
```

Also remove unused `loading_panel` from the line-9 import.

---

### Step 6 — Home signal (`chat_ui.py`)

```python
if dispatch(query, ctx):
    if ctx.signal.get("exit"):
        render_assistant("Goodbye!")
        break
    if ctx.signal.get("home"):
        break   # no goodbye message
    continue
```

`chat_loop()` returns `"home"` if home signal is set, `None` otherwise.

---

### Step 7 — App loop (`main.py`)

```python
while True:
    project_id = startup_loop()
    result = chat_loop(project_id=project_id)
    if result != "home":
        break
```

---

---

## Phases

### Phase 1 — DB + Schema ✅ (Steps 1–2)
- `pgvector.py`: add `description` + `active` columns to schema
- `pgvector.py`: update `list_projects`, `get_project`, `get_or_create_project`; add `update_project`, `deactivate_project`

**Test:** Nuke + reinit (`python -m yara.db.setup_db`). Confirm `description` and `active` columns exist in `project` table.

---

### Phase 2 — Home Screen UI (Steps 3–4)
- `ui_helpers.py`: add `home_panel()`
- `startup_ui.py`: use `home_panel`, show description + file count in grey50, add description step to wizard, add `/edit` and `/delete` inline handling

**Test:** Run app. Verify padding, description, file count on home screen. Test `/create` (description prompt). Test `/edit` (pre-filled values). Test `/delete` (project disappears).

---

### Phase 3 — `/home` command + app loop (Steps 5–7)
- `commands.py`: add `/home` command, remove unused `loading_panel` import
- `chat_ui.py`: handle `signal["home"]`, return `"home"` from `chat_loop()`
- `main.py`: wrap startup+chat in `while True` loop

**Test:** From chat, type `/home` — confirm returns to project selection. Type `/exit` — confirm app exits cleanly.
