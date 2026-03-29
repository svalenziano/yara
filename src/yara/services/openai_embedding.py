from yara.services.openai_client import client
from yara.config import env

def generate_embeddings(text: list[str], metadata=list[dict], verbose=False):
    """
    Input: String to embed
    Return: Embedding (Array of numbers)

    **MAXIMUMS:**
    8,192 tokens per embedding
    300,000 tokens per request
    [API Docs](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create)
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=int(env['VECTOR_DIMS'])
    )

    if not response.data:
        raise Exception("Invalid OpenAI response", response)
    
    return response.data