"""
Configuration management for Ghost Writer
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.getenv("GHOST_WRITER_CONFIG_PATH", "config/config.yaml")
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                return self._get_default_config()
            
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config file {self.config_path}: {e}")
            logger.info("Falling back to default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Provide default configuration values"""
        return {
            "database": {
                "path": "data/database/ghost_writer.db"
            },
            "ocr": {
                "default_provider": "tesseract",
                "providers": {
                    "tesseract": {
                        "config": "--oem 3 --psm 6",
                        "confidence_threshold": 60
                    },
                    "cloud_vision": {
                        "confidence_threshold": 70
                    },
                    "hybrid": {
                        "low_confidence_threshold": 75,
                        "cost_limit_per_day": 5.00,
                        "prefer_local": True
                    }
                }
            },
            "embeddings": {
                "model_name": "all-MiniLM-L6-v2",
                "dimension": 384
            },
            "faiss": {
                "index_path": "data/faiss_index/"
            },
            "llm": {
                "model": "llama3:latest",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "style": {
                "corpus_path": "data/style_corpus/",
                "min_examples": 3
            },
            "processing": {
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "logging": {
                "level": "INFO"
            }
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        # Database path override
        if db_path := os.getenv("GHOST_WRITER_DB_PATH"):
            self._config["database"]["path"] = db_path
        
        # Logging level override
        if log_level := os.getenv("GHOST_WRITER_LOG_LEVEL"):
            self._config["logging"]["level"] = log_level.upper()
        
        # Daily budget override
        if budget := os.getenv("GHOST_WRITER_DAILY_BUDGET"):
            try:
                self._config["ocr"]["providers"]["hybrid"]["cost_limit_per_day"] = float(budget)
            except ValueError:
                logger.warning(f"Invalid budget value: {budget}")
        
        # Tesseract command override
        if tesseract_cmd := os.getenv("TESSERACT_CMD"):
            self._config["tesseract_cmd"] = tesseract_cmd
        
        # Ollama host override
        if ollama_host := os.getenv("OLLAMA_HOST"):
            self._config["ollama_host"] = ollama_host

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.path')"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._config.get("database", {})

    def get_ocr_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get OCR configuration for specific provider or default"""
        ocr_config = self._config.get("ocr", {})
        
        if provider is None:
            provider = ocr_config.get("default_provider", "tesseract")
        
        provider_config = ocr_config.get("providers", {}).get(provider, {})
        
        return {
            "provider": provider,
            **provider_config
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """Get embedding configuration"""
        return self._config.get("embeddings", {})

    def get_faiss_config(self) -> Dict[str, Any]:
        """Get FAISS configuration"""
        return self._config.get("faiss", {})

    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config.get("llm", {})

    def get_style_config(self) -> Dict[str, Any]:
        """Get style corpus configuration"""
        return self._config.get("style", {})

    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self._config.get("processing", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._config.get("logging", {})

    def get_cost_config(self) -> Dict[str, Any]:
        """Get cost monitoring configuration"""
        return self._config.get("cost_monitoring", {})

    def get_search_config(self) -> Dict[str, Any]:
        """Get search configuration"""
        return self._config.get("search", {})

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return (
            os.getenv("GHOST_WRITER_DEBUG", "false").lower() == "true" or
            self.get("logging.level") == "DEBUG"
        )

    def validate_config(self) -> bool:
        """Validate configuration values"""
        try:
            # Check required paths exist or can be created
            db_path = Path(self.get("database.path"))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            faiss_path = Path(self.get("faiss.index_path"))
            faiss_path.mkdir(parents=True, exist_ok=True)
            
            style_path = Path(self.get("style.corpus_path"))
            style_path.mkdir(parents=True, exist_ok=True)
            
            # Validate numeric values
            assert isinstance(self.get("ocr.providers.hybrid.cost_limit_per_day"), (int, float))
            assert isinstance(self.get("embeddings.dimension"), int)
            assert isinstance(self.get("llm.temperature"), (int, float))
            assert 0 <= self.get("llm.temperature") <= 1
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def save_config(self, output_path: Optional[str] = None) -> bool:
        """Save current configuration to YAML file"""
        try:
            if output_path is None:
                path_obj = self.config_path
            else:
                path_obj = Path(output_path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path_obj, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {path_obj}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"Config(path={self.config_path}, provider={self.get('ocr.default_provider')})"

    def __repr__(self) -> str:
        return self.__str__()


# Global configuration instance
config = Config()