# Plan: Add query to conversation before routing

## Context
Currently `query` is threaded as a separate parameter through `router()` and every handler.
The goal is to add the query to `conversation` in `chat_ui.py` before routing, so handlers
only need `conversation` — making the handler signature uniform and cleaner.

`rag_request` is already updated (uses `replace_last_entry` + extracts query from conversation).
This plan finishes the job for the remaining handlers and call sites.

## Changes

### 1. `src/yara/cli/chat_ui.py` (lines 52–54)
Add `conversation.add_entry('user', query)` before routing, then drop `query` from the
`router()` and `handler()` calls:

```python
logger.info("user: %s", query)
conversation.add_entry('user', query)          # NEW
handler = router(conversation)                 # was router(query, conversation)
llm_response = handler(conversation)           # was handler(query, conversation)
```

### 2. `src/yara/services/router.py`
- Change `router(query, conversation)` → `router(conversation)`
- Extract query internally with `conversation.get_last_user_query()` for the
  `classify_request` call (which still needs the raw string)

```python
def router(conversation: Conversation) -> Callable:
    if len(conversation) <= 3:
        logger.info("routing to rag_request (conversation start)")
        return handlers.rag_request

    query = conversation.get_last_user_query()
    chosen = classify_request(query, conversation, ROUTES)
    logger.info("routing to %s", chosen.__name__)
    return chosen
```

### 3. `src/yara/services/handlers.py`

**`rag_request`** — already updated; swap `get_entries()[-1]['content']` for the new helper:
```python
query = conversation.get_last_user_query()   # cleaner than get_entries()[-1]['content']
```

**`simple_request`** — remove `query` param and the `add_entry` call (query already in convo):
```python
def simple_request(conversation: Conversation) -> str:
    return _get_llM_response_and_update_convo(conversation)
```

**`ask_about_new_topic`** — same pattern, drop `query` param and `add_entry("user", query)`:
```python
def ask_about_new_topic(conversation: Conversation) -> str:
    response = (
        "It sounds like you'd like to start a conversation"
        " about a new topic, is this correct?"
    )
    conversation.add_entry("assistant", response)
    return response
```

**`new_topic`** — must capture query *before* `reset()` wipes the conversation:
```python
def new_topic(conversation: Conversation) -> str:
    query = conversation.get_last_user_query()   # save before reset clears it
    summary = (
        "You just had a conversation about another topic,"
        " and the user is now asking about a new topic.  "
    )
    conversation.reset(
        developer_content=SYSTEM_PROMPT + summary,
        greeting="Ok, what's the next thing I can help you with?",
    )
    conversation.add_entry("user", query)
    return _get_llM_response_and_update_convo(conversation)
```

### 4. Side note: bug in `conversation.py` line 51
`self.entries[-1] = ...` is not indented inside the `if` block — it runs unconditionally
and the `raise` is unreachable. Fix:
```python
def replace_last_entry(self, role: Role, content: str):
    last_entry = self.entries[-1]
    if last_entry['role'] != role:
        raise ValueError(f"Role mismatch: old={last_entry['role']} & new={role}")
    self.entries[-1] = {'role': role, 'content': content}
```
(Also note: the original condition checked `content` too, which would always prevent a
replace since the content is different by design — only role should be validated.)

## Critical files
- `src/yara/cli/chat_ui.py`
- `src/yara/services/router.py`
- `src/yara/services/handlers.py`
- `src/yara/services/conversation.py` (bug fix)

## Verification
1. `docker compose up -d` + `python -m yara.db.setup_db` if DB isn't running
2. `python -m yara.main` — run a full chat session:
   - Ask a document question → should trigger `rag_request` (retrieval)
   - Ask a follow-up → should trigger `simple_request` (no retrieval)
   - Ask about a new topic → should trigger `ask_about_new_topic` / `new_topic`
3. `python -m yara.services.router` — runs `_test_router()` to verify classification
