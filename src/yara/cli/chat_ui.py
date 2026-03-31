from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.cursor_shapes import CursorShape

from yara.services.router import router



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

        route = router(ask, conversation)
        llm_response = route(ask, conversation)

        render_assistant(llm_response)


if __name__ == "__main__":
    chat_loop()
