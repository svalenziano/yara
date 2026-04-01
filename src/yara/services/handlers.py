from textwrap import dedent

from opentelemetry import trace

from yara.services.conversation import SYSTEM_PROMPT, Conversation
from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import simple_llm_call, enrich_query

tracer = trace.get_tracer(__name__)


def _get_llm_response_and_update_convo(conversation: Conversation) -> str:
    """
    Utility function: get a simple response from the LLM,
    update the convo, and return the response text.
    """
    response_text = simple_llm_call(conversation)
    conversation.add_entry("assistant", response_text)
    return response_text


def rag_request(conversation: Conversation) -> str:
    """
    The user is asking a question that requires searching the knowledge base
    for relevant documents. Use this route when the user asks about facts,
    topics, or details that should come from their stored documents.
    """
    with tracer.start_as_current_span("rag_request"):
        query = conversation.get_last_user_query()
        enriched = enrich_query(conversation)

        found = query_similar_chunks_pretty(enriched)

        conversation.replace_last_entry(
            "user",
            dedent(f"""Please use these documents to answer my question.
                Please do NOT rely on your training knowledge to answer my question.
                If the question is not answerable based on these documents,
                please let me know.

                Here are the documents:
                <documents>
                {found}
                </documents>

                Here is my question:
                <question>
                {query}
                </question>
                """),
        )

        return _get_llm_response_and_update_convo(conversation)


def simple_request(conversation: Conversation) -> str:
    """
    The user's request can be answered without retrieving more docs.
    Respond to the user with the context you currently have.
    """
    return _get_llm_response_and_update_convo(conversation)


def ask_about_new_topic(conversation: Conversation) -> str:
    """
    The user has asked about something that seems very different from
    the previous line of questioning.  Ask the user if they want to start
    a new conversation.
    """

    response = (
        "It sounds like you'd like to start a conversation"
        " about a new topic, is this correct? y/n"
    )

    conversation.add_entry("assistant", response)

    return response


def new_topic(conversation: Conversation) -> str:
    """
    The user has asked to start a conversation about a new topic.
    The conversation will be compressed to make room for the new convo.
    """
    query = conversation.get_last_user_query()
    summary = (
        "You just had a conversation about another topic,"
        " and the user is now asking about a new topic.  "
    )

    conversation.reset(
        developer_content=SYSTEM_PROMPT + summary,
        greeting="Ok, what's the next thing I can help you with?",
    )
    conversation.add_entry("user", query)

    return _get_llm_response_and_update_convo(conversation)
