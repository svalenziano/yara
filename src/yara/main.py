import logging

from yara.cli.chat_ui import chat_loop


def main():
    logging.basicConfig(
        filename="yara.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("yara").setLevel(logging.DEBUG)

    chat_loop()


if __name__ == "__main__":
    main()
