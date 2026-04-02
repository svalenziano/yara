from contextlib import contextmanager
from typing import cast

import psycopg2
from psycopg2.extras import Json, RealDictCursor, RealDictRow

from yara.config import env
from yara.types import Chunk, SimilarChunk


@contextmanager
def _database_connect():
    """
    Commits on successful exit.

    psycopg2 autocommit is off by default:
    changes will be rolled back in the event of an error.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=env["PG_DB_NAME"],
            host=env["PG_HOST"],
            port=env["PG_PORT"],
            user=env["PG_USER"],
            password=env["PG_PASSWORD"] or None,
        )
        yield connection
        connection.commit()
    except Exception as e:
        print("📦 Database error: ", e)
        if connection:
            connection.rollback()  # explicit rollback: fine but not necessary?
        raise
    finally:
        if connection:
            connection.close()


def nuke():
    prompt = "Are you sure you wish to nuke and reset the DB? (y/n)?"

    if input(prompt).lower() != "y":
        print("Aborting")
        return
    print("Nuking the DB...")

    with _database_connect() as conn:
        cur = conn.cursor()
        try:
            for table in [
                "chunk",
            ]:
                cur.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ DROP TABLE {table}")

        except Exception as e:
            print("Error durring database setup")
            raise (e)
        finally:
            cur.close()


def setup():
    print("Executing DB setup...")
    with _database_connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunk (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    project_id BIGINT NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    dir_path VARCHAR(500) NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding VECTOR({env["VECTOR_DIMS"]}) NOT NULL,
                    chunk_number INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    filesize INTEGER NOT NULL,
                    metadata JSONB DEFAULT '{{}}'::jsonb,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified TIMESTAMP DEFAULT NULL
                );
            """,
            )
            print("✅ Database Setup complete\n")

        except Exception as e:
            print("Error durring database setup")
            raise (e)
        finally:
            cur.close()


def get_dict(query, params=()) -> list[RealDictRow]:
    with _database_connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def get_chunk_count() -> int:
    query = """
        SELECT count(id) FROM chunk;
    """
    return get_dict(query)[0]["count"] or 0


def get_similar_chunks(embedding, top_k: int) -> list[SimilarChunk]:
    """
    Args:
        embedding: the embedding you wish to find similar chunks to
        top_k: how many records to return?
    """
    query = """
        SELECT 
            id, project_id, filename, dir_path, chunk_text, 
            1 - (embedding <=> %s::vector) AS cosine_similarity
        FROM chunk
        ORDER BY cosine_similarity DESC
        LIMIT %s;
    """
    return [cast(SimilarChunk, dict(d)) for d in get_dict(query, (embedding, top_k))]


def get_max_project_id() -> int:
    query = """
        SELECT max(project_id) FROM chunk;
    """
    return get_dict(query)[0]["max"] or 0


def _nuke_chunks():
    result = get_dict("""
        DELETE FROM chunk RETURNING project_id;
    """)
    delete_count = len(result)
    print(f"📦 Deleted all {delete_count} from the table.")


def get_ingested_files(dir_path: str) -> set[tuple[str, str, int]]:
    """
    Returns set of (dir_path, filename, filesize) for all chunks whose
    dir_path starts with the given directory.
    """
    query = """
        SELECT DISTINCT dir_path, filename, filesize
        FROM chunk
        WHERE dir_path LIKE %s || '%%';
    """
    rows = get_dict(query, (dir_path,))
    return {(r["dir_path"], r["filename"], r["filesize"]) for r in rows}


def delete_chunks_for_file(dir_path: str, filename: str) -> int:
    """
    Deletes all chunks for the given file. Returns count of deleted rows.
    """
    query = "DELETE FROM chunk WHERE dir_path = %s AND filename = %s;"
    with _database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (dir_path, filename))
            return cursor.rowcount


def insert_chunks(chunks: list[Chunk], project_id: int | None = None) -> int:
    """
    Returns: number of successful insertions
    **TODO = make project_id dynamic**
    **TODO Optimization = executemany() or psycopg2.extras.execute_values() ?**
    """
    if not project_id:
        project_id = get_max_project_id() + 1

    insert_count = 0
    query = """
    INSERT INTO chunk (
        project_id,
        filename,
        dir_path,
        chunk_text,
        embedding,
        chunk_number,
        total_chunks,
        filesize,
        metadata
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    with _database_connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            for chunk in chunks:
                cursor.execute(
                    query,
                    (
                        project_id,
                        chunk.filename,
                        chunk.dir_path,
                        chunk.chunk_text,
                        chunk.embedding,
                        chunk.chunk_number,
                        chunk.total_chunks,
                        chunk.filesize,
                        Json(chunk.metadata),
                    ),
                )
                insert_count += 1
    return insert_count


def test():
    print("📦 Testing database connection...")
    result = get_dict("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = [t["table_name"] for t in result]
    print(f"    ✅ Database Connected, '{env['PG_DB_NAME']}' Database is present.")
    print(f"    ✅ Tables found: {', '.join(tables)}")


test()  # RUN A TEST WHENEVER THE MODULE IS LOADED

if __name__ == "__main__":
    print(get_max_project_id())
