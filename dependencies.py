"""Module that stores widely used dependencies."""

import pgn_parser
import logging
import os

parser = pgn_parser.ChessGame()


def set_logging():
    level = os.environ.get("LOGGING", "INFO")
    handler = logging.FileHandler('./logs/myapp.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)
    if level == "INFO":
        logger.setLevel(logging.INFO)
    elif level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    return logger

LOGGER = set_logging()
