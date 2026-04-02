"""
LLM-powered routing and classification
"""

from typing import Callable

from opentelemetry import trace
from rich.console import Console

import yara.services.handlers as handlers
from yara.services.conversation import Conversation
from yara.services.openai_client import classify_request

ROUTES = [
    handlers.rag_request,
    handlers.simple_request,
    # handlers.ask_about_new_topic,
    # handlers.new_topic,
]

tracer = trace.get_tracer(__name__)

def not_a_router(conversation: Conversation) -> Callable:
    """
    A placeholder router, for when you want to disable routing
    """
    return handlers.rag_request

def router(conversation: Conversation) -> Callable:
    if len(conversation) <= 3:  # Conversation has just begun
        return handlers.rag_request

    query = conversation.get_last_user_query()
    with tracer.start_as_current_span("classify"):
        chosen = classify_request(query, conversation, ROUTES)
    return chosen


def _test_router():
    console = Console()
    for query in [
        "I'm looking for an electrician",
        "What documents do I have that explain Arduino?",
        "How did you arrive at that answer?",
        "Oh really, tell me more",
    ]:
        convo = Conversation()
        convo.add_entry("user", "What is 1 + 1?")
        convo.add_entry("assistant", "2")

        # console.log(convo.get_entries())
        console.log("Classifying...")
        classified = classify_request(query, convo, ROUTES, verbose=True)
        console.log(classified.__name__)


if __name__ == "__main__":
    _test_router()
