"""
LLM-powered routing and classification
"""
from yara.services.handlers import basic_rag

ROUTES = [
    basic_rag
]

def router(query: str, conversation: list[dict]):
    return basic_rag
