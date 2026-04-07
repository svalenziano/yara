import logging

from phoenix.otel import register

from yara.cli.chat_ui import chat_loop
from yara.cli.startup_ui import startup_loop


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("yara.log"),  # write logs to file
            # stream logs to STDOUT
            # uncommenting the following line may break the terminal UI
            # logging.StreamHandler(),
        ],
    )
    register(project_name="yara", auto_instrument=True)

    while True:
        project_id = startup_loop()
        result = chat_loop(project_id=project_id)
        if result != "home":
            break


if __name__ == "__main__":
    main()
