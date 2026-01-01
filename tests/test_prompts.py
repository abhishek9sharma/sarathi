import pytest

from sarathi.config.config_manager import config


def test_config_prompts_structure():
    """Verify DEFAULT_CONFIG has expected prompts structure"""
    prompts = config.get("prompts")
    assert isinstance(prompts, dict)

    # Check required keys in DEFAULT_CONFIG (or loaded config)
    required_keys = [
        "commit_generator",
        "qahelper",
        "update_docstrings",
        "generate_tests",
        "edit_code",
        "file_analysis",
        "commit_coordination",
    ]
    for key in required_keys:
        assert key in prompts, f"Missing prompt key: {key}"


def test_commit_generator_prompt():
    """Verify commit_generator prompt in config"""
    prompt = config.get("prompts.commit_generator")
    assert isinstance(prompt, str)
    assert len(prompt) > 0

    # Verify it contains key instructions
    assert "commit message" in prompt.lower()
    assert "diff" in prompt.lower()


def test_qahelper_prompt():
    """Verify qahelper prompt in config"""
    prompt = config.get("prompts.qahelper")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "question" in prompt.lower()


def test_update_docstrings_prompt():
    """Verify update_docstrings prompt in config"""
    prompt = config.get("prompts.update_docstrings")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "docstring" in prompt.lower()
    assert "Google style" in prompt


def test_generate_tests_prompt():
    """Verify generate_tests prompt in config"""
    prompt = config.get("prompts.generate_tests")
    assert isinstance(prompt, str)
    assert "{test_framework}" in prompt


def test_all_config_prompts_not_empty():
    """Ensure all configured prompts are non-empty strings"""
    prompts = config.get("prompts")
    for key, value in prompts.items():
        assert isinstance(value, str), f"Prompt {key} should be a string"
        assert len(value.strip()) > 0, f"Prompt {key} is empty"
