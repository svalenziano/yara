"""
LLM-powered routing and classification
"""

from typing import Callable

import yara.services.handlers as handlers
from yara.services.conversation import Conversation

ROUTES = [handlers.rag_request]

counter = 0


def router(query: str, conversation: Conversation) -> Callable:
    """
    # TODO: determine whether user is asking about current
        information, or new information


        Idea:
            -
    """


    if len(conversation) <= 3:  # Conversation has just begun
        return handlers.rag_request

    # TODO: CLASSIFY the request and return a specific handler
    # Tell the LLM what handlers you have, provide the conversation history.
    # let the LLM decide on the route
    # return the appropriate route
    return handlers.rag_request
