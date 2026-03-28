# CLAUDE.md

See [README.md](./README.md) for project overview, architecture, and database schema.

## Key Constraints
- **Learning project** — avoid frameworks that abstract away RAG/LLM concepts; prefer raw implementations
- **No ORM** — use raw SQL with psycopg2
- **CLI decoupled from RAG logic** — so a future web UI could replace it

## Dev Setup
```bash
docker compose up -d          # start PostgreSQL + pgvector on port 8888
python -m yara.db.setup_db    # create tables
```
