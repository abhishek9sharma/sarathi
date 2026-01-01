from unittest.mock import MagicMock, patch

import pytest

from sarathi.cli.chat_cli import ChatSession


@pytest.fixture
def mock_agent_engine():
    with patch("sarathi.cli.chat_cli.AgentEngine") as mock:
        yield mock


def test_chat_session_init(mock_agent_engine):
    """Test ChatSession initialization"""
    session = ChatSession()
    assert session.running is True
    assert session.agent is not None
    mock_agent_engine.assert_called_once()

    # Verify prompt hydration
    call_args = mock_agent_engine.call_args
    assert "system_prompt" in call_args[1]
    assert "Current Directory" in call_args[1]["system_prompt"]


def test_handle_slash_commands(mock_agent_engine, capsys):
    """Test slash commands processing"""
    session = ChatSession()

    # Mock agent messages for history test
    session.agent.messages = [
        {"role": "system", "content": "SysPrompt"},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]

    # Test /history
    session.handle_slash_command("/history")
    captured = capsys.readouterr()
    assert "[system]: SysPrompt" in captured.out
    assert "[user]: Hi" in captured.out

    # Test /clear
    session.handle_slash_command("/clear")
    assert len(session.agent.messages) == 1
    assert session.agent.messages[0]["content"] == "SysPrompt"

    # Test /exit
    session.handle_slash_command("/exit")
    assert session.running is False


@patch("builtins.input")
def test_chat_loop_exit(mock_input, mock_agent_engine):
    """Test that the chat loop exits on /exit"""
    mock_input.return_value = "/exit"

    session = ChatSession()
    session.start()

    assert session.running is False


@patch("builtins.input")
def test_chat_loop_run_agent(mock_input, mock_agent_engine):
    """Test that valid input triggers agent run"""
    # First input is valid, second is exit to break loop
    mock_input.side_effect = ["Hello AI", "/exit"]

    # Config mock agent instance
    mock_instance = mock_agent_engine.return_value
    mock_instance.run_stream.return_value = iter(["AI ", "Response"])

    session = ChatSession()
    session.start()

    # Verify agent.run_stream was called with user input
    mock_instance.run_stream.assert_called_with("Hello AI")


def test_file_injection(mock_agent_engine, tmp_path):
    """Test @file syntax injection"""
    # Create temp file
    f = tmp_path / "test.txt"
    f.write_text("Secret Content")

    session = ChatSession()

    # Process input with @file
    processed = session._process_at_mentions(f"Analyze @{f}")

    assert "Secret Content" in processed
    assert f"Context from {f}" in processed


@patch("questionary.select")
def test_permission_callback(mock_select, mock_agent_engine):
    """Test permission logic"""
    session = ChatSession()

    # Mocking the questionary chain: select(...).ask()
    mock_ask = MagicMock()
    mock_select.return_value.ask = mock_ask

    # 1. Non-sensitive tool (pass through)
    assert session._confirm_tool("read_file", {}) is True

    # 2. Sensitive tool - Deny
    mock_ask.return_value = "n"
    assert session._confirm_tool("run_command", {}) is False

    # 3. Sensitive tool - Allow
    mock_ask.return_value = "y"
    assert session._confirm_tool("run_command", {}) is True

    # 4. Sensitive tool - Always
    mock_ask.return_value = "always"
    assert session._confirm_tool("run_command", {}) is True
    # Should now pass without calling select again
    mock_ask.return_value = "n"
    assert session._confirm_tool("run_command", {}) is True
