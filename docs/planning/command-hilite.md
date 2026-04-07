# Slash-Command Support with Real-Time Highlighting

## Context

The chat loop in `chat_ui.py` has a hardcoded `/exit` check and no extensible command system. We want to:
- Support slash commands (`/help`, `/new`, `/exit`) with a registry pattern
- Highlight the `/command` portion in blue+bold as the user types, using prompt_toolkit's `Lexer` API
- Make it easy to add new commands without touching `chat_ui.py`

## Files to Modify

| File | Action |
|------|--------|
| `src/yara/cli/commands.py` | **Create** — command registry, lexer, built-in commands |
| `src/yara/cli/chat_ui.py` | **Modify** — wire in lexer + dispatch |

## Step 1: Create `src/yara/cli/commands.py`

### CommandContext dataclass
```python
@dataclass
class CommandContext:
    conversation: Conversation
    console: Console
    signal: dict = field(default_factory=dict)  # e.g. signal["exit"] = True
```

### Registry + decorator
```python
COMMANDS: dict[str, Callable[[CommandContext], None]] = {}

def register_command(name: str):
    def decorator(fn):
        COMMANDS[name] = fn
        return fn
    return decorator
```

### dispatch()
- If input starts with `/`, parse the command name, look it up in `COMMANDS`, call handler
- Return `True` if input was a command (even unknown), `False` otherwise
- Unknown commands print an error via `ctx.console`

### Built-in commands
- `@register_command("exit")` — sets `ctx.signal["exit"] = True`
- `@register_command("help")` — prints sorted list of registered commands via `ctx.console`
- `@register_command("new")` — calls `ctx.conversation.reset()` (no args needed, defaults exist), then renders the greeting via `render_assistant()`
  - **Note**: `Conversation.reset()` accepts optional `developer_content` and `greeting` params but has sensible defaults (`SYSTEM_PROMPT`, `DEFAULT_GREETING`)
  - Use lazy import of `render_assistant` to avoid circular import

### SlashCommandLexer
```python
class SlashCommandLexer(Lexer):
    def lex_document(self, document):
        def get_line(lineno):
            line = document.lines[lineno]
            # if starts with /, split into [("class:slash-command", "/word"), ("", rest)]
            # otherwise return [("", line)]
        return get_line
```

Highlights **all** `/word` patterns (not just known commands). Invalid commands get a friendly error at dispatch time instead.

### Style
```python
SLASH_COMMAND_STYLE = Style.from_dict({"slash-command": "bold ansiblue"})
```

## Step 2: Modify `src/yara/cli/chat_ui.py`

### a) Add imports
```python
from yara.cli.commands import CommandContext, SlashCommandLexer, SLASH_COMMAND_STYLE, dispatch
```

### b) Update `get_user_input()` — add `lexer` and `style` params
```python
def get_user_input(history):
    return prompt(
        HTML("<ansiblue>❯ </ansiblue>"),
        history=history,
        cursor=CursorShape.BLINKING_BLOCK,
        lexer=SlashCommandLexer(),
        style=SLASH_COMMAND_STYLE,
    )
```

### c) Refactor `chat_loop()`
- Create `CommandContext` once before the loop
- Remove hardcoded `/exit` check (lines 105-107)
- After empty-input check, call `dispatch(query, ctx)`:
  - If `True` and `ctx.signal.get("exit")`: render goodbye + break
  - If `True`: continue (command was handled)
  - If `False`: fall through to existing RAG logic (unchanged)

## Verification

1. Run the app: `python -m yara.main`
2. Type `/help` — should print available commands
3. Type `/new` — conversation resets, greeting re-rendered
4. Type `/exit` — goodbye message, app exits
5. Type `/unknown` — error message with hint to use `/help`
6. Type `/help but with extra text` — `/help` still highlights blue as you type
7. Type a normal message — no highlighting, goes through RAG as before
