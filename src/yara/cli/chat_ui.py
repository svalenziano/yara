from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.cursor_shapes import CursorShape

from yara.services.router import router
from yara.services.handlers import initialize_conversation



console = Console()




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

    conversation = initialize_conversation()

    render_assistant(conversation[-1]['content'])

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

        handler = router(ask, conversation)
        llm_response = handler(ask, conversation)

        render_assistant(llm_response)


if __name__ == "__main__":
    chat_loop()
