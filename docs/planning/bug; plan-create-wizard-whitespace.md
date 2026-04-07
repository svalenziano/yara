# Plan: Fix `/create` Wizard Blank-Line Flood

## Context

When a user runs `/create` and types in the wizard, `prompt_toolkit.prompt()` re-renders on every keystroke. Its render cycle issues an `erase_down` escape sequence (clears cursor to end of screen) to manage space for its completion menu and multi-line input. Because the wizard runs after `console.clear()`, the prompt starts near the top of the terminal, and every keystroke causes `erase_down` to flood the remaining ~40+ lines with blank space, visually pushing the prompt off screen.

The startup `❯` prompt doesn't exhibit this because `render_home()` fills most of the screen, leaving only a few lines below the prompt for `erase_down` to clear.

## Root Cause

`prompt_toolkit.prompt()` is overkill for the wizard — it provides history, completion, and multi-line support that the wizard doesn't use, but its rendering cycle has side effects in this mixed Rich+prompt_toolkit context.

## Fix

Replace `prompt_toolkit.prompt(HTML(...))` with `console.input(...)` in `project_wizard()`. Rich's `Console.input()` wraps Python's built-in `input()` with markup support, has no erase-down rendering, and is already the idiomatic tool in this codebase.

**File:** `src/yara/cli/startup_ui.py`

**In `project_wizard()`**, replace each `prompt(HTML("<ansiblue>...: </ansiblue>"))` call with `console.input("[blue]...: [/blue]")`:

```python
# Step 1
name = console.input("[blue]Project name (≤ 40 chars): [/blue]").strip()

# Step 2
description = console.input("[blue]Description (optional): [/blue]").strip() or None

# Step 3 (loop)
path = console.input("[blue]Ingestion path: [/blue]").strip()
```

The `try/except (KeyboardInterrupt, EOFError)` blocks remain unchanged — `console.input()` raises the same exceptions.

Remove the now-unused `from prompt_toolkit import prompt` and `from prompt_toolkit.formatted_text import HTML` imports if no other functions in the file use them.

> **Note:** `edit_wizard()`, `delete_confirm()`, and `_pick_project()` also use `prompt(HTML(...))`. They are less likely to exhibit this issue (called after render_home fills the screen), but should be converted for consistency.

## Files to Modify

- `src/yara/cli/startup_ui.py` — `project_wizard()` (lines 91–131), plus imports

## Verification

1. Run `/create` — type characters in the project name field; screen should remain stable with no blank-line flood.
2. Tab/arrow keys won't trigger autocomplete (expected — wizard never had it).
3. Ctrl-C at any step should still raise `WizardCancelled` and return to the startup loop.
4. Completing the wizard should ingest files and open chat normally.
