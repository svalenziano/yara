from rich.console import Console

console = Console()
# console.color_system = "auto"


def subtle(text):
    console.print(text, style="bright_black")


if __name__ == "__main__":
    subtle("Hello world!")
