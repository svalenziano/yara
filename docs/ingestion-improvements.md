# Plan: Smart Ingestion — Skip & Purge

## Context

Re-running ingestion on the same directory currently re-embeds every file, wasting OpenAI API calls and creating duplicate chunks. We want two improvements:
1. **Skip** files already in the DB with the same filesize
2. **Purge** chunks for files that no longer exist on the filesystem

Together these make the DB match the filesystem on each run.

## Approach

Use the existing `dir_path`, `filename`, and `filesize` columns in the `chunk` table. No schema changes needed.

### Step 0: Add DB functions in `pgvector.py`

**`get_ingested_files(dir_path)`** — returns set of `(dir_path, filename, filesize)` tuples for chunks whose `dir_path` starts with the given directory. Scoped query avoids scanning unrelated data.

```sql
SELECT DISTINCT dir_path, filename, filesize FROM chunk WHERE dir_path LIKE %s || '%%';
```

**`delete_chunks_for_file(dir_path, filename)`** — deletes all chunks matching a specific file. Uses `cursor.rowcount` for the count (no `RETURNING` needed).

```sql
DELETE FROM chunk WHERE dir_path = %s AND filename = %s;
```

### Step 1: Purge stale files — `purge_stale_files()` in `ingest.py`

Standalone function, callable and testable independently. Accepts `purge_modified: bool` and `verbose: bool` parameters.

- Call `get_ingested_files(directory_path)` internally to get current DB state
- For each, check if the file still exists on disk (`os.path.isfile`)
  - If not on disk → purge (stale)
  - If on disk but filesize differs and `purge_modified=True` → purge (will be re-ingested)
  - If on disk with same filesize → leave alone
- Call `delete_chunks_for_file()` for each file to purge
- Print summary when verbose

### Step 2: Filter unchanged files — `_filter_already_ingested()` in `ingest.py`

- For each filepath from `_get_all_filepaths()`, get its `dir_path`, `filename`, `filesize`
- Skip if `(dir_path, filename, filesize)` is in the ingested set
- Print skip count when verbose

### Step 3: Wire into `ingest_files_to_db()`

```python
paths = _get_all_filepaths(directory_path)
purge_stale_files(directory_path, purge_modified=True, verbose=verbose)
ingested = get_ingested_files(directory_path)          # fresh query after purge
paths = _filter_already_ingested(paths, ingested, verbose=verbose)
# ... existing batching/embedding/insert logic
```

Note: `get_ingested_files()` is called **after** the purge so the set reflects current DB state. No side effects — purge doesn't mutate any passed-in data.

### Files to modify

- `src/yara/db/pgvector.py` — add `get_ingested_files()`, `delete_chunks_for_file()`
- `src/yara/services/ingest.py` — add `purge_stale_files()`, `_filter_already_ingested()`, wire into `ingest_files_to_db()`

### Edge cases

- **File content changed but size didn't**: won't re-ingest (accepted trade-off)
- **File moved to new directory**: ingested as new (different `dir_path`), old path chunks purged
- **Empty DB**: ingested set is empty, purge is a no-op, all files ingested normally
- **Deleted subdirectory**: all nested files purged (they won't pass `os.path.isfile`)
- **project_id fragmentation**: re-ingested files get a new project_id — accepted for now

## Verification

1. Ingest a directory — all files processed
2. Re-run — all files skipped, nothing purged
3. Delete a file from disk, re-run — stale chunks purged, rest skipped
4. Modify a file (change size), re-run — old chunks purged, file re-ingested with fresh embeddings
