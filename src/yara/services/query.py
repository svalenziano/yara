"""
Query the ingested data
"""

from yara.services.openai_embedding import generate_single_embedding
from yara.db.pgvector import get_similar_chunks

def query_similar_chunks(query_text: str):
    """
    
    Algo:
    - Embed the query
    - Query the DB for similar chunks
    - Return chunks
    """
    query_vector = generate_single_embedding(query_text)
    return 
