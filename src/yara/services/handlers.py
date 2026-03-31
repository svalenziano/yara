from yara.services.conversation import SYSTEM_PROMPT, Conversation
from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import simple_llm_call


def _get_response_and_update_convo(conversation: Conversation) -> str:
    response_text = simple_llm_call(conversation)
    conversation.add_entry("assistant", response_text)
    return response_text


def rag_request(query: str, conversation: Conversation) -> str:
    """
    Augment the conversation with chunks from the vector DB and
    query the LLM for a response

    Input: query and convo
    Side effects: mutate convo to reflect new interactions
    Return: last assistant response
    """
    found = query_similar_chunks_pretty(query)

    conversation.add_entry(
        "user",
        f"""Please use these documents to answer my question.
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
            """,
    )

    return _get_response_and_update_convo(conversation)

def simple_request(query, conversation) -> str:
    conversation.add_entry(query)
    return _get_response_and_update_convo(conversation)

def ask_about_new_topic(query: str, conversation: Conversation) -> str:
    """
    The user has asked about something that seems very different from
    the previous line of questioning.  Ask the user if they want to start
    a new conversation.
    """
    response = (
        "It sounds like you'd like to start a conversation"
        " about a new topic, is this correct?"
    )

    conversation.add_entry("user", query)
    conversation.add_entry("assistant", response)

    return response


def new_topic(query: str, conversation: Conversation) -> str:
    """
    The user has asked to start a conversation about a new topic.
    The conversation will be compressed to make room for the new convo.


    TODO - actually compress the history instead of this hacky method!

    """
    summary = (
        "You just had a conversation about another topic,"
        " and the user is now asking about a new topic.  "
    )

    conversation.reset(
        developer_content=SYSTEM_PROMPT + summary,
        greeting="Ok, what's the next thing I can help you with?",
    )
    conversation.add_entry("user", query)

    return _get_response_and_update_convo(conversation)
