"""Configuration helpers for environment-based settings.

This module centralizes loading of secrets and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Sensible defaults
DEFAULT_APP_NAME = "ExecMind AI"
DEFAULT_MODEL_NAME = "gemini-2.5-flash"
DEFAULT_DEBUG = False

def get_setting(key, default=None):
    """Return a configuration value from the environment."""
    return os.getenv(key, default)

def get_app_name() -> str:
    """Return the application name, defaulting to 'ExecMind AI'."""
    return get_setting("APP_NAME", DEFAULT_APP_NAME)

def get_model_name() -> str:
    """Return the target Gemini model name, defaulting to 'gemini-2.5-flash'."""
    return get_setting("MODEL_NAME", DEFAULT_MODEL_NAME)

def is_debug() -> bool:
    """Return True if DEBUG mode is enabled, False otherwise."""
    val = get_setting("DEBUG")
    if val is None:
        return DEFAULT_DEBUG
    return str(val).lower() in ("true", "1", "yes", "on")

def get_google_api_key() -> str:
    """Return the Google API key. Raises ValueError if not configured."""
    key = get_setting("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please set it in your .env file."
        )
    return key

def get_google_cloud_project() -> str:
    """Return the Google Cloud Project ID. Raises ValueError if not configured."""
    project = get_setting("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT is not set. Please set it in your .env file."
        )
    return project

def validate_config() -> None:
    """Validate that all required configuration settings are present."""
    errors = []
    
    if not get_setting("GOOGLE_API_KEY"):
        errors.append("GOOGLE_API_KEY is missing.")
        
    if not get_setting("GOOGLE_CLOUD_PROJECT"):
        errors.append("GOOGLE_CLOUD_PROJECT is missing.")
        
    if errors:
        raise ValueError(
            "Configuration Validation Failed:\n" + "\n".join(f"- {err}" for err in errors)
        )

