import os
import yaml
from typing import Dict, Any


class Config:
    """Centralized configuration management."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../config/settings.yaml')
        self.config_path = config_path
        self._config = None

    @property
    def config(self) -> Dict[str, Any]:
        if self._config is None:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        return self._config

    def get_database_url(self) -> str:
        """Get database URL based on config."""
        db_config = self.config['database']
        db_type = db_config['type']

        if db_type == 'sqlite':
            db_path = db_config['path']
            os.makedirs(db_path, exist_ok=True)
            return f'sqlite:///{db_path}/database.db'
        elif db_type == 'postgresql':
            return db_config['connection_string']
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def get_api_config(self) -> Dict[str, Any]:
        return self.config.get('api', {})

    def get_scheduler_config(self) -> Dict[str, Any]:
        return self.config.get('scheduler', {})

    def get_logging_config(self) -> Dict[str, Any]:
        return self.config.get('logging', {})

    def get_tickers(self) -> list[str]:
        return self.config.get('tickers', [])


# Singleton instance
config = Config()