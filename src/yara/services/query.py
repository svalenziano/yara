"""
Query the ingested data
"""

from rich import print
from yara.services.openai_embedding import generate_single_embedding
from yara.db.pgvector import get_similar_chunks
from yara.services.openai_client import client

def query_similar_chunks(query_text: str, top_k=10):
    """
    
    Algo:
    - Embed the query
    - Query the DB for similar chunks
    - Return chunks
    """
    query_vector = generate_single_embedding(query_text)
    return get_similar_chunks(query_vector, top_k=top_k)

def simple_query(query_text: str) -> str:
    result = ""

    for r in query_similar_chunks(query_text):
        result += "\n" + "-" * 10
        result += "\n" + r['filename']
        result += "\n" + "-" * 10
        result += "\n" + r['chunk_text']
    
    return result

def llm_query_loop():
    system_prompt = "You are a helpful AI assistant tasked with helping the user find materials within a database of documents."
    first_prompt = 'How can I help you today?'
    history = [
        {
            'role': 'developer',
            'content': system_prompt,
        },
        {
            'role': 'assistant',
            'content': first_prompt
        }
    ]
    
    print("Assistant: ", first_prompt)
    ask = input("\nUser: ")


    while True:
        
        found = simple_query(ask)

        history += [
            {
                'role': 'user',
                'content': f"""Please use these documents to answer my question.
                Please do NOT rely on your training to answer my question.
                If the question is not answerable based on these documents, please let me know.

                Here are the documents:
                <documents>
                {found}
                </documents>

                Here is my question:
                <question>
                {ask}
                </question>
                """
             }
        ]

        response = client.responses.create(
            model="gpt-4.1-2025-04-14",
            input=history,  # type: ignore
            temperature=0,
        )

        history += [
            {
                'role': 'assistant',
                'content': response.output_text,
            }
        ]

        print(f"\nAssistant: {response.output_text}")

        ask = input("\nUser: ")

        if ask.lower().strip("/") == "exit":
            print("\n Goodbye!")
            quit()

if __name__ == "__main__":
    # print(simple_query("Dogs"))
    llm_query_loop()