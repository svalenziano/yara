
from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import client

def basic_rag(query, conversation) -> str:
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