"""
LLM-powered routing and classification
"""

import logging
from typing import Callable

from pydantic import BaseModel

import yara.services.handlers as handlers
from yara.services.conversation import Conversation
from yara.services.openai_client import classify_request

ROUTES = [
    handlers.rag_request,
    handlers.simple_request,
    handlers.new_topic,
]

logger = logging.getLogger(__name__)


def router(query: str, conversation: Conversation) -> Callable:
    if len(conversation) <= 3:  # Conversation has just begun
        logger.info("routing to rag_request (conversation start)")
        return handlers.rag_request

    chosen = classify_request(query, conversation, ROUTES)
    logger.info("routing to %s", chosen.__name__)
    return chosen


if __name__ == "__main__":
    c = Conversation()
    c.add_entry(role="user", content="What documents do I have that explain Arduino?")
    print("Classifying...")
    classified = classify_request(
        "What documents do I have that explain Arduino?", c, ROUTES
    )
    print(classified.__name__)
