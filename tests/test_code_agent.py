from unittest.mock import MagicMock, patch

import pytest

from sarathi.code.code_agent import CodeEditAgent


def test_code_edit_agent_initialization():
    """Test the initialization of CodeEditAgent."""
    agent = CodeEditAgent()
    assert agent.agent_name == "code_editor"


def test_generate_tests_success():
    """Test generating tests successfully."""
    agent = CodeEditAgent()
    source_file = "dummy_path.py"
    expected_result = "tests/test_dummy_path.py"

    with patch(
        "sarathi.llm.agent_engine.AgentEngine.run", return_value=expected_result
    ) as mock_run:
        result = agent.generate_tests(source_file)
        mock_run.assert_called_once_with(
            f"Generate comprehensive unit tests for the file: {source_file}"
        )
        assert result == expected_result


def test_generate_tests_with_error():
    """Test generating tests when an error occurs."""
    agent = CodeEditAgent()
    source_file = "non_existent_path.py"
    expected_error = "Error: File not found"

    with patch(
        "sarathi.llm.agent_engine.AgentEngine.run", return_value=expected_error
    ) as mock_run:
        result = agent.generate_tests(source_file)
        mock_run.assert_called_once_with(
            f"Generate comprehensive unit tests for the file: {source_file}"
        )
        assert result == expected_error


def test_edit_code_with_context():
    """Test editing code with context files provided."""
    agent = CodeEditAgent()
    user_request = "Refactor the code"
    context_files = ["file1.py", "file2.py"]
    expected_result = "Refactoring complete"

    with patch(
        "sarathi.llm.agent_engine.AgentEngine.run", return_value=expected_result
    ) as mock_run:
        result = agent.edit_code(user_request, context_files)
        assert "Context files:" in mock_run.call_args[0][0]
        assert result == expected_result


def test_edit_code_without_context():
    """Test editing code without any context files."""
    agent = CodeEditAgent()
    user_request = "Add a new feature"
    expected_result = "Feature added successfully"

    with patch(
        "sarathi.llm.agent_engine.AgentEngine.run", return_value=expected_result
    ) as mock_run:
        result = agent.edit_code(user_request)
        mock_run.assert_called_once_with(user_request)
        assert result == expected_result
