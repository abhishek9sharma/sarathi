import os
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "core": {"provider": "openai", "timeout": 30},
    "providers": {
        "openai": {"base_url": "https://api.openai.com/v1"},
        "ollama": {"base_url": "http://localhost:11434", "model": "llama3"},
    },
    "agents": {
        "commit_generator": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "system_prompt": None,
        },
        "qahelper": {
            "provider": "openai",
            "model": "gpt-4o-mini",
        },
        "update_docstrings": {
            "provider": "openai",
            "model": "gpt-4o-mini",
        },
        "code_editor": {
            "provider": "openai",
            "model": "gpt-4o",  # Use more capable model for code editing
            "temperature": 0.3,  # Lower temperature for more deterministic code
        },
    },
}


import copy

class ConfigManager:
    def __init__(self):
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self.load_configs()

    def load_configs(self, custom_path=None):
        """Loads configuration. If custom_path is provided, it uses that.
        Otherwise it defaults to the global ~/.sarathi/config.yaml.
        """
        # Always start with defaults
        self._config = copy.deepcopy(DEFAULT_CONFIG)

        if custom_path:
            config_path = Path(custom_path)
            if config_path.exists():
                self._merge_from_file(config_path)
            else:
                print(f"Warning: Configuration file not found at {custom_path}")
        else:
            # User Global Config (~/.sarathi/config.yaml)
            global_config_path = Path.home() / ".sarathi" / "config.yaml"
            if global_config_path.exists():
                self._merge_from_file(global_config_path)

        # Environment Variables (apply last for secrets)
        self._apply_env_overrides()

    def _merge_from_file(self, path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    # Security: Enforce that api_key cannot be loaded from yaml
                    if "providers" in data:
                        for provider in data["providers"].values():
                            if "api_key" in provider:
                                provider.pop("api_key", None)
                                print(
                                    "Warning: 'api_key' in configuration file is ignored for security. Use environment variables."
                                )

                    self._deep_merge(self._config, data)
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")

    def _deep_merge(self, base, update):
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        # Allow legacy env vars to override the active provider config
        api_key = os.getenv("SARATHI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            # We don't know which provider they mean if they just set OPENAI_API_KEY,
            # but historically it meant OpenAI.
            self._config["providers"]["openai"]["api_key"] = api_key

        model = os.getenv("OPENAI_MODEL_NAME")
        if model:
            # This is tricky as we don't know which agent checking the env var was meant for.
            # In legacy sarathi, it applied to everything.
            self._config["agents"]["commit_generator"]["model"] = model
            self._config["agents"]["qahelper"]["model"] = model

    def get(self, key_path, default=None):
        """Get a value using dot notation e.g. 'agents.commit_generator.model'"""
        keys = key_path.split(".")
        curr = self._config
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr

    def get_agent_config(self, agent_name):
        return self._config.get("agents", {}).get(agent_name, {})

    def get_provider_config(self, provider_name):
        return self._config.get("providers", {}).get(provider_name, {})


# Singleton instance
config = ConfigManager()
