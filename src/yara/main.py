from phoenix.otel import register

from yara.cli.chat_ui import chat_loop


def main():
    register(project_name="yara", auto_instrument=True)

    chat_loop()


if __name__ == "__main__":
    main()
