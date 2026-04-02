# Logging Plan

## Goal

Add structured, file-based logging using Python's built-in `logging` module to capture: user inputs, routing decisions, retrieved chunks, and LLM responses.

## Architecture

The standard Python pattern is `logging.getLogger(__name__)` in each module. This creates a hierarchy (`yara.cli.chat_ui`, `yara.services.handlers`, etc.) and allows per-module verbosity tuning later.

All loggers inherit from the root logger, so a single `basicConfig` call in `main.py` routes all output to `yara.log`.

## What gets logged where

| Module | Log level | What |
|--------|-----------|------|
| `chat_ui.py` | INFO | User input, final rendered response |
| `router.py` | INFO | Which handler was selected |
| `handlers.py` | DEBUG | RAG chunks injected into prompt |
| `handlers.py` | INFO | LLM response text |
| `conversation.py` | DEBUG | Replaces existing debug `print()` on lines 62-63 |

## Setup

Configure logging once in `main.py` before calling `chat_loop()`:

```python
import logging

logging.basicConfig(
    filename="yara.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

If `config.VERBOSE` is True, also add a `StreamHandler` to mirror logs to `stderr`.

## Files to modify

- `src/yara/main.py` — configure logging before `chat_loop()`
- `src/yara/cli/chat_ui.py` — add module logger; log user input + response
- `src/yara/services/handlers.py` — add module logger; log chunks + LLM response
- `src/yara/services/router.py` — add module logger; log routing decision
- `src/yara/services/conversation.py` — replace `print()` debug lines 62-63 with `logger.debug`

## Expected output (one turn)

```
2026-03-31 12:00:01 INFO  yara.cli.chat_ui:51 - user: what is the capital of france?
2026-03-31 12:00:01 INFO  yara.services.router:12 - routing to rag_request
2026-03-31 12:00:01 DEBUG yara.services.handlers:28 - retrieved chunks: ...
2026-03-31 12:00:02 INFO  yara.services.handlers:14 - llm response: Paris is ...
2026-03-31 12:00:02 INFO  yara.cli.chat_ui:53 - assistant: Paris is ...
```

## Verification

```bash
python -m yara.main   # run the chat loop, ask a question
tail -f yara.log      # watch log lines appear in real time
```
