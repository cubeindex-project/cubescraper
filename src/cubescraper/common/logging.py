import logging

from rich.logging import RichHandler


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%H:%M:%S]",
        handlers=[RichHandler(rich_tracebacks=True)],
        force=True,
    )
