# yara (Yet Another RAG App)


## Overview
`yara` is an assistant that helps answer questions about documents that you feed it.

`yara` aims to be fast and simple. 

### Learning Goals
This app is a learning project.  I will avoid the use of frameworks that abstract away important RAG concepts and LLM interactions that I wish to learn.

Learning objectives:
1. How to build a RAG app
2. Building an interactive terminal UI
3. Modular project architecture (without over-engineering)
4. RAG methods like structured outputs, tool use, query classification

### Screenshots



### Limitations
Currently supported: text files (txt, md, json, etc.)

Future: PDF


## Getting started

Start Postgres & pgvector:
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
```bash
docker compose down -v  # removes volumes
# Also, re-do the setup steps listed above!
```

Activate the virtual environment and then start the app
```bash
eval $(poetry env activate)
python -m yara.main
```





## How it works
Here's the flow:

```mermaid
    flowchart LR
        a(1 - Upload your docs)
        b(2 - Data ingestion)
        c(3 - LLM querying: ask the helpful assistant about your docs!)

        a-->b
        b-->c
        c--"repeat as desired"-->c
        c-->a
```

Here's some detail of the ingestion pipeline:

```mermaid
    flowchart LR
        a(Chunk documents and create embeddings)
        b(Clear existing vectors from DB)
        c("Add the new vectors (and associated metadata) to the DB")
        d(Ready for querying!)
        a-->b
        b-->c
        c-->d
```


### A bit more detail
- **History** is augmented anytime responses are received from the User or the LLM.
- **Why is the routing step necessary?** There are scenarios where you don't want to retrieve data from the Vector DB, e.g. the user is asking a follow-up question about the data that was recently retrieved.  In this scenario, you wouldn't want the history/context being polluted with chunks that are unhelpful
```mermaid
flowchart

a(User Query)
b(Do Deterministic Stuff)
a--"slash command"-->b
b-->a

c(Routing. Small LLM Call.)
d(Augment history w/ retrieval from vector DB)
a-->c
c--"I Need additional stuff"-->d

e(Analyze Data & Respond to User. Large LLM Call.)
c--"I have what I need"-->e
d-->e
f(Print response)
e-->f
f-->a

```

### Routing / classification step
More detail on the 'Routing step' in the above diagram.  Routing logic is a placeholder at the moment.
```mermaid
flowchart
aa(User input)
aa-->a
a("`**Routing step**
LLM Classifies the request, 
App routes the request`")
a-->b(Q about content on a specific topic)-->c(RAG) --> z
a-->k(Q about a new topic) --> l(Re-write/compress history) --> c --> z
a-->m(Follow-up Q on retrieved content)-->z
a-->i(User is asking for an overview of the files in the system)-->j('fd' or Tree)
a-->d(Ingestion, aka User wants to add more content)-->e(Ingestion pipeline)
a-->f(User is done)-->Exit
a-->g(Something else)-->h(Oops, can't do that.  Here are your options.)-->aa
z(LLM 'Explainer' Call)
```



## Architecture

Avoid:
- The CLI should not be coupled with the underlying RAG functionality. Why? In the future I might want to add a Web UI instead of / in addition to the CLI.


### Database ERD
```mermaid
    erDiagram
        chunk {
            SERIAL id PK "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
            bigint project_id FK "Indexed. Each chunk has one project_id"
            varchar(500) filename "Just the filename and extension"
            varchar(500) dir_path "Just the filepath, no filename or extension"
            text chunk_text "Raw chunk text, prior to embedding"
            vector embedding "pgvector embedding"
            integer chunk_number "e.g. chunk 5 of x chunks"
            integer total_chunks "DENORMALIZED e.g. this file was split into 10 chunks"
            integer filesize "Filesize in bytes. For file comparison / cache invalidation."
            timestampz created "DEFAULT CURRENT_TIMESTAMP, not currently used"
            timestampz modified "DEFAULT NULL, not currently used"
            JSONB metadata "Future: misc. metadata that may vary per doc"
        }
        
        project {
	        SERIAL id PK "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
            varchar(100) name "NOT NULL"
            varchar(500) ingestion_path "Files are ingested from this base path."
            timestampz last_ingested "Updated at the end of each ingestion / refresh"
        }
        
        project ||--o{ chunk : "has"
```


### File storage
No file storage.  User gives Python a filepath that points to a file or folder.

Python will use that filepath to ingest the files into the DB, but it won't do anything with the original files, since the DB will contain everything we need to know about them.



## Run tests
```
poetry run pytest -v
```

## Docker setup details
More info, see [Docker setup](./docs/pgvector_docker_setup.md)