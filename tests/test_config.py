import sys
import os

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock the environment variables for testing
os.environ["APP_NAME"] = "Test ExecMind"
os.environ["DEBUG"] = "true"
os.environ["GOOGLE_API_KEY"] = "mock-api-key"
os.environ["GOOGLE_CLOUD_PROJECT"] = "mock-project-id"

from app.utils.config import (
    get_app_name,
    get_model_name,
    is_debug,
    get_google_api_key,
    get_google_cloud_project,
    validate_config
)

def test_config():
    print("Testing config values:")
    print(f"App Name: {get_app_name()} (Expected: Test ExecMind)")
    print(f"Model Name: {get_model_name()} (Expected: gemini-2.5-flash)")
    print(f"Is Debug: {is_debug()} (Expected: True)")
    print(f"API Key: {get_google_api_key()} (Expected: mock-api-key)")
    print(f"Project ID: {get_google_cloud_project()} (Expected: mock-project-id)")
    
    # Run validation
    validate_config()
    print("Validation passed successfully!")
    
    # Check default model
    if get_model_name() == "gemini-2.5-flash":
        print("Default model name matches.")
        
    # Test validation error
    os.environ["GOOGLE_API_KEY"] = ""
    try:
        validate_config()
        print("ERROR: validation should have failed.")
    except ValueError as e:
        print(f"Expected failure caught successfully: {e}")

if __name__ == "__main__":
    test_config()
