"""
Strategy Configuration - Load and validate config files
"""

import json
from pathlib import Path
from typing import Dict, Any


class StrategyConfig:
    """
    Load and validate strategy configuration.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to config JSON file (optional)
        """
        self.config = None
        if config_path:
            self.load(config_path)
    
    def load(self, config_path):
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            dict: Configuration dict
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.validate()
        return self.config
    
    def validate(self):
        """
        Validate configuration structure.
        
        Raises:
            ValueError: If config is invalid
        """
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        # TODO: Add validation logic
        # - Check required fields
        # - Validate value ranges
        # - Check data file exists
    
    def get(self, key, default=None):
        """
        Get config value by key (supports nested keys with dot notation).
        
        Args:
            key: Config key (e.g., "strategy.rsi_period")
            default: Default value if key not found
            
        Returns:
            Any: Config value
        """
        if not self.config:
            return default
        
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value



