import os
from typing import Any, Dict

def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        'github_token': os.getenv('GITHUB_TOKEN'),
        'config_path': os.getenv('CONFIG_PATH', 'config/settings.yaml')
    }
