from yara.openai_client import client

def generate_embedding(text: str, verbose=False) -> list[float]:
    """
    Input: String to embed
    Return: Embedding (Array of numbers)
    """
    if verbose: print("Fetching embedding")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    embed = response.data[0].embedding

    if verbose: print("Successful fetch!")
    
    return embed