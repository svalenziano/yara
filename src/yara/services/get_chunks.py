"""
Query the ingested data
"""

from opentelemetry import trace

from yara.db.pgvector import get_similar_chunks
from yara.services.openai_client import generate_single_embedding

tracer = trace.get_tracer(__name__)


def query_similar_chunks(query_text: str, top_k=10):
    """

    Algo:
    - Embed the query
    - Query the DB for similar chunks
    - Return chunks
    """
    with tracer.start_as_current_span("retriever", attributes={
        "openinference.span.kind": "RETRIEVER",
        "input.value": query_text,
    }) as span:
        query_vector = generate_single_embedding(query_text)
        results = get_similar_chunks(query_vector, top_k=top_k)
        span.set_attribute("retrieval.documents", len(results))
        return results


def query_similar_chunks_pretty(query_text: str) -> str:
    result = ""

    for r in query_similar_chunks(query_text):
        result += "\n" + "-" * 10
        result += "\n" + r["filename"]
        result += "\n" + "-" * 10
        result += "\n" + r["chunk_text"]

    return result


if __name__ == "__main__":
    pass
