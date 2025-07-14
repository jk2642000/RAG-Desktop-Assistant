import json
import os
from typing import Dict, Any
from PyQt5.QtCore import QSettings

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = QSettings("RAG_Assistant", "Desktop")
        self.defaults = {
            'window': {
                'width': 1200,
                'height': 800,
                'x': 100,
                'y': 100
            },
            'splitter': {
                'left_width': 300,
                'right_width': 900
            },
            'ui': {
                'theme': 'light',
                'font_size': 12
            },
            'memory': {
                'max_memory_mb': 2048,
                'lazy_loading': True
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file and QSettings"""
        config = self.defaults.copy()
        
        # Load from JSON file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(config, file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        # Load UI settings from QSettings
        config['window']['width'] = self.settings.value('window/width', config['window']['width'], type=int)
        config['window']['height'] = self.settings.value('window/height', config['window']['height'], type=int)
        config['window']['x'] = self.settings.value('window/x', config['window']['x'], type=int)
        config['window']['y'] = self.settings.value('window/y', config['window']['y'], type=int)
        config['splitter']['left_width'] = self.settings.value('splitter/left_width', config['splitter']['left_width'], type=int)
        config['splitter']['right_width'] = self.settings.value('splitter/right_width', config['splitter']['right_width'], type=int)
        
        return config
    
    def save_config(self):
        """Save configuration to file and QSettings"""
        # Save to JSON file
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")
        
        # Save UI settings to QSettings
        self.settings.setValue('window/width', self.config['window']['width'])
        self.settings.setValue('window/height', self.config['window']['height'])
        self.settings.setValue('window/x', self.config['window']['x'])
        self.settings.setValue('window/y', self.config['window']['y'])
        self.settings.setValue('splitter/left_width', self.config['splitter']['left_width'])
        self.settings.setValue('splitter/right_width', self.config['splitter']['right_width'])
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _merge_config(self, base: Dict, update: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

# Global config manager
config_manager = ConfigManager()