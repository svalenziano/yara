from opentelemetry import trace
from prompt_toolkit import prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from yara.services.conversation import Conversation
from yara.services.router import not_a_router
from yara.types import SimilarChunk

console = Console()
tracer = trace.get_tracer(__name__)


def sources_panel(sources: list[SimilarChunk]) -> Panel:
    """
    Deduplicate by dir_path+filename, sort alphabetically,
    render with styled paths.
    """
    deduplicated: list[str] = []

    for idx, source in enumerate(sources):
        fullpath = f"{idx}) '{source['filename']}'"
        # fullpath = f"{idx}) {source['dir_path']}/{source['filename']}"
        if fullpath not in deduplicated:
            deduplicated.append(fullpath)
    deduplicated.sort()
    return Panel(
        Markdown("\n".join(deduplicated)),
        title="Sources",
        border_style="grey50",
        style="grey50",
    )


def assistant_panel(text: str) -> Panel:
    return Panel(Markdown(text), title="Assistant", border_style="bright_black")


def loading_panel() -> Panel:
    return Panel(Spinner("dots"), title="Assistant", border_style="bright_black")


def get_user_input(history):
    return prompt(
        HTML("<ansiblue>❯ </ansiblue>"),
        history=history,
        cursor=CursorShape.BLINKING_BLOCK,
    )


def render_assistant(text):
    console.print()
    console.print(assistant_panel(text))
    console.print()


def stream_assistant(chunks):
    full_text = ""
    console.print()
    with Live(
        loading_panel(),
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

            # do RAG at every loop, for now.
            # Todo: add real routing
            handler = not_a_router(conversation)
            llm_response_stream = handler(conversation)

            # render response and provide full response for logging
            llm_response = stream_assistant(llm_response_stream)

            sources = conversation.read_sources()
            if sources:
                console.print(sources_panel(sources))
                console.print()
                conversation.clear_sources()
            span.set_attribute("output.value", llm_response)


if __name__ == "__main__":
    chat_loop()
