# yara: Yet Another RAG App

## Overview
`yara` is an assistant that helps answer questions about documents that you upload to it.

Currently supported docs:
1. Start with text only (markdown, txt, etc.)
2. Add PDF support if there's time

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
Here's some detail of the ingestion pipeline
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

## Database ERD
```mermaid
    erDiagram
        CHUNKS {
            bigint id PK
            string filename
            string filepath
            string chunk_text
            vector embedding

        }


```

### Learning?!
This app is a learning project.

Learning objectives:
1. How to build a RAG app
2. Building an interactive CLI
3. Modular project architecture (without over-engineering)

## Architecture
The CLI should not be coupled with the underlying RAG functionality.

In the future I might want to add a Web UI instead of / in addition to the CLI.

Layers of the cake (tentative architecture):

CLI
/////////////////////////////////
Business logic
/////////////////////////////////
Database / API Adapters

## Database Setup
See [Docker setup](./docs/pgvector_docker_setup.md)


poetry add openai, python-dotenv, tiktoken, psycopg2-binary, langchain-experimental, docling

poetry add openai python-dotenv tiktoken psycopg2-binary langchain-experimental docling 