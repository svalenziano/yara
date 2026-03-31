from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import client

SYSTEM_PROMPT = "You are a helpful AI assistant tasked with helping the user find materials within a database of documents.  "


def initialize_conversation(greeting=None) -> list[dict]:

    GREETING = "How can I help you today?"
    conversation = [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": greeting or GREETING},
    ]
    return conversation


def get_response_and_augment_convo(conversation) -> str:
    response = client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=conversation,  # type: ignore
        temperature=0,
    )

    response_text = response.output_text

    conversation.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )

    return response_text


def first_rag_request(query, conversation) -> str:
    """
    Input: query and convo
    Side effects: mutate convo to reflect new interactions
    Return: last assistant response

    Algo:
        - Augment convo w chunks from vector DB
    """
    found = query_similar_chunks_pretty(query)

    conversation.append(
        {
            "role": "user",
            "content": f"""Please use these documents to answer my question.
            Please do NOT rely on your training knowledge to answer my question.
            If the question is not answerable based on these documents, please let me know.

            Here are the documents:
            <documents>
            {found}
            </documents>

            Here is my question:
            <question>
            {query}
            </question>
            """,
        }
    )

    return get_response_and_augment_convo(conversation)


def ask_about_new_topic(query, conversation) -> str:
    """
    The user has asked about something that seems very different from the previous line of questioning.  Ask the user if they want to start a new conversation.
    """
    response = "It sounds like you'd like to start a conversation about a new topic, is this correct?"

    conversation += [
        {"role": "user", "content": query},
        {"role": "assistant", "content": response},
    ]

    return response


def new_topic(query, conversation) -> str:
    """
    The user has asked to start a conversation about a new topic.
    The conversation will be compressed to make room for the new convo.


    TODO - actually compress the history instead of this hacky method!

    """
    summary = "You just had a conversation about another topic, and the user is now asking about a new topic.  "

    conversation.clear()
    conversation += [
        {"role": "developer", "content": SYSTEM_PROMPT + summary},
        {
            "role": "assistant",
            "content": "Ok, what's the next thing I can help you with?",
        },
        {"role": "user", "content": query},
    ]

    return get_response_and_augment_convo(conversation)
