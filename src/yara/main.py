import logging

from phoenix.otel import register

from yara.cli.chat_ui import chat_loop


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
        handlers=[
            # logging.StreamHandler(),          # stream logs to STDOUT
            logging.FileHandler("yara.log"),  # write logs to file
        ],
    )
    register(project_name="yara", auto_instrument=True)

    chat_loop()


if __name__ == "__main__":
    main()
