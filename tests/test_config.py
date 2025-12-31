import pytest
from unittest.mock import patch, mock_open
import os
from sarathi.config.config_manager import ConfigManager

# Helper to reset the singleton's state if testing ConfigManager in isolation usually 
# requires it, although here we instantiate fresh classes.

@pytest.fixture
def clean_env():
    # Save original env
    old_env = os.environ.copy()
    # Clear relevant keys
    for key in ["OPENAI_API_KEY", "SARATHI_OPENAI_API_KEY", "OPENAI_ENDPOINT_URL", "OPENAI_MODEL_NAME"]:
        if key in os.environ:
            del os.environ[key]
    yield
    # Restore env
    os.environ.clear()
    os.environ.update(old_env)

def test_default_config(clean_env):
    # Use patch.object to prevent _merge_from_file from doing anything
    # This effectively simulates "no config files found" regardless of filesystem
    with patch.object(ConfigManager, "_merge_from_file") as mock_merge:
        cm = ConfigManager()
        assert cm.get("core.provider") == "openai"
        assert cm.get("providers.openai.base_url") == "https://api.openai.com/v1"
        # Ensure api_key is NOT present by default (removed for security)
        assert cm.get("providers.openai.api_key") is None
        # Ensure prompts are None in default object
        assert cm.get("agents.commit_generator.system_prompt") is None

def test_config_file_loading_and_security(clean_env):
    yaml_content = """
    core:
        timeout: 99
    providers:
        openai:
            api_key: "BAD_KEY"
            base_url: "https://custom.url"
    agents:
        qahelper:
            system_prompt: "I am a test prompt"
    """
    
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        with patch("os.path.exists", return_value=True): # For pathlib
             with patch("pathlib.Path.exists", return_value=True):
                cm = ConfigManager()
                
                # Check normal overrides
                assert cm.get("core.timeout") == 99
                assert cm.get("providers.openai.base_url") == "https://custom.url"
                assert cm.get("agents.qahelper.system_prompt") == "I am a test prompt"
                
                # Check SECURITY Feature: api_key should be stripped
                assert cm.get("providers.openai.api_key") is None

def test_env_var_overrides(clean_env):
    os.environ["OPENAI_API_KEY"] = "env-key"
    os.environ["OPENAI_MODEL_NAME"] = "env-model"
    
    cm = ConfigManager()
    
    # API Key should be injected from env
    assert cm.get("providers.openai.api_key") == "env-key"
    
    # Model should update agents
    assert cm.get("agents.commit_generator.model") == "env-model"
    assert cm.get("agents.qahelper.model") == "env-model"

def test_config_manager_set_and_save():
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("pathlib.Path.exists", return_value=True):
            cm = ConfigManager()
            cm.set("core.verify_ssl", False, save=True)
            assert cm.get("core.verify_ssl") is False
            mock_file.assert_called()

def test_config_manager_update_agent_model():
    cm = ConfigManager()
    cm.update_agent_model("chat", "gpt-4o", save=False)
    assert cm.get("agents.chat.model") == "gpt-4o"
