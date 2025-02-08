import logging
import json
import os

def setup_logging(log_file="app.log"):
    """Set up logging configuration."""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Logging setup complete.")

def load_json(file_path):
    """Load JSON data from a file."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    """Save data as JSON to a file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def validate_config(config, required_keys):
    """Validate if all required keys exist in a configuration dictionary."""
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing configuration keys: {missing_keys}")
    return True

# Example usage
if __name__ == "__main__":
    setup_logging()
    sample_config = {"api_key": "12345", "timeout": 30}
    validate_config(sample_config, ["api_key", "timeout"])
