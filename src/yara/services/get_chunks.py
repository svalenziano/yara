"""
Query the ingested data
"""

from opentelemetry import trace

from yara.db.pgvector import get_similar_chunks
from yara.services.openai_client import generate_single_embedding
from yara.types import SimilarChunk

tracer = trace.get_tracer(__name__)


def query_similar_chunks(query_text: str, top_k=10) -> str:
    """
    Accepts a text query for the vectorDB and returns a big
    string that includes the matching chunks
    """
    with tracer.start_as_current_span(
        "retriever",
        attributes={
            "openinference.span.kind": "RETRIEVER",
            "input.value": query_text,
        },
    ) as span:
        query_vector = generate_single_embedding(query_text)
        results = get_similar_chunks(query_vector, top_k=top_k)
        span.set_attribute("retrieval.documents", len(results))
        return format_chunks(results)


def format_chunks(chunks: list[SimilarChunk]) -> str:

    result = "<chunks>"

    for chunk in chunks:
        result += f"\n\n<chunk filename={chunk['filename']}>"
        result += "\n" + chunk["chunk_text"]
        result += f"\n</chunk filename={chunk['filename']}>"

    return result + "\n</chunks>\n\n"


if __name__ == "__main__":
    pass
