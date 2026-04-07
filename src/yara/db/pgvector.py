import logging
from contextlib import contextmanager
from typing import cast

import psycopg2
from psycopg2.extras import Json, RealDictCursor, RealDictRow

from yara.config import env
from yara.types import Chunk, SimilarChunk

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
            for table in ["chunk", "project"]:
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
                """
                CREATE TABLE IF NOT EXISTS project (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    ingestion_path VARCHAR(500) NOT NULL,
                    last_ingested TIMESTAMPTZ DEFAULT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE
                );
                """,
            )
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunk (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    project_id BIGINT NOT NULL REFERENCES project(id),
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


def list_projects() -> list[RealDictRow]:
    return get_dict(
        """
        SELECT p.id, p.name, p.description, p.ingestion_path, p.last_ingested,
               COUNT(DISTINCT c.filename) AS file_count
        FROM project p
        LEFT JOIN chunk c ON c.project_id = p.id
        WHERE p.active = TRUE
        GROUP BY p.id
        ORDER BY p.id;
        """
    )


def get_project(project_id: int) -> RealDictRow:
    rows = get_dict(
        "SELECT id, name, description, ingestion_path, last_ingested FROM project WHERE id = %s;",
        (project_id,),
    )
    return rows[0]


def get_or_create_project(
    name: str, ingestion_path: str, description: str | None = None
) -> int:
    rows = get_dict(
        "SELECT id FROM project WHERE ingestion_path = %s;",
        (ingestion_path,),
    )
    if rows:
        return rows[0]["id"]
    rows = get_dict(
        "INSERT INTO project (name, ingestion_path, description) VALUES (%s, %s, %s) RETURNING id;",
        (name, ingestion_path, description),
    )
    return rows[0]["id"]


def update_project(project_id: int, name: str, description: str | None) -> None:
    with _database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE project SET name = %s, description = %s WHERE id = %s;",
                (name, description, project_id),
            )


def deactivate_project(project_id: int) -> None:
    with _database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE project SET active = FALSE WHERE id = %s;",
                (project_id,),
            )


def update_project_last_ingested(project_id: int) -> None:
    with _database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE project SET last_ingested = NOW() WHERE id = %s;",
                (project_id,),
            )


def get_similar_chunks(embedding, top_k: int, project_id: int) -> list[SimilarChunk]:
    """
    Args:
        embedding: the embedding you wish to find similar chunks to
        top_k: how many records to return?
        project_id: only return chunks belonging to this project
    """
    query = """
        SELECT
            id, project_id, filename, dir_path, chunk_text,
            1 - (embedding <=> %s::vector) AS cosine_similarity
        FROM chunk
        WHERE project_id = %s
        ORDER BY cosine_similarity DESC
        LIMIT %s;
    """
    rows = get_dict(query, (embedding, project_id, top_k))
    return [cast(SimilarChunk, dict(d)) for d in rows]


def _nuke_chunks():
    result = get_dict("""
        DELETE FROM chunk RETURNING project_id;
    """)
    delete_count = len(result)
    print(f"📦 Deleted all {delete_count} from the table.")


def get_ingested_files(dir_path: str, project_id: int) -> set[tuple[str, str, int]]:
    """
    Returns set of (dir_path, filename, filesize) for all chunks whose
    dir_path starts with the given directory.
    """
    query = """
        SELECT DISTINCT dir_path, filename, filesize
        FROM chunk
        WHERE dir_path LIKE %s || '%%'
        AND project_id = %s;
    """
    rows = get_dict(query, (dir_path, project_id))
    return {(r["dir_path"], r["filename"], r["filesize"]) for r in rows}


def delete_chunks_for_file(dir_path: str, filename: str, project_id: int) -> int:
    """
    Deletes all chunks for the given file. Returns count of deleted rows.
    """
    query = (
        "DELETE FROM chunk WHERE dir_path = %s AND filename = %s AND project_id = %s;"
    )
    with _database_connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (dir_path, filename, project_id))
            count = cursor.rowcount
            logger.info(
                "DELETE chunk WHERE dir_path=%s filename=%s project_id=%d → %d rows",
                dir_path,
                filename,
                project_id,
                count,
            )
            return count


def insert_chunks(chunks: list[Chunk], project_id: int) -> int:
    """
    Returns: number of successful insertions
    **TODO = make project_id dynamic**
    **TODO Optimization = executemany() or psycopg2.extras.execute_values() ?**
    """

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
    logger.info("INSERT chunk: %d rows (project_id=%d)", insert_count, project_id)
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
    setup()
