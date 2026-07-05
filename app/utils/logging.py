"""Application logging helpers.

This module will provide consistent logging for agents and UI events.
"""

import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_logger(name):
    """Return a configured logger instance."""
    return logging.getLogger(name)
