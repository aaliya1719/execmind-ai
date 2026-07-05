"""Configuration helpers for environment-based settings.

This module will centralize loading of secrets and application settings.
"""

import os
from dotenv import load_dotenv


load_dotenv()


def get_setting(key, default=None):
    """Return a configuration value from the environment."""
    return os.getenv(key, default)
