from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.cursor_shapes import CursorShape

from yara.services.get_chunks import query_similar_chunks_pretty
from yara.services.openai_client import client


console = Console()

SYSTEM_PROMPT = "You are a helpful AI assistant tasked with helping the user find materials within a database of documents."
GREETING = "How can I help you today?"


def get_user_input(history):
    return prompt(
        HTML("<ansiblue>❯ </ansiblue>"),
        history=history,
        cursor=CursorShape.BLINKING_BLOCK,
    )


def render_assistant(text):
    console.print()
    console.print(Panel(Markdown(text), title="Assistant", border_style="bright_black"))
    console.print()


def chat_loop():
    history_file = FileHistory(".yara_chat_history")
    conversation = [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": GREETING},
    ]

    render_assistant(GREETING)

    while True:
        try:
            ask = get_user_input(history_file)
        except (EOFError, KeyboardInterrupt):
            render_assistant("Goodbye!")
            break

        if ask.strip().lower().strip("/") == "exit":
            console.print("\nGoodbye!")
            break

        if not ask.strip():
            continue

        """
        Todo: classifier

        IDEAS
            1) 
                - execute classifer, return a 'route' string
                - switch modes based on that string

            2) 
                - ???
        """

        

        found = query_similar_chunks_pretty(ask)



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
                {ask}
                </question>
                """,
        })

        response = client.responses.create(
            model="gpt-4.1-2025-04-14",
            input=conversation,  # type: ignore
            temperature=0,
        )

        conversation.append({
            "role": "assistant",
            "content": response.output_text,
        })

        render_assistant(response.output_text)


if __name__ == "__main__":
    chat_loop()
