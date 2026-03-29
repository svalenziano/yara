from yara.services.openai_client import client
from yara.config import env

def generate_embeddings(text: list[str]):
    """
    Input: String to embed
    
    Return: EmbeddingResponse, e.g.
    ```
        {
            "object": "list",
            "data": [
                {
                "object": "embedding",
                "embedding": [
                    0.0023064255,
                    -0.009327292,
                    .... (1536 floats total for ada-002)
                    -0.0028842222,
                ],
                "index": 0
                }
            ],
            "model": "text-embedding-ada-002",
            "usage": {
                "prompt_tokens": 8,
                "total_tokens": 8
            }
        }
    ```

    **MAXIMUMS:**
        8,192 tokens per embedding
        300,000 tokens per request
    
    [Docs](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create)
    """
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=int(env['VECTOR_DIMS'])
    )

    if not response.data:
        raise Exception("Invalid OpenAI response", response)
    
    return response.data


def generate_single_embedding(text: str) -> list[float]:
    """
    Returns a single embedding e.g. [1.23, 4.56, ... , 7.89]
    """
    return generate_embeddings([text])[0].embedding