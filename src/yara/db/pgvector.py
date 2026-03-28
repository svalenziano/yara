import psycopg2
from psycopg2.extras import RealDictCursor, RealDictRow
from config import env
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
    result = get_dict("""
    SELECT id,
           book_title,
           chapter_title,
           chapter_url,
           substr(embedding::text, 1, 50) || '...' as truncated_embedding
    FROM book_chapter
    LIMIT 15;
    """
    )

    print(result)


# RUN A TEST WHENEVER THE MODULE IS LOADED
print("Testing database connection...")
test()
print("Database Connected 🙂")

if __name__ == "__main__":
    pass