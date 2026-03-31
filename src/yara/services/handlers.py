
from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import client

def initialize_conversation() -> list[dict]:
    SYSTEM_PROMPT = "You are a helpful AI assistant tasked with helping the user find materials within a database of documents."
    GREETING = "How can I help you today?"
    conversation = [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": GREETING},
    ]
    return conversation

def first_rag_request(query, conversation) -> str:
    """
    Input: query and convo
    Side effects: mutate convo to reflect new interactions
    Return: last assistant response

    Algo:
        - Augment convo w chunks from vector DB
    """
    found = query_similar_chunks_pretty(query)

    conversation.append({
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
    })

    response = client.responses.create(
        model="gpt-4.1-2025-04-14",
        input=conversation,  # type: ignore
        temperature=0,
    )

    final_response = response.output_text

    conversation.append({
        "role": "assistant",
        "content": final_response,
    })

    return final_response

def new_topic(query, conversation) -> str:
    """
    TODO - compress the history!

    Remove existing context and submit new query to LLM.
    """
    return ""

