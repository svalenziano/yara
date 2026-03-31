"""
Query the ingested data
"""

from rich import print
from yara.services.openai_embedding import generate_single_embedding
from yara.db.pgvector import get_similar_chunks
from yara.services.openai_client import client

def query_similar_chunks(query_text: str, top_k=10):
    """
    
    Algo:
    - Embed the query
    - Query the DB for similar chunks
    - Return chunks
    """
    query_vector = generate_single_embedding(query_text)
    return get_similar_chunks(query_vector, top_k=top_k)

def query_similar_chunks_pretty(query_text: str) -> str:
    result = ""

    for r in query_similar_chunks(query_text):
        result += "\n" + "-" * 10
        result += "\n" + r['filename']
        result += "\n" + "-" * 10
        result += "\n" + r['chunk_text']
    
    return result


if __name__ == "__main__":
    pass