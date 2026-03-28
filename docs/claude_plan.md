# Ingestion Pipeline Implementation Plan

## Context
The RAG app needs a file ingestion pipeline to read files from a directory, generate embeddings, and store them in the `chunk` table. Currently `ingest.py` is just a planning doc and `pgvector.py` lacks the needed insert/query functions. Each file will be treated as a single chunk for now (`generate_chunks` is deferred).

## Files to Modify
- `src/yara/db/pgvector.py` — add `get_max_project_id()` and `add_chunk()`
- `src/yara/services/ingest.py` — add `get_files()`, `read_files()`, and `ingest_chunks()`

## Implementation

### 1. `pgvector.py` — `get_max_project_id() -> int`
- Query `SELECT MAX(project_id) AS max_id FROM chunk` using existing `get_dict()`
- Return `result[0]['max_id'] or 0` (handles empty table where MAX returns NULL)

### 2. `pgvector.py` — `add_chunk(...) -> None`
- Parameters: `project_id, filename, dir_path, chunk_text, embedding, chunk_number, total_chunks, filesize, metadata`
- Use `_database_connect()` context manager, parameterized INSERT with `%s::vector` for embedding
- Serialize `metadata` dict with `json.dumps()` (add `import json`)
- Follow existing cursor pattern from `setup()`

### 3. `ingest.py` — `get_files(directory, extension_filter=["txt", "md"], limit=50) -> list[str]`
- Use `os.walk()` to traverse directory
- Filter with `filename.endswith(f".{ext}")` — handles compound extensions like `.excalidraw.png`
- Collect full paths via `os.path.join(root, filename)`, stop at `limit`

### 4. `ingest.py` — `read_files(files: list[str]) -> Generator[tuple[str, str], None, None]`
- Generator yielding `(filepath, content)` tuples
- Read with `open(fp, 'r', encoding='utf-8').read()`
- Skip unreadable files with try/except (print warning, continue)

### 5. `ingest.py` — `ingest_chunks(directory) -> str`
- Get `project_id = pgvector.get_max_project_id() + 1`
- Call `get_files(directory)` then iterate `read_files(files)`
- For each file: derive `filename`, `dir_path`, `filesize` from path; generate embedding via `generate_embedding(content)`; call `pgvector.add_chunk(...)` with `chunk_number=1, total_chunks=1`
- Metadata: `{"source_path": filepath, "extension": ext}`
- Wrap per-file processing in try/except to skip failures
- Return summary string: `"Ingested {count}/{total} files as project_id {project_id}"`
- Imports: `os`, `yara.db.pgvector`, `yara.openai_embedding.generate_embedding`

## Implementation Order
1. `get_max_project_id()` + `add_chunk()` in pgvector.py (no dependencies)
2. `get_files()` + `read_files()` in ingest.py (no dependencies)
3. `ingest_chunks()` in ingest.py (wires everything together)

## Verification
- Start the PostgreSQL container (`docker compose up -d`)
- Run `python -c "from yara.db.pgvector import get_max_project_id; print(get_max_project_id())"` — should return 0
- Run `ingest_chunks()` against a small test directory with a few `.md`/`.txt` files
- Verify rows in DB: `SELECT project_id, filename, chunk_number FROM chunk;`

## Notes
- One DB connection per `add_chunk` call is fine for the 50-file limit
- Large files may exceed embedding token limit (8191 tokens) — the per-file try/except will catch API errors; proper chunking comes later with `generate_chunks()`