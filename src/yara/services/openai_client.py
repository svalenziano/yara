from textwrap import dedent
from typing import Callable


from openai import OpenAI

from yara.config import env
from yara.services.conversation import Conversation

client = OpenAI(api_key=env["OPENAI_API_KEY"])

MODELS = {
    "fast": "gpt-4.1-nano-2025-04-14",
    "normal": "gpt-4.1-mini-2025-04-14",
    "heavy": "gpt-4.1",
}


def classify_request(
    conversation: Conversation, possible_options: list[Callable]
) -> str:
    """
    Make a routing decision

    Input = query
    Output = query path aka routing decision.  Must one one of `possible_options`
    """
    if not possible_options:
        raise TypeError("possible_options must be provided")

    options = {}
    pass


def enrich_query(conversation: Conversation) -> str:
    """
    Returns enriched query which can be used for vector DB querying
    """

    augmented_convo = conversation.get_augmented_entries(
        dedent("""
        Please review the above conversation.  My goal is to rewrite
        the user's last query such that it will return more accurate
        result from a vector database.  Can you provide such a query?

        Return only the query.  Do not include any additional text.
    """)
    )

    response = client.responses.create(
        model=MODELS["fast"],
        input=augmented_convo,  # type: ignore
        temperature=0,
    )

    return response.output_text

def simple_llm_call(conversation: Conversation) -> str:
    response = client.responses.create(
        model=MODELS['normal'],
        input=conversation.entries(),  # type: ignore
        temperature=0,
    )

    return response.output_text

def generate_embeddings(text: list[str], metadata: list[dict] = []):
    """
    Args:
        - text: list of texts to embed
        - metadata: added to the embedding, if present

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
    if metadata:
        text = [
            " ".join(f"{k}: {v}" for k, v in meta.items()) + "\n" + t
            for t, meta in zip(text, metadata)
        ]

    response = client.embeddings.create(
        model="text-embedding-3-small", input=text, dimensions=int(env["VECTOR_DIMS"])
    )

    if not response.data:
        raise Exception("Invalid OpenAI response", response)

    return response.data


def generate_single_embedding(text: str) -> list[float]:
    """
    Returns a single embedding e.g. [1.23, 4.56, ... , 7.89]
    """
    return generate_embeddings([text])[0].embedding
