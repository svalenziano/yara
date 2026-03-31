"""
LLM-powered routing and classification
"""

import logging
from typing import Callable

from pydantic import BaseModel
from rich import print
from rich.console import Console

import yara.services.handlers as handlers
from yara.services.conversation import Conversation
from yara.services.openai_client import classify_request

ROUTES = [
    handlers.rag_request,
    handlers.simple_request,
    handlers.new_topic,
]

logger = logging.getLogger(__name__)
console = Console()


def router(conversation: Conversation) -> Callable:
    if len(conversation) <= 3:  # Conversation has just begun
        logger.info("routing to rag_request (conversation start)")
        return handlers.rag_request

    query = conversation.get_last_user_query()
    chosen = classify_request(query, conversation, ROUTES)
    logger.info("routing to %s", chosen.__name__)
    return chosen

def _test_router():
    for query in [
        "I'm looking for an electrician",
        "What documents do I have that explain Arduino?",
        "How did you arrive at that answer?",
        "Oh really, tell me more"
    ]:
        convo = Conversation()
        convo.add_entry("user","What is 1 + 1?")
        convo.add_entry("assistant","2")
        
        # console.log(convo.get_entries())
        console.log("Classifying...")
        classified = classify_request(
            query, convo, ROUTES, verbose=True
        )
        console.log(classified.__name__)

if __name__ == "__main__":
    _test_router()
