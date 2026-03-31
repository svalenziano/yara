"""
LLM-powered routing and classification
"""

from typing import Callable

from yara.services.handlers import first_rag_request

ROUTES = [first_rag_request]


def router(query: str, conversation: list[dict]) -> Callable:
    """
    # TODO: determine whether user is asking about current
        information, or new information


        Idea:
            -
    """

    return first_rag_request
