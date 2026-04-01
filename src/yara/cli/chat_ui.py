from opentelemetry import trace
from prompt_toolkit import prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from yara.services.conversation import Conversation
from yara.services.router import not_a_router

console = Console()
tracer = trace.get_tracer(__name__)


def assistant_panel(text: str) -> Panel:
    return Panel(Markdown(text), title="Assistant", border_style="bright_black")


def get_user_input(history):
    return prompt(
        HTML("<ansiblue>❯ </ansiblue>"),
        history=history,
        cursor=CursorShape.BLINKING_BLOCK,
    )


def render_assistant(text):
    console.print()
    console.print(assistant_panel(text))  # will not render if you place inside f-string
    console.print()


def stream_assistant(chunks):
    full_text = ""
    console.print()
    with Live(
        assistant_panel("..."),
        console=console,
        refresh_per_second=12,
    ) as live:
        for chunk in chunks:
            full_text += chunk
            live.update(assistant_panel(full_text))
    console.print()
    return full_text


def chat_loop():
    cli_history_file = FileHistory(".yara_chat_history")

    conversation = Conversation()

    render_assistant(conversation.first_assistant_prompt())

    while True:
        try:
            query = get_user_input(cli_history_file)
        except (EOFError, KeyboardInterrupt):
            render_assistant("Goodbye!")
            break

        if query.strip().lower().strip("/") == "exit":
            render_assistant("Goodbye!")
            break

        if not query.strip():
            continue

        with tracer.start_as_current_span(
            "query",
            attributes={
                "input.value": query,
            },
        ) as span:
            conversation.add_entry("user", query)
            handler = not_a_router(conversation)
            llm_response_stream = handler(conversation)
            llm_response = stream_assistant(llm_response_stream)
            span.set_attribute("output.value", llm_response)


if __name__ == "__main__":
    chat_loop()
