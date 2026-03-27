# yara: Yet Another RAG App

## Overview

`yara` is an assistant that helps answer questions about documents that you upload to it.

### Limitations

Currently supported docs:

1. Start with text only (markdown, txt, etc.)
2. Add PDF support if there's time

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
        c--"for now, docs will be replaced entirely with the new docs"-->a
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

## Architecture

Avoid:

- The CLI should not be coupled with the underlying RAG functionality. Why? In the future I might want to add a Web UI instead of / in addition to the CLI.

Layers of the cake (tentative architecture):

```
CLI
/////////////////////////////////
Business logic
/////////////////////////////////
Database / API Adapters
```

### v1

App logic:

- App: Main app logic
  - Dat Ingestion
  - Data Querying
- OpenAI: Makes API calls to OpenAI
- Config: loads environment vars

User interface:

- CLI: Invokes the application.  Orchestrates the CLI user experience

### v0

```mermaid
    classDiagram

    class RAG

    class CLI

    class OpenAI

    class Config

```

### Database ERD

```mermaid
    erDiagram
        CHUNKS {
            bigint id PK
            string filename "Just the filename and extension"
            string filepath "Just the system filepath, no filename or extension"
            string chunk_text "Raw chunk text, prior to embedding"
            vector embedding "pgvector embedding"
        }


```

### File storage

No file storage.  User gives Python a filepath that points to a file or folder.

Python will use that filepath to ingest the files into the DB, but it won't do anything with the original files, since the DB will contain everything we need to know about them.

More info: see [brianstorm](./docs/file-storage-brainstorm.md)

## Database Setup

See [Docker setup](./docs/pgvector_docker_setup.md)

poetry add openai, python-dotenv, tiktoken, psycopg2-binary, langchain-experimental, docling

poetry add openai python-dotenv tiktoken psycopg2-binary langchain-experimental docling
