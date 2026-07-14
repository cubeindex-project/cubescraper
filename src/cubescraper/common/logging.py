import contextvars
import logging

from rich.logging import RichHandler

log_context = contextvars.ContextVar("log_context", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.context = log_context.get()
        return True


def setup_logging(rich_tracebacks: bool = True):
    handler = RichHandler(rich_tracebacks=rich_tracebacks)
    handler.addFilter(ContextFilter())

    logging.basicConfig(
        level=logging.WARNING,
        format="[%(context)s] [%(funcName)s] %(message)s",
        datefmt="[%H:%M:%S]",
        handlers=[handler],
        force=True,
    )

    logging.getLogger("cubescraper").setLevel(logging.DEBUG)
