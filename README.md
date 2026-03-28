# yara: Yet Another RAG App

## Overview

`yara` is an assistant that helps answer questions about documents that you feed it.

`yara` aims to be fast and simple. 

### Limitations

Currently supported docs:
1. Start with text only (markdown, txt, etc.)
2. Add PDF support if there's time

## Get started
See "Installation" below, activate the virtual environment, and then do:
```
python -m yara.main
```

## MVP Todo
- [ ] Is the app running?
- [ ] DB:
	- [x] just a Chunks table for now
- [ ] Backend (no fancy CLI)
	- [ ] Ingestion of multiple files into database WITHOUT embedding
		- [ ] For each ingestion, create a new project number and use that project number for every doc. (This is an alternative to destroying all chunks, in case I want to re-examine old chunks)
	- [ ] Keyword querying of files in the DB (non-semantic, uses SQL queries)
	- [ ] Add embedding onto ingestion
	- [ ] Add semantic search of the DB
- [ ] Interactive CLI
	- [ ] Initiate ingestion: 

## Behaviors
Here's the flow:

```mermaid
    flowchart LR
        a(Upload your docs)
        b(Ingestion pipeline)
        c(LLM querying: ask the helpful assistant about your docs!)

        a-->b
        b-->c
        c--"repeat as desired"-->c
        c-->a
```

Here's some detail of the ingestion pipeline:

```mermaid
    flowchart LR
        a(chunk documents and create embeddings)
        b(clear existing vectors from DB)
        c("add the new vectors (and associated metadata) to the DB")
        d(ready for querying!)
        a-->b
        b-->c
        c-->d
```

## Learning Goals

This app is a learning project.  I will avoid the use of frameworks that abstract away important RAG concepts and LLM interactions that I wish to learn.

Learning objectives:
1. How to build a RAG app
2. Building an interactive CLI
3. Modular project architecture (without over-engineering)
4. Advanced LLM methods like structured outputs, tool use, query classification

## Architecture

Avoid:
- The CLI should not be coupled with the underlying RAG functionality. Why? In the future I might want to add a Web UI instead of / in addition to the CLI.

### Layers of the cake (tentative architecture):
App logic:
- App: Main app logic
	- Data Ingestion
	- Data Querying
- OpenAI adapters - make calls to OpenAI
	- LLM
	- Embedding
- DB
	- pgvector - i/o with Postgres pgvector DB
- Config: loads environment vars

User interface:
- CLI: Invokes the application.  Orchestrates the CLI user experience

### Module Design (stub)

```mermaid
    classDiagram

    class RAG

    class CLI

    class OpenAI

    class Config

```

### Database ERD
Items marked as Future are NOT part of the MVP

```mermaid
    erDiagram
        chunk {
            SERIAL id PK
            bigint doc_id FK "Future"
            bigint project_id FK  "Future foreign key"
            varchar(500) filename "Just the filename and extension"
            varchar(500) dir_path "Just the filepath, no filename or extension"
            text chunk_text "Raw chunk text, prior to embedding"
            vector embedding "pgvector embedding"
            integer chunk_number "e.g. chunk 5 of x chunks"
            integer total_chunks "e.g. this file was split into 10 chunks"
            integer filesize "Filesize in bytes. For future file comparison / cache invalidation."
            JSONB metadata "Future: misc. metadata that may vary per doc"
        }
        
        doc {
	        bigint id PK "Future"
        }
        
        project {
	        bigint id PK "Future"
        }
```


### File storage
No file storage.  User gives Python a filepath that points to a file or folder.

Python will use that filepath to ingest the files into the DB, but it won't do anything with the original files, since the DB will contain everything we need to know about them.

More info: see [brianstorm](./docs/file-storage-brainstorm.md)

## Installation
Start Postgres:
```bash
docker compose up -d
```

Verify that the DB was created and that you can connect to it:
```bash
docker compose exec db psql -U postgres -l
# or
psql -h localhost -p 8888 -U postgres
```

Setup tables in the database:
```bash
python -m yara.db.setup_db
```

If changes are made to the schema, you should do:
```
docker compose down -v  # removes volumes

# Also, re-do the setup steps listed above!
```


More info, see [Docker setup](./docs/pgvector_docker_setup.md)