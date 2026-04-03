from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from yara.cli.colors import console


def assistant_panel(text: str) -> Panel:
    return Panel(Markdown(text), title="Assistant", border_style="bright_black")


def home_panel(content: str) -> Panel:
    return Panel(content, title="Yara — Select a Project", border_style="bright_black", padding=(1, 3))


def loading_panel() -> Panel:
    return Panel(Spinner("dots"), title="Assistant", border_style="bright_black")


def render_assistant(text):
    console.print(assistant_panel(text))

def render_home(content: str):
    whitespace(10)
    console.print(home_panel(content))


def whitespace(n: int):
    for i in range(n):
        console.print("")
        

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
