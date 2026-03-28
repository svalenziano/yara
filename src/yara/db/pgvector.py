import psycopg2
from psycopg2.extras import RealDictCursor, RealDictRow
from yara.config import env
from contextlib import contextmanager

@contextmanager
def _database_connect():
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=env['PG_DB_NAME'],
            host=env["PG_HOST"],
            port=env["PG_PORT"],
            user=env["PG_USER"],
            password=env["PG_PASSWORD"] or None
        )
        yield connection
        connection.commit()
    except Exception as e:
        print("Database error: ", e)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def setup():
    with _database_connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS chunk (
                    id SERIAL PRIMARY KEY,
                    project_id BIGINT NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    dir_path VARCHAR(500) NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding VECTOR({env['VECTOR_DIMS']}) NOT NULL,
                    chunk_number INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                filesize INTEGER NOT NULL,
                    metadata JSONB NOT NULL
                );
            """, )
        except Exception as e:
            print("Error durring database setup")
            raise(e)
        finally:
            cur.close()

def get_dict(query, params=()) -> list[RealDictRow]:
    with _database_connect() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
        
def get_similar(embedding, top_k: int) -> list[dict]:
    """
    top_k = how many records to return?
    """
    query = """
        SELECT id, book_title, chapter_title, chapter_url, 
            1 - (embedding <=> %s::vector) AS cosine_similarity
        FROM book_chapter
        ORDER BY cosine_similarity DESC
        LIMIT %s;
    """
    return [dict(d) for d in get_dict(query, (embedding, top_k))]

def test():
    print("Testing database connection...")
    get_dict("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    print(f"✅ Database Connected, {env['PG_DB_NAME']} table is present.\n")


test()  # RUN A TEST WHENEVER THE MODULE IS LOADED

if __name__ == "__main__":
    pass