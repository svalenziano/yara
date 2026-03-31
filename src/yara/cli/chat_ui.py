from prompt_toolkit import prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from yara.services.conversation import Conversation
from yara.services.router import router

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
    cli_history_file = FileHistory(".yara_chat_history")

    conversation = Conversation()

    render_assistant(conversation.first_assistant_prompt())

    while True:
        try:
            ask = get_user_input(cli_history_file)
        except (EOFError, KeyboardInterrupt):
            render_assistant("Goodbye!")
            break

        if ask.strip().lower().strip("/") == "exit":
            render_assistant("Goodbye!")
            break

        if not ask.strip():
            continue

        handler = router(ask, conversation)
        llm_response = handler(ask, conversation)

        render_assistant(llm_response)


if __name__ == "__main__":
    chat_loop()
