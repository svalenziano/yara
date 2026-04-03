# Plan: Ingestion Logging

## Context

The ingestion pipeline currently uses `print()` calls gated behind a `verbose` flag. This gives no persistent record and no severity distinction. We want structured logging using Python's built-in `logging` module so that file-level events (purge, skip, insert) and DB write operations are observable at appropriate granularity.

## Approach

Add module-level loggers to `ingest.py` and `pgvector.py`. Replace `print()` calls with levelled log calls. Wire `verbose` to `DEBUG` vs `INFO` at the entry point.

### Log level conventions

| Level | Used for |
|-------|----------|
| `DEBUG` | Per-file detail — each purged/skipped filename, each batch |
| `INFO` | Summaries — total purged, skipped, inserted per run |
| `WARNING` | Unexpected but recoverable — e.g. IOError on a file |

### Step 1: Module loggers (both files)

Add at the top of each module (after imports, before constants):

```python
import logging
logger = logging.getLogger(__name__)
```

No `basicConfig` or handlers — modules should not configure the root logger. Add a `NullHandler` to suppress "no handler" warnings if the module is used as a library:

```python
logging.getLogger(__name__).addHandler(logging.NullHandler())
```

### Step 2: `ingest.py` — replace `print()` with log calls

**`purge_stale_files()`**
- `DEBUG` for each purged file: `"Purging %s/%s (reason: %s)", dir_path, filename, reason`
- `INFO` summary: `"Purge complete: %d stale, %d modified"` (always, not just when `to_purge` is non-empty — zero counts confirm the check ran)

**`_filter_already_ingested()`**
- `DEBUG` for each skipped file: `"Skipping already-ingested: %s/%s"`, dir_path, filename`
- `INFO` summary: `"Skip complete: %d unchanged, %d to ingest"`

**`ingest_files_to_db()`**
- `INFO`: `"Starting ingestion for %s — %d files found"` (after `_get_all_filepaths`)
- `DEBUG` per batch: `"Batch %d/%d — %d chunks"` 
- `INFO` per batch insert: `"Inserted %d chunks (batch %d/%d)"`
- `INFO` final: `"Ingestion complete: %d files, %d chunks inserted"`

**Drop the `verbose` flag** from these three functions — callers can set the log level instead. Keep the `verbose` parameter on `ingest_files_to_db()` signature for one release to avoid breaking callers, but ignore it internally (it controls nothing once logging is in place).

### Step 3: `pgvector.py` — log DB writes

**`delete_chunks_for_file()`**
- `DEBUG`: `"DELETE chunk WHERE dir_path=%s filename=%s → %d rows"`, dir_path, filename, rowcount`

**`insert_chunks()`**
- `DEBUG` per chunk inserted: too noisy — skip
- `INFO` after loop: `"INSERT chunk: %d rows (project_id=%d)"`, insert_count, project_id`

Keep existing `print()` calls in `nuke()` and `setup()` — those are interactive/setup operations, not pipeline logging.

### Step 4: Configure logging at entry points

**`src/yara/main.py`** (chat entry point — ingestion not called here, but good hygiene):

```python
logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
```

**`src/yara/services/ingest.py` `__main__` block** (standalone ingestion run):

```python
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")
    ...
```

### Files to modify

- `src/yara/services/ingest.py` — add logger, replace prints, configure in `__main__`
- `src/yara/db/pgvector.py` — add logger, log in `delete_chunks_for_file` and `insert_chunks`
- `src/yara/main.py` — add `basicConfig`

## Verification

1. Run ingestion standalone (`python -m yara.services.ingest`) — confirm DEBUG output shows per-file events and DB write counts
2. Re-run on same directory — confirm INFO shows "0 purged, N skipped, 0 inserted"
3. Delete a file, re-run — confirm DEBUG logs the filename and reason "stale", INFO shows summary
4. Set `LOG_LEVEL=INFO` (or change `basicConfig` level) — confirm per-file DEBUG lines disappear but summaries remain
