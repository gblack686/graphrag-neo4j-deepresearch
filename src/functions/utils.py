"""
Utility functions for general purpose operations.
"""
from typing import Any, Dict, List
import logging
import json

def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Failed to load config file: {str(e)}")

# Add more utility functions here 