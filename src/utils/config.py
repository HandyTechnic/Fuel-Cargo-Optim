"""
Configuration module for the fuel and cargo optimization system.

This module handles configuration settings, including default values and user overrides.
It provides functions to load, validate, and access configuration settings from various sources.
"""
from typing import Dict, Any, Optional, Union
import os
import json
import yaml


class Config:
    """
    Configuration manager for the fuel and cargo optimization system.
    
    This class handles loading, validating, and accessing configuration settings
    from various sources, including files and user inputs.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to a configuration file
        """
        # Default configuration
        self.defaults = {
            "aircraft": {
                "type": "A330-203",
                "owe": 120310,
                "variable_load": 0,
                "mtow": 233000,
                "mlw": 182000,
                "mzfw": 170000,
                "fuel_capacity": 109186,
                "fuel_density": 0.785,
                "passenger_capacity": 264,
                "std_pax_weight": 102,
                "additional_burn_factor": 0.0001
            },
            "routes": {
                "MLE-TFU": {
                    "distance": 2662,
                    "flight_time": 6.08,
                    "flight_level": 380,
                    "wind_component": -22,
                    "min_trip_fuel": 32841,
                    "contingency_fuel_pct": 0.05,
                    "reserve_fuel": 2500,
                    "fuel_price_origin": 0.9974,
                    "fuel_price_dest": 0.6875,
                    "cargo_revenue_rate": 2.6
                },
                "MLE-PEK": {
                    "distance": 3800,
                    "flight_time": 8.5,
                    "flight_level": 380,
                    "wind_component": -25,
                    "min_trip_fuel": 45000,
                    "contingency_fuel_pct": 0.05,
                    "reserve_fuel": 2500,
                    "fuel_price_origin": 0.9974,
                    "fuel_price_dest": 0.6853,
                    "cargo_revenue_rate": 2.6
                },
                "MLE-PVG": {
                    "distance": 4000,
                    "flight_time": 9.0,
                    "flight_level": 380,
                    "wind_component": -25,
                    "min_trip_fuel": 47000,
                    "contingency_fuel_pct": 0.05,
                    "reserve_fuel": 2500,
                    "fuel_price_origin": 0.9974,
                    "fuel_price_dest": 0.5914,
                    "cargo_revenue_rate": 2.6
                }
            },
            "optimization": {
                "method": "linear",
                "cargo_steps": 20,
                "fuel_steps": 20
            },
            "logging": {
                "level": "INFO",
                "file": "fuel_cargo_optim.log",
                "console": True
            }
        }
        
        # User configuration
        self.user_config = {}
        
        # User overrides for specific values
        self.overrides = {}
        
        # Load config file if provided
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        # Determine file format from extension
        _, ext = os.path.splitext(config_file)
        
        try:
            with open(config_file, 'r') as f:
                if ext.lower() == '.json':
                    self.user_config = json.load(f)
                elif ext.lower() in ['.yaml', '.yml']:
                    self.user_config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {ext}")
        except Exception as e:
            raise ValueError(f"Failed to parse configuration file: {str(e)}")
        
        # Validate the loaded configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate the loaded configuration.
        
        Raises:
            ValueError: If the configuration is invalid
        """
        # Placeholder for validation logic
        # This would check required fields, data types, and value ranges
        pass
    
    def set_override(self, key: str, value: Any) -> None:
        """
        Set a user override for a specific configuration value.
        
        Args:
            key: Configuration key (dot notation for nested keys)
            value: Override value
        """
        self.overrides[key] = value
    
    def set_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Set multiple user overrides.
        
        Args:
            overrides: Dictionary of override values
        """
        self.overrides.update(overrides)
    
    def clear_overrides(self) -> None:
        """Clear all user overrides."""
        self.overrides = {}
    
    def _get_nested_value(self, config_dict: Dict[str, Any], key_path: list) -> Any:
        """
        Get a nested value from a dictionary.
        
        Args:
            config_dict: Dictionary to search in
            key_path: List of keys to navigate the nested structure
        
        Returns:
            Any: The value if found, None otherwise
        """
        current = config_dict
        for key in key_path:
            if key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, config_dict: Dict[str, Any], key_path: list, value: Any) -> None:
        """
        Set a nested value in a dictionary.
        
        Args:
            config_dict: Dictionary to modify
            key_path: List of keys to navigate the nested structure
            value: Value to set
        """
        current = config_dict
        for key in key_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[key_path[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Order of precedence:
        1. User overrides
        2. User configuration file
        3. Default configuration
        4. Provided default value
        
        Args:
            key: Configuration key (dot notation for nested keys)
            default: Default value if key is not found
        
        Returns:
            Any: The configuration value
        """
        # Check user overrides first
        if key in self.overrides:
            return self.overrides[key]
        
        # Split the key into path components
        key_path = key.split('.')
        
        # Check user configuration
        user_value = self._get_nested_value(self.user_config, key_path)
        if user_value is not None:
            return user_value
        
        # Check default configuration
        default_value = self._get_nested_value(self.defaults, key_path)
        if default_value is not None:
            return default_value
        
        # Return provided default value
        return default
    
    def get_aircraft_config(self) -> Dict[str, Any]:
        """
        Get the aircraft configuration.
        
        Returns:
            Dict[str, Any]: Aircraft configuration
        """
        return self.get('aircraft', {})
    
    def get_route_config(self, route_code: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific route.
        
        Args:
            route_code: Route code (e.g., 'MLE-TFU')
        
        Returns:
            Dict[str, Any]: Route configuration
        """
        return self.get(f'routes.{route_code}', {})
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """
        Get the optimization configuration.
        
        Returns:
            Dict[str, Any]: Optimization configuration
        """
        return self.get('optimization', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get the logging configuration.
        
        Returns:
            Dict[str, Any]: Logging configuration
        """
        return self.get('logging', {})
    
    def save_config(self, file_path: str) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            file_path: Path to save the configuration file
        
        Raises:
            ValueError: If the file format is unsupported
        """
        # Merge defaults, user_config, and overrides
        merged_config = self.defaults.copy()
        
        # Update with user_config
        for key, value in self.user_config.items():
            if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                merged_config[key].update(value)
            else:
                merged_config[key] = value
        
        # Apply overrides
        for key, value in self.overrides.items():
            key_path = key.split('.')
            self._set_nested_value(merged_config, key_path, value)
        
        # Determine file format from extension
        _, ext = os.path.splitext(file_path)
        
        try:
            with open(file_path, 'w') as f:
                if ext.lower() == '.json':
                    json.dump(merged_config, f, indent=2)
                elif ext.lower() in ['.yaml', '.yml']:
                    yaml.dump(merged_config, f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {ext}")
        except Exception as e:
            raise ValueError(f"Failed to save configuration file: {str(e)}")


# Default configuration instance
_config = Config()

def load_config(config_file: str) -> None:
    """
    Load configuration from a file.
    
    Args:
        config_file: Path to the configuration file
    """
    global _config
    _config.load_config(config_file)

def get_config() -> Config:
    """
    Get the default configuration instance.
    
    Returns:
        Config: Default configuration instance
    """
    return _config

def set_override(key: str, value: Any) -> None:
    """
    Set a user override for a specific configuration value.
    
    Args:
        key: Configuration key
        value: Override value
    """
    _config.set_override(key, value)

def set_overrides(overrides: Dict[str, Any]) -> None:
    """
    Set multiple user overrides.
    
    Args:
        overrides: Dictionary of override values
    """
    _config.set_overrides(overrides)

def get(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key is not found
    
    Returns:
        Any: The configuration value
    """
    return _config.get(key, default)