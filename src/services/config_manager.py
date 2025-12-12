"""
Configuration Manager
Loads and validates domain configurations
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
import yaml
from pydantic import BaseModel, ValidationError, Field
from typing import List

logger = logging.getLogger(__name__)


class IntentConfig(BaseModel):
    """Intent configuration schema"""
    name: str
    entities: List[str] = []
    api_endpoint: Optional[str] = None
    api_method: str = "POST"
    api_headers: Dict[str, str] = {}
    response_template: Optional[str] = None
    requires_auth: bool = False


class ContextRetrievalConfig(BaseModel):
    """RAG configuration schema"""
    enabled: bool = False
    collection_name: Optional[str] = None
    top_k: int = 5
    score_threshold: float = 0.5


class DomainConfig(BaseModel):
    """Complete domain configuration schema"""
    domain_name: str
    description: Optional[str] = None
    intents: List[IntentConfig]
    context_retrieval: ContextRetrievalConfig = Field(default_factory=ContextRetrievalConfig)
    response_templates: Dict[str, str] = {}
    system_prompt: Optional[str] = None
    fallback_response: str = "I'm not sure how to help with that."
    max_turns: int = 50
    metadata: Dict[str, Any] = {}


class ConfigManager:
    """
    Manages domain configurations.
    Loads, validates, and provides access to domain-specific settings.
    """

    def __init__(self, config_dir: str = "config/domains"):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing domain config files
        """
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, DomainConfig] = {}
        
        logger.info(f"ConfigManager initialized with directory: {config_dir}")

    def load_config(self, domain_name: str, file_path: Optional[str] = None) -> bool:
        """
        Load domain configuration from file.

        Args:
            domain_name: Domain identifier
            file_path: Config file path (auto-detected if None)

        Returns:
            True if successful
        """
        try:
            if file_path is None:
                # Try both JSON and YAML
                json_path = self.config_dir / f"{domain_name}.json"
                yaml_path = self.config_dir / f"{domain_name}.yaml"
                
                if json_path.exists():
                    file_path = json_path
                elif yaml_path.exists():
                    file_path = yaml_path
                else:
                    logger.error(f"Config file not found for domain: {domain_name}")
                    return False
            else:
                file_path = Path(file_path)

            logger.info(f"Loading config from: {file_path}")

            # Load file
            with open(file_path, 'r') as f:
                if file_path.suffix == '.json':
                    config_data = json.load(f)
                elif file_path.suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {file_path.suffix}")

            # Validate with Pydantic
            config = DomainConfig(**config_data)
            
            # Store config
            self.configs[domain_name] = config
            
            logger.info(f"Loaded config for domain: {domain_name} "
                       f"({len(config.intents)} intents)")
            return True

        except ValidationError as e:
            logger.error(f"Config validation failed for {domain_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load config for {domain_name}: {e}")
            return False

    def load_all_configs(self) -> int:
        """
        Load all configuration files from config directory.

        Returns:
            Number of configs loaded
        """
        try:
            if not self.config_dir.exists():
                logger.warning(f"Config directory does not exist: {self.config_dir}")
                return 0

            loaded = 0
            for file_path in self.config_dir.glob("*.json"):
                domain_name = file_path.stem
                if self.load_config(domain_name, str(file_path)):
                    loaded += 1

            for file_path in self.config_dir.glob("*.yaml"):
                domain_name = file_path.stem
                if domain_name not in self.configs:  # Avoid duplicates
                    if self.load_config(domain_name, str(file_path)):
                        loaded += 1

            logger.info(f"Loaded {loaded} domain configurations")
            return loaded

        except Exception as e:
            logger.error(f"Failed to load configs: {e}")
            return 0

    def get_config(self, domain_name: str) -> Optional[DomainConfig]:
        """
        Get domain configuration.

        Args:
            domain_name: Domain identifier

        Returns:
            Domain configuration or None
        """
        config = self.configs.get(domain_name)
        
        if config is None:
            logger.warning(f"Config not found for domain: {domain_name}")
            # Try to load it
            if self.load_config(domain_name):
                config = self.configs.get(domain_name)
        
        return config

    def get_intent_config(
        self,
        domain_name: str,
        intent_name: str
    ) -> Optional[IntentConfig]:
        """
        Get specific intent configuration.

        Args:
            domain_name: Domain identifier
            intent_name: Intent name

        Returns:
            Intent configuration or None
        """
        config = self.get_config(domain_name)
        if not config:
            return None

        for intent in config.intents:
            if intent.name == intent_name:
                return intent

        logger.warning(f"Intent '{intent_name}' not found in domain '{domain_name}'")
        return None

    def get_system_prompt(self, domain_name: str) -> str:
        """Get system prompt for domain"""
        config = self.get_config(domain_name)
        if config and config.system_prompt:
            return config.system_prompt
        
        return "You are a helpful assistant."

    def get_response_template(
        self,
        domain_name: str,
        intent_name: str
    ) -> Optional[str]:
        """Get response template for intent"""
        config = self.get_config(domain_name)
        if not config:
            return None

        return config.response_templates.get(intent_name)

    def list_domains(self) -> List[str]:
        """Get list of loaded domains"""
        return list(self.configs.keys())

    def reload_config(self, domain_name: str) -> bool:
        """Reload configuration for domain"""
        logger.info(f"Reloading config for domain: {domain_name}")
        return self.load_config(domain_name)

    def validate_config(self, config_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration data.

        Args:
            config_data: Configuration dictionary

        Returns:
            (is_valid, error_message)
        """
        try:
            DomainConfig(**config_data)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def save_config(
        self,
        domain_name: str,
        config: DomainConfig,
        format: str = "json"
    ) -> bool:
        """
        Save configuration to file.

        Args:
            domain_name: Domain identifier
            config: Domain configuration
            format: File format (json or yaml)

        Returns:
            True if successful
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = self.config_dir / f"{domain_name}.{format}"
            
            config_dict = config.model_dump()
            
            with open(file_path, 'w') as f:
                if format == 'json':
                    json.dump(config_dict, f, indent=2)
                elif format in ['yaml', 'yml']:
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    raise ValueError(f"Unsupported format: {format}")

            # Update in-memory config
            self.configs[domain_name] = config
            
            logger.info(f"Saved config for domain: {domain_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

