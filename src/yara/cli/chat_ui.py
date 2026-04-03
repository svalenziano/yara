import uuid

from openinference.instrumentation import using_session
from opentelemetry import trace
from prompt_toolkit import prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.markdown import Markdown
from rich.panel import Panel

from yara.cli.colors import console
from yara.cli.commands import (
    SLASH_COMMAND_STYLE,
    CommandContext,
    SlashCommandLexer,
    dispatch,
)
from yara.cli.ui_helpers import render_assistant, stream_assistant
from yara.db.pgvector import get_project
from yara.services.conversation import Conversation
from yara.services.router import not_a_router
from yara.types import SimilarChunk

tracer = trace.get_tracer(__name__)


def numbered_markdown_list(texts: list[str]) -> str:
    """
    Given ['lorem', 'ipsum'] returns:
        1) lorem
        2) ipsum
    """
    return "\n".join(f"{i + 1}) {text}" for i, text in enumerate(texts))


def sources_panel(sources: list[SimilarChunk]) -> Panel:
    """
    List of sources
    Do not sort (keep original relevance sorting from vector DB)
    """
    deduplicated: list[str] = []

    for source in sources:
        path = f"'{source['filename']}'"
        # fullpath = f"{idx}) {source['dir_path']}/{source['filename']}"
        if path not in deduplicated:
            deduplicated.append(path)
    # numbered = numbered_markdown_list(deduplicated)
    return Panel(
        Markdown("\n".join(deduplicated)),
        title="Sources",
        border_style="grey50",
        style="grey50",
    )


def get_user_input(history):
    return prompt(
        HTML("<ansiblue>❯ </ansiblue>"),
        history=history,
        cursor=CursorShape.BLINKING_BLOCK,
        lexer=SlashCommandLexer(),
        style=SLASH_COMMAND_STYLE,
    )


def chat_loop(project_id: int) -> str | None:
    cli_history_file = FileHistory(".yara_chat_history")
    session_id = str(uuid.uuid4())

    with using_session(session_id):
        conversation = Conversation(project_id=project_id)
        project = dict(get_project(project_id))
        ctx = CommandContext(
            conversation=conversation, console=console, project=project
        )

        render_assistant(conversation.first_assistant_prompt())

        while True:
            try:
                query = get_user_input(cli_history_file)
            except (EOFError, KeyboardInterrupt):
                render_assistant("Goodbye!")
                break

            if not query.strip():
                continue

            if dispatch(query, ctx):
                if ctx.signal.get("exit"):
                    render_assistant("Goodbye!")
                    break
                if ctx.signal.get("home"):
                    return "home"
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
    chat_loop(project_id=1)
