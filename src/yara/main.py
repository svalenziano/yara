import logging

from phoenix.otel import register

from yara.cli.chat_ui import chat_loop


def main():
    logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
    register(project_name="yara", auto_instrument=True)

    chat_loop()


if __name__ == "__main__":
    main()
