from enum import Enum
from textwrap import dedent
from typing import Callable

from openai import OpenAI
from pydantic import BaseModel
from rich import print
from rich.console import Console

from yara.config import env
from yara.services.conversation import Conversation

console = Console()
client = OpenAI(api_key=env["OPENAI_API_KEY"])

MODELS = {
    "fast": "gpt-4.1-nano-2025-04-14",
    "normal": "gpt-4.1-mini-2025-04-14",
    "heavy": "gpt-4.1",
}


def prettify(docstring: str):
    """
    Extracts the important part of the docstring:

    Before:
        This function doe
        very important stuff.

        Args: lorem
        Returns: ipsum

    After:
        This function does stuff very important stuff
    """
    lines = docstring.splitlines()
    summary = []
    for line in lines:
        if line.strip() == "":
            if summary:
                break
        else:
            summary.append(line.strip())
    return " ".join(summary)


def classify_request(
    query: str,
    conversation: Conversation,
    possible_options: list[Callable],
    verbose=False,
) -> Callable:
    """
    Make a routing decision

    Input = query
    Output = query path aka routing decision.  Must one one of `possible_options`

    Algo:
        - format possible_options in the format that OpenAI wants
            - use the function __name__ and __doc__ to pass relevant info to OpenAI
        - query the LLM Structured Output
        - return the result to the user
    """

    options_for_llm = [
        {
            "route_name": option.__name__,
            "route_description": dedent(
                prettify(option.__doc__ if option.__doc__ else "")
            ),
        }
        for option in possible_options
    ]

    RouteEnum = Enum(
        "RouteEnum", {opt["route_name"]: opt["route_name"] for opt in options_for_llm}
    )

    class RoutingDecision(BaseModel):
        route_name: RouteEnum  # type: ignore[valid-type]

    routes_text = "\n".join(
        f"- {opt['route_name']}: {opt['route_description']}" for opt in options_for_llm
    )

    routing_prompt = dedent(f"""
    Based on the conversation and the user's latest message,
    please select the most appropriate route.  More than one route may 
    fit the request.  Pick the route that fits best.

    User's latest message: {query}

    Available routes:\n{routes_text}
    """)

    augmented = conversation.get_augmented_entries(routing_prompt)

    if verbose:
        console.log(augmented)

    response = client.responses.parse(
        model=MODELS["fast"],
        input=augmented,  # type: ignore[arg-type]
        text_format=RoutingDecision,
        temperature=0,
    )
    chosen_name = response.output_parsed.route_name.value  # type: ignore[union-attr]

    for option in possible_options:
        if option.__name__ == chosen_name:
            return option

    raise Exception("ROUTING ERROR:Valid route was not found")


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
        model=MODELS["normal"],
        input=conversation.get_entries(),  # type: ignore
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


if __name__ == "__main__":
    pass
