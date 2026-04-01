import logging
from typing import cast

from yara.cli.chat_ui import chat_loop


class YaraLogger(logging.Logger):
    log_chunks: bool = False


def main():
    logging.basicConfig(
        filename="yara.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = cast(YaraLogger, logging.getLogger("yara"))
    logger.setLevel(logging.INFO)
    logger.log_chunks = False

    chat_loop()


if __name__ == "__main__":
    main()
