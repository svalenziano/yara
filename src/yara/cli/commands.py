from dataclasses import dataclass, field
from typing import Callable

from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from rich.console import Console

from yara.services.conversation import Conversation

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
    ctx.signal["exit"] = True


@register_command("help")
def cmd_help(ctx: CommandContext):
    names = sorted(COMMANDS.keys())
    ctx.console.print("[bold]Available commands:[/bold]")
    for name in names:
        ctx.console.print(f"  /{name}")


@register_command("new")
def cmd_new(ctx: CommandContext):
    from yara.cli.chat_ui import render_assistant  # lazy import to avoid circular

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
