# Code Review: `src/yara/services/`

**Reviewer:** Claude Code
**Date:** 2026-03-31

---

## `conversation.py`

**Bug — `get_last_user_query` crashes if no user entries exist**
```python
return [x['content'] for x in self.entries if x['role'] == 'user'][-1] or ""
```
The `or ""` fallback never fires — `[-1]` on an empty list raises `IndexError` before it can. The `new_topic` handler calls this before `reset()`, so it's safe in practice, but the method's contract is fragile. Either guard against it or document the precondition.

**Minor — debug log scaffolding**
Line 73 — `"augmented entries is a copy: ..."` is a one-time sanity check that should be removed now that it's confirmed.

**Minor — `get_entries()` leaks the internal list**
The return type `Sequence[Entry]` implies read-only, but it returns `self.entries` directly. The warning comment is easy to miss. Low risk for now but worth keeping in mind as the codebase grows.

---

## `handlers.py`

**Style — inconsistent function name casing**
`_get_llM_response_and_update_convo` — the `llM` mid-word caps is a typo-style quirk. `_get_llm_response_and_update_convo` would be consistent with Python conventions.

**Minor — indented f-string sends leading whitespace to the LLM** (`rag_request`, lines 33–47)
Every line of the prompt has leading spaces due to the indentation. The LLM handles it fine in practice, but `textwrap.dedent()` would clean it up.

**Possible bug — `ask_about_new_topic` is not in `ROUTES`**
`router.py` lists `[rag_request, simple_request, new_topic]`. `ask_about_new_topic` is a handler with a docstring written for the router to select, but the router can never choose it. Is this intentional (manually wired later) or an omission?

---

## `router.py`

**Bug — two unused imports**
```python
from pydantic import BaseModel  # never used
from rich import print           # overrides builtin print, also never called
```
`BaseModel` was likely left over from an earlier iteration. `rich.print` shadowing the builtin is a silent footgun.

**Minor — `_test_router` doesn't add the query to the conversation**
The live path adds `query` to `conversation` before calling `router`. The test bypasses that, passing `query` directly to `classify_request` with a conversation that doesn't contain it. The test still runs, but it no longer mirrors real call conditions.

**Style — missing blank line before `_test_router`** (PEP 8: two blank lines between top-level definitions)

---

## `openai_client.py`

**Bug — mutable default argument**
```python
def generate_embeddings(text: list[str], metadata: list[dict] = []):
```
Classic Python gotcha — the default list is shared across all calls. Use `metadata: list[dict] | None = None` and set `if metadata is None: metadata = []` inside the body.

**Dead code — `enrich_query` is never called**
It's a well-written function and probably intended for future use (`rag_request` could use it to improve retrieval quality), but right now it's unreachable.

**Minor — query appears twice in the routing prompt**
`classify_request` injects `User's latest message: {query}` into the prompt, and after the recent refactor, `query` is also the last entry in `conversation` (which becomes `augmented`). The LLM sees it twice. Not a correctness issue, but slightly wasteful.

---

## `ingest.py`

**Bug — mutable default arguments**
Both `_has_extension` (line 37) and `_get_all_filepaths` (line 46) use `["md", "txt"]` as a default. Use tuples: `extensions=("md", "txt")`.

**Bug — `dirnames` filter is too broad** (line 69)
```python
dirnames[:] = [d for d in dirnames if "." not in d]
```
This skips any directory with a dot anywhere in the name (e.g., `my.project`). Intent is clearly to skip hidden dirs — should be `not d.startswith(".")`.

**Minor — `_get_file_metadata` returns misleading placeholder**
It returns `{"data": "this feature not yet implemented"}` which gets stored in the DB. Should return `{}` until implemented.

**Minor — `MOCK = False` with dead `if MOCK:` branch**
`ingest_files_to_db` has `if MOCK: raise Exception("Not implemented")` that can never be reached since `MOCK` is a hardcoded `False`. Remove the branch or leave `MOCK` out entirely until you need it.

**Minor — `_bundle_files` swallows individual tracebacks**
`raise IOError(errors)` wraps a list of exceptions, losing the individual stack traces. At minimum, `raise errors[0]` would give a usable traceback.

---

## `get_chunks.py`

Nothing significant. One style note: `query_similar_chunks_pretty` builds its string with `+=` in a loop — `"\n".join(...)` or a list comprehension would be more idiomatic, but it's a cosmetic issue at these data sizes.

---

## Summary by priority

| Priority | Issue | File |
|---|---|---|
| Bug | `get_last_user_query` IndexError on empty | `conversation.py` |
| Bug | Mutable default `metadata=[]` | `openai_client.py` |
| Bug | Mutable defaults `extensions=["md","txt"]` | `ingest.py` |
| Bug | Dot-dir filter too broad | `ingest.py` |
| Missing | `ask_about_new_topic` not in `ROUTES` | `router.py` |
| Cleanup | Unused imports (`BaseModel`, `rich.print`) | `router.py` |
| Cleanup | Dead `enrich_query` | `openai_client.py` |
| Cleanup | Dead `MOCK` branch | `ingest.py` |
| Cleanup | Misleading `_get_file_metadata` return | `ingest.py` |
| Style | `_get_llM_response` casing | `handlers.py` |