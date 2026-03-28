# from pgvector import _database_connect
from yara.db.pgvector import _database_connect
from psycopg2.extras import RealDictCursor, RealDictRow

def get_dict(query, params=()) -> list[RealDictRow]:
    with _database_connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunk (
                    id SERIAL PRIMARY KEY,
                    project_id bigint NOT NULL,
                    filename varchar(500) NOT NULL,
                    filepath varchar(500) NOT NULL,
                    
                );
            """)
        except Exception as e:
            print("Error durring database setup")
            raise(e)
        finally:
            cur.close()

# conn = psycopg2.connect(
#     host="localhost",
#     port=8888,
#     user="postgres",
#     database="book_search"
# )

# cur = conn.cursor()

# try:
#     cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS book_chapter (
#             id SERIAL PRIMARY KEY,
#             book_title TEXT NOT NULL,
#             chapter_title TEXT NOT NULL,
#             chapter_url TEXT NOT NULL,
#             content TEXT NOT NULL,
#             embedding vector(1536)
#         );
#     """)
#     conn.commit()
#     print("Database setup complete!")
# except Exception as e:
#     print("Error during setup:", e)
# finally:
#     cur.close()
#     conn.close()