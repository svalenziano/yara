"""
LLM-powered routing and classification
"""

from typing import Callable
from pydantic import BaseModel

import yara.services.handlers as handlers
from yara.services.conversation import Conversation

ROUTES = [handlers.rag_request]

counter = 0


def router(query: str, conversation: Conversation) -> Callable:
    """
    # TODO: determine whether user is asking about current
        information, or new information


        Idea:
            - query LLM - new or old information?
            - if new, then do RAG
            - if old, then pass existing history with new user query
    """

    if len(conversation) <= 3:  # Conversation has just begun
        return handlers.rag_request

    # TODO: CLASSIFY the request and return a specific handler
    # Tell the LLM what handlers you have, provide the conversation history.
    # let the LLM decide on the route
    # return the appropriate route
    return handlers.rag_request
