# Code Review: `src/yara/services/ingest.py`

**Reviewer:** Claude Code
**Date:** 2026-03-29

---

## Summary

The ingestion pipeline reads files from disk, chunks them, generates OpenAI embeddings, and inserts everything into pgvector. The overall flow is clear and well-structured. Below are findings organized by severity.

---

## Critical

### 1. No token/size guard on the OpenAI embedding request (line 183)

`generate_embeddings(texts)` sends **all** chunk texts in a single API call. The OpenAI embeddings endpoint has a **300,000 token per-request limit** (noted in the TODO on line 153). A large directory could easily exceed this and produce a hard failure after all the file I/O work is already done.

**Recommendation:** Batch `texts` into groups that stay under the token limit (a rough heuristic: `sum(len(t) / 4 for t in batch) < 300_000`) and call `generate_embeddings` per batch.

### 2. `_bundle_files` generator yields results *then* raises after exhaustion (lines 101-124)

The generator yields `FileBundle`s as it goes, but collects `IOError`s and raises a combined error only after the generator is fully consumed. By that point, `_files_to_chunks` has already built a chunk list from the successful files, and `ingest_files_to_db` proceeds to embed and insert them before the error can surface. In practice, the raise on line 124 fires **after** the `for file in files` loop in `_files_to_chunks` exits normally, so the exception is never raised at all -- the error is silently swallowed.

**Recommendation:** Either fail fast on the first `IOError`, or collect errors and report them *after* the full pipeline completes (outside the generator), making it explicit that partial ingestion occurred.

---

## Bugs

### 3. `_get_all_filepaths` doesn't respect `limit` across subdirectories (lines 55-61)

The `break` on line 58 exits the inner `for filename in filenames` loop but not the outer `os.walk` loop. Walking continues into the next directory and keeps appending files past the limit.

**Fix:** Check `limit` in the outer loop as well, or use a `return` / early exit instead of `break`.

### 4. `_has_extension` matches suffixes, not true extensions (lines 34-41)

`filename.endswith("md")` will match `README.md` but also `a-file-named-cmd`. Using `filename.endswith(".md")` (with the dot) or `os.path.splitext` would be more correct.

### 5. `insert_chunks` default argument is evaluated at import time (pgvector.py:131-132)

```python
def insert_chunks(chunks, project_id=get_max_project_id() + 1):
```

`get_max_project_id() + 1` runs once when the module is first imported, not on each call. Every call to `insert_chunks` that omits `project_id` reuses the same stale value. This means multiple ingestion runs in the same process will all write to the same project_id.

**Fix:** Use `None` as the default and resolve inside the function body:
```python
def insert_chunks(chunks, project_id=None):
    if project_id is None:
        project_id = get_max_project_id() + 1
```

### 6. `get_similar` references a non-existent table (pgvector.py:103-114)

`get_similar` queries `book_chapter` with columns like `book_title` and `chapter_url`, but the schema only defines a `chunk` table. This function will raise a `ProgrammingError` at runtime.

---

## Design / Maintainability

### 7. Module-level globals control behavior (lines 25-28)

`MOCK`, `LIMIT`, `VERBOSE`, and `EXTENSIONS` are module-level globals, but `EXTENSIONS` is never actually passed to `_get_all_filepaths` -- the function uses its own default `["md", "txt"]` (line 46). This means the `EXTENSIONS` tuple on line 28 has no effect.

**Recommendation:** Thread `EXTENSIONS` through as a parameter, or have `_get_all_filepaths` reference the module constant instead of its own default.

### 8. `MOCK` path raises unconditionally (lines 180-181)

The `MOCK` flag exists but its branch just raises `Exception("Not implemented")`. If it's not ready, consider removing the flag entirely to reduce dead code.

### 9. `_chunk_text` uses naive fixed-size splitting (lines 70-77)

Splitting on a character count boundary will cut words and sentences in half, which can degrade embedding quality. This is fine for a v1, but a TODO or note acknowledging this tradeoff would help.

### 10. `test()` runs on every import of `pgvector.py` (pgvector.py:184)

```python
test()  # RUN A TEST WHENEVER THE MODULE IS LOADED
```

This means every `import yara.db.pgvector` hits the database and prints output. This will cause problems in tests, CI, or any context where the DB isn't running.

### 11. Stale/incomplete docstring block (lines 11-24)

The `ALGO` / `FUNCTIONS` comment block at the top appears to be leftover planning notes. Consider removing it or replacing it with a concise module docstring.

---

## Minor / Style

| Line | Issue |
|------|-------|
| 2 | `import random` is only used by `_mock_vector`, which is itself unused. Dead import. |
| 3 | `from pprint import pp` is unused. |
| 37 | Mutable default argument `extensions=['md', 'txt']`. Use a tuple or `None` sentinel. |
| 46 | Same mutable default issue: `extensions: list[str] = ["md", "txt"]`. |
| 62 | `"." not in d` to skip hidden dirs also skips valid dirs like `my.project`. Consider checking `d.startswith(".")`. |
| 67 | Typo: `# NOT IMPELMENTED` -> `# NOT IMPLEMENTED` |
| 150 | Trailing blank line with whitespace. |
| 199 | Hardcoded personal path in `__main__` block -- fine for local dev, just be aware it's in version control. |

---

## What's Working Well

- **Clean separation of concerns:** chunking, embedding, and DB insertion are distinct functions with clear responsibilities.
- **Generator-based file bundling** (`_bundle_files`) keeps memory usage low for large directories.
- **Dataclasses for `Chunk` and `FileBundle`** give the pipeline a clear, typed data contract.
- **The overall pipeline flow** in `ingest_files_to_db` is easy to follow: paths -> bundles -> chunks -> embeddings -> DB.
