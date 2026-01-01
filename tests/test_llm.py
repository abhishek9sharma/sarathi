from unittest.mock import MagicMock, patch

import pytest

from sarathi.config.config_manager import ConfigManager
from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.call_llm import call_llm_model, get_agent_config


# Mock ConfigManager to return predictable results
@pytest.fixture
def mock_config():
    with patch("sarathi.llm.call_llm.config") as mock:
        with patch("sarathi.config.config_manager.config", mock):
            # Default behavior
            mock.get_agent_config.return_value = {}
            mock.get_provider_config.return_value = {
                "base_url": "https://api.openai.com/v1",
                "api_key": "test_key",
            }

            # Make .get() return 30 for timeout, but None for others (like prompts)
            mock.get.side_effect = lambda key, default=None: (
                30 if key == "core.timeout" else default
            )
            yield mock


def test_get_agent_config(mock_config):
    # Test legacy mapping
    mock_config.get_agent_config.return_value = {"model": "legacy_model"}
    assert get_agent_config("autocommit") == {"model": "legacy_model"}
    mock_config.get_agent_config.assert_called_with("commit_generator")

    # Test normal lookup
    assert get_agent_config("chat") == {"model": "legacy_model"}
    mock_config.get_agent_config.assert_called_with("chat")


@patch("httpx.Client")
def test_call_llm_success_text(mock_client_class, mock_config):
    # Setup mock client behavior for context manager
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello World"}}]
    }
    mock_client.post.return_value = mock_response

    prompt_info = {"model": "default-model", "system_msg": "You are helpful"}

    # Call function
    result = call_llm_model(prompt_info, "Hi", resp_type="text", agent_name="chat")

    assert result == "Hello World"

    # Verify request structure
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer test_key"
    assert kwargs["json"]["messages"][0]["content"] == "You are helpful"
    assert kwargs["json"]["messages"][1]["content"] == "Hi"


@patch("httpx.Client")
def test_call_llm_override_config(mock_client_class, mock_config):
    mock_client = mock_client_class.return_value.__enter__.return_value
    # Setup specific agent config
    mock_config.get_agent_config.return_value = {
        "model": "super-model",
        "system_prompt": "Override Prompt",
        "temperature": 0.9,
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_client.post.return_value = mock_response

    call_llm_model({}, "Hi", agent_name="test_agent")

    # Verify overrides
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    body = kwargs["json"]
    assert body["model"] == "super-model"
    assert body["temperature"] == 0.9
    assert body["messages"][0]["content"] == "Override Prompt"


@patch("httpx.Client")
def test_call_llm_failure(mock_client_class, mock_config):
    mock_client = mock_client_class.return_value.__enter__.return_value
    # Setup exception
    import httpx

    mock_client.post.side_effect = httpx.HTTPError("Connection Error")

    result = call_llm_model({}, "Hi")

    assert isinstance(result, dict)
    assert "Error" in result
    assert "Connection Error" in result["Error"]


@patch("httpx.Client")
def test_llm_respects_verify_ssl(mock_client_class, mock_config):
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_config.get.side_effect = lambda key, default=None: (
        False
        if key == "core.verify_ssl"
        else (30 if key == "core.timeout" else default)
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    mock_client.post.return_value = mock_response

    call_llm_model({"model": "test"}, "hi")

    # Check Client initialization
    mock_client_class.assert_called_with(timeout=30, verify=False)


@patch("httpx.Client")
def test_agent_engine_respects_verify_ssl(mock_client_class, mock_config):
    mock_client = mock_client_class.return_value.__enter__.return_value
    mock_config.get.side_effect = lambda key, default=None: (
        False
        if key == "core.verify_ssl"
        else (30 if key == "core.timeout" else default)
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    mock_client.post.return_value = mock_response

    agent = AgentEngine("chat", system_prompt="test")
    agent._call_llm()

    mock_client_class.assert_called_with(timeout=30, verify=False)


@patch("httpx.Client")
@patch("time.sleep")
def test_call_llm_retries_on_429(mock_sleep, mock_client_class, mock_config):
    mock_client = mock_client_class.return_value.__enter__.return_value
    # first two are 429, third is success
    mock_429 = MagicMock()
    mock_429.status_code = 429

    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {"choices": [{"message": {"content": "Success"}}]}

    mock_client.post.side_effect = [mock_429, mock_429, mock_success]

    mock_config.get.side_effect = lambda key, default=None: (
        3 if key == "core.llm_retries" else (30 if key == "core.timeout" else default)
    )

    result = call_llm_model({}, "Hi", resp_type="text")

    assert result == "Success"
    assert mock_client.post.call_count == 3
    assert mock_sleep.call_count == 2


@patch("sarathi.llm.agent_engine.AgentEngine._call_llm_stream")
def test_agent_engine_safety_limit(mock_call_stream):
    # Mock LLM always returning a tool call
    mock_call_stream.return_value = [
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "1",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"file_path": "test.py"}',
                                },
                            }
                        ]
                    }
                }
            ]
        }
    ]

    # Mock registry to avoid actual tool execution
    with patch("sarathi.llm.tools.registry.call_tool") as mock_tool:
        mock_tool.return_value = "content"
        # Avoid permission check
        agent = AgentEngine("chat")
        # Collect tokens from stream
        tokens = list(agent.run_stream("Infinite loop please"))
        result = "".join([t for t in tokens if isinstance(t, str)])

        assert "Safety Limit reached" in result
        assert mock_call_stream.call_count == 10
