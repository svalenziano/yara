from dataclasses import dataclass, field
from typing import Callable

from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel

from yara.cli.ui_helpers import render_assistant
from yara.services.conversation import Conversation
from yara.services.openai_client import prettify

COMMANDS: dict[str, Callable] = {}


def register_command(name: str):
    def decorator(fn):
        COMMANDS[name] = fn
        return fn

    return decorator


@dataclass
class CommandContext:
    conversation: Conversation
    console: Console
    project: dict | None = None
    signal: dict = field(default_factory=dict)


def dispatch(query: str, ctx: CommandContext) -> bool:
    if not query.startswith("/"):
        return False

    parts = query.split()
    name = parts[0][1:]  # strip leading /

    handler = COMMANDS.get(name)
    if handler is None:
        ctx.console.print(
            f"[red]Unknown command: /{name}[/red] — type /help for available commands"
        )
        return True

    handler(ctx)
    return True


@register_command("exit")
def cmd_exit(ctx: CommandContext):
    """Exit the application."""
    ctx.signal["exit"] = True


@register_command("help")
def cmd_help(ctx: CommandContext):
    """Show this help message."""
    ctx.console.print("[bold]Available commands:[/bold]")
    for name in sorted(COMMANDS.keys()):
        handler = COMMANDS[name]
        doc = prettify(handler.__doc__ or "")
        ctx.console.print(f"  [bold]/{name.ljust(10)}[/bold]  {doc}")


@register_command("refresh")
def cmd_refresh(ctx: CommandContext):
    """Re-ingest the current project's files into the database."""
    from yara.services.ingest import ingest_files_to_db

    if not ctx.project:
        ctx.console.print("[yellow]No active project. Open a project first.[/yellow]")
        return

    path = ctx.project["ingestion_path"]
    project_id = ctx.project["id"]
    ctx.console.print()
    with ctx.console.status("Refreshing..."):
        ingest_files_to_db(path, project_id)
    ctx.console.print(Panel("Refresh complete.", border_style="green"))
    ctx.console.print()


@register_command("home")
def cmd_home(ctx: CommandContext):
    """Return to the project selection screen."""
    ctx.signal["home"] = True


@register_command("new")
def cmd_new(ctx: CommandContext):
    """Start a new conversation in the current project."""
    ctx.conversation.reset()
    render_assistant(ctx.conversation.first_assistant_prompt())


class SlashCommandLexer(Lexer):
    def lex_document(self, document):
        def get_line(lineno):
            line = document.lines[lineno]
            if line.startswith("/"):
                # find end of the /word token
                end = line.find(" ")
                if end == -1:
                    return [("class:slash-command", line)]
                return [("class:slash-command", line[:end]), ("", line[end:])]
            return [("", line)]

        return get_line


SLASH_COMMAND_STYLE = Style.from_dict({"slash-command": "bold ansiblue"})
