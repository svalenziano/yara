"""
LLM-powered routing and classification
"""

from typing import Callable

import yara.services.handlers as handlers

# ROUTES = [rag_request]

counter = 0


def router(query: str, conversation: list[dict]) -> Callable:
    """
    # TODO: determine whether user is asking about current
        information, or new information


        Idea:
            -
    """
    global counter
    counter += 1

    if counter <= 1:
        return handlers.rag_request

    # TODO: CLASSIFY the request and return a specific handler
    # Tell the LLM what handlers you have, provide the conversation history.
    # let the LLM decide on the route
    # return the appropriate route
    return handlers.rag_request
