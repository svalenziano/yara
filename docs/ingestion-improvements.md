# Plan: Smart Ingestion — Skip & Purge

## Context

Re-running ingestion on the same directory currently re-embeds every file, wasting OpenAI API calls and creating duplicate chunks. We want two improvements:
1. **Skip** files already in the DB with the same filesize
2. **Purge** chunks for files that no longer exist on the filesystem

Together these make the DB match the filesystem on each run.

## Approach

Use the existing `dir_path`, `filename`, and `filesize` columns in the `chunk` table. No schema changes needed.

### Step 0: Add DB functions in `pgvector.py`

**`get_ingested_files()`** — returns set of `(dir_path, filename, filesize)` tuples for all chunks in the DB. Used by both skip and purge logic.

```sql
SELECT DISTINCT dir_path, filename, filesize FROM chunk;
```

**`delete_chunks_for_file(dir_path, filename)`** — deletes all chunks matching a specific file. Returns count of deleted rows.

```sql
DELETE FROM chunk WHERE dir_path = %s AND filename = %s RETURNING id;
```

### Step 1: Purge stale files — `purge_stale_files()` in `ingest.py`

Standalone function, callable and testable independently.

- Get `ingested_files` set from DB (via `get_ingested_files()`)
- Filter to files whose `dir_path` starts with the ingestion directory
- For each, check if the file still exists on disk (`os.path.isfile`)
- If not, call `delete_chunks_for_file()` to remove its chunks
- Print summary when verbose

### Step 2: Filter unchanged files — `_filter_already_ingested()` in `ingest.py`

- For each filepath from `_get_all_filepaths()`, get its `dir_path`, `filename`, `filesize`
- Skip if `(dir_path, filename, filesize)` is in the ingested set
- Print skip count when verbose

### Step 3: Wire into `ingest_files_to_db()`

```python
paths = _get_all_filepaths(directory_path)
ingested = get_ingested_files()
purge_stale_files(directory_path, ingested, verbose)   # step 1: purge first
paths = _filter_already_ingested(paths, ingested)      # step 2: skip unchanged
# ... existing batching/embedding/insert logic
```

### Files to modify

- `src/yara/db/pgvector.py` — add `get_ingested_files()`, `delete_chunks_for_file()`
- `src/yara/services/ingest.py` — add `purge_stale_files()`, `_filter_already_ingested()`, wire into `ingest_files_to_db()`

### Edge cases

- **File content changed but size didn't**: won't re-ingest (accepted trade-off)
- **File moved to new directory**: ingested as new (different `dir_path`), old path chunks purged
- **Empty DB**: ingested set is empty, purge is a no-op, all files ingested normally
- **Deleted subdirectory**: all nested files purged (they won't pass `os.path.isfile`)

## Verification

1. Ingest a directory — all files processed
2. Re-run — all files skipped, nothing purged
3. Delete a file from disk, re-run — stale chunks purged, rest skipped
4. Modify a file (change size), re-run — old chunks remain but new chunks added (note: does NOT delete old chunks for changed files — we could add this if desired)
