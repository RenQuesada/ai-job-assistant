import logging
import os
import sys

def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose or os.environ.get("LOG_LEVEL", "").lower() == "debug" else logging.WARNING

    logger = logging.getLogger("aip444")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[DEBUG] %(message)s"))
    logger.addHandler(handler)

    return logger

logger = setup_logging()