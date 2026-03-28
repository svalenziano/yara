from yara.services.openai_client import client
from yara.config import env

def generate_embedding(text: str, verbose=False) -> list[float]:
    """
    Input: String to embed
    Return: Embedding (Array of numbers)
    """
    if verbose: print("░", end="")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=int(env['VECTOR_DIMS'])
    )
    embed = response.data[0].embedding

    if verbose: print("█", end="")
    
    return embed