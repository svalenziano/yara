# Streaming LLM Response Plan

## Context

Currently all LLM responses are fetched in one blocking call (`simple_llm_call`), and the full text is rendered after the entire response arrives. The goal is to stream tokens to the terminal as they arrive, giving the user immediate feedback instead of staring at a blank screen.

The key constraint: streaming logic (printing/rendering) belongs in the UI layer (`chat_ui.py`), not the service layer (`openai_client.py`). The service layer should yield raw text chunks.

## Files to Modify

1. `src/yara/services/openai_client.py` — make `streamed_llm_call` a generator
2. `src/yara/services/handlers.py` — add streaming-aware handler utility
3. `src/yara/cli/chat_ui.py` — add `stream_assistant()` and wire it up

## Implementation

### 1. `openai_client.py` — `streamed_llm_call` becomes a generator

Change `streamed_llm_call` to yield text deltas instead of returning a complete string:

```python
from collections.abc import Generator

def streamed_llm_call(
    conversation: Conversation, model=MODELS["normal"]
) -> Generator[str, None, None]:
    stream = client.responses.create(
        model=model,
        input=conversation.get_entries(),
        temperature=0,
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta":
            yield event.delta
```

- Return type changes from `str` to `Generator[str, None, None]`
- No printing, no accumulation — the caller handles that

### 2. `handlers.py` — add `_get_streamed_response_and_update_convo`

Add a new utility alongside `_get_llm_response_and_update_convo`:

```python
from collections.abc import Generator

from yara.services.openai_client import enrich_query, simple_llm_call, streamed_llm_call

def _get_streamed_response_and_update_convo(conversation: Conversation) -> Generator[str, None, None]:
    full_text = ""
    for chunk in streamed_llm_call(conversation):
        full_text += chunk
        yield chunk
    conversation.add_entry("assistant", full_text)
```

This preserves the existing pattern (update conversation after the response is complete) while passing chunks through to the caller.

Then update `rag_request` to use it. Important: use `yield from` (not `return`) since the utility is a generator:

```python
def rag_request(conversation: Conversation) -> Generator[str, None, None]:
    # ... existing enrichment/chunking logic stays the same ...
    yield from _get_streamed_response_and_update_convo(conversation)
```

The last line changes from `return _get_llm_response_and_update_convo(conversation)` to `yield from _get_streamed_response_and_update_convo(conversation)`. Return type changes from `str` to `Generator[str, None, None]`.

Leave the other handlers (`simple_request`, `new_topic`, `ask_about_new_topic`) unchanged for now since `not_a_router` only returns `rag_request`. Add a TODO docstring note to each unmodified handler that uses `_get_llm_response_and_update_convo`:

- `simple_request` — add `TODO - handle responses as streams like _get_streamed_response_and_update_convo`
- `new_topic` — add `TODO - handle responses as streams like _get_streamed_response_and_update_convo`
- `ask_about_new_topic` — no change (returns static string, no LLM call)

### 3. `chat_ui.py` — add `stream_assistant()` using Rich `Live`

```python
from rich.live import Live

def stream_assistant(chunks):
    full_text = ""
    console.print()
    with Live(
        Panel(Markdown(""), title="Assistant", border_style="bright_black"),
        console=console,
        refresh_per_second=12,
    ) as live:
        for chunk in chunks:
            full_text += chunk
            live.update(
                Panel(Markdown(full_text), title="Assistant", border_style="bright_black")
            )
    console.print()
    return full_text
```

Then update the chat loop (lines 57-60). Replace:

```python
llm_response = handler(conversation)
span.set_attribute("output.value", llm_response)

render_assistant(llm_response)
```

With:

```python
llm_response_stream = handler(conversation)
llm_response = stream_assistant(llm_response_stream)
span.set_attribute("output.value", llm_response)
```

- `render_assistant(llm_response)` on line 60 is removed — `stream_assistant` handles rendering
- `stream_assistant` returns the full accumulated text so the span attribute still works
- The existing `render_assistant` function should be kept (it's still used for the greeting on line 36 and goodbye messages)

## Verification

1. `docker compose up -d` to ensure DB is running
2. Run the CLI: `python -m yara.cli.chat_ui`
3. Ask a question — tokens should appear progressively inside the Rich panel
4. Verify the conversation history still works (ask a follow-up question that depends on context)
5. Verify the tracing span still captures the full `output.value`
