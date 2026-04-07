## Goal
Implement unit tests on my interaction modules & functions so that I don't have to run the prompt UI through every possible combination of interactions to know that I haven't created a regression

Implement with `pytest`


## Claude Plan

### Out of Scope (Phase 1)
- `startup_ui.py` — wizard flows (project_wizard, edit_wizard, delete_confirm, startup_loop)
- `chat_ui.py` — chat REPL state machine
- `ui_helpers.py` — rendering primitives
- Rendering/output assertions (what gets printed); tests will only assert on control flow

---

### Dependencies to Add
`pytest` and `pytest-mock` are not yet in `pyproject.toml`. Add to the `dev` group:
```
poetry add --group dev pytest pytest-mock
```

Optionally add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

### New File: `tests/test_commands.py`

#### Fixture
```python
@pytest.fixture
def ctx():
    return CommandContext(
        conversation=MagicMock(),
        console=MagicMock(),
        signal={},
    )
```

#### Test Cases

**`dispatch()` — routing logic**

| Test | Input | Assert |
|---|---|---|
| non-slash input | `"hello"` | returns `False`, no handler called |
| known command | `"/exit"` | returns `True`, `signal["exit"]` set |
| unknown command | `"/foo"` | returns `True`, `console.print` called with error |
| command with trailing args | `"/exit now"` | returns `True`, dispatches correctly |

**`cmd_exit`** — sets `ctx.signal["exit"] = True`

**`cmd_home`** — sets `ctx.signal["home"] = True`

**`cmd_new`** (patch `yara.cli.commands.render_assistant`)
- Calls `ctx.conversation.reset()`
- Calls `render_assistant` with result of `ctx.conversation.first_assistant_prompt()`

**`cmd_help`**
- Calls `ctx.console.print` at least once

**`cmd_refresh` — no project**
- `ctx.project = None` → prints warning, does NOT call `ingest_files_to_db`

**`cmd_refresh` — with project** (patch `yara.services.ingest.ingest_files_to_db`)
- `ctx.project = {"id": 1, "ingestion_path": "/tmp/docs"}` → calls `ingest_files_to_db("/tmp/docs", 1)`

> Note: `ingest_files_to_db` is imported lazily inside `cmd_refresh`, so the patch target is `yara.services.ingest.ingest_files_to_db`.

---

### Verification
```bash
poetry run pytest tests/test_commands.py -v
```
All tests pass with no real DB, terminal, or OpenAI calls.
