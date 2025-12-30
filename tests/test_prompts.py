import pytest
from sarathi.llm.prompts import prompt_dict

def test_prompt_dict_structure():
    """Verify prompt_dict has expected structure"""
    assert isinstance(prompt_dict, dict)
    
    # Check required keys
    required_keys = ["autocommit", "qahelper", "update_docstrings"]
    for key in required_keys:
        assert key in prompt_dict, f"Missing key: {key}"

def test_autocommit_prompt():
    """Verify autocommit prompt has required fields"""
    autocommit = prompt_dict["autocommit"]
    
    assert "system_msg" in autocommit
    assert "model" in autocommit
    
    # Check content
    system_msg = autocommit["system_msg"]
    assert isinstance(system_msg, str)
    assert len(system_msg) > 0
    
    # Verify it contains key instructions
    assert "commit message" in system_msg.lower()
    assert "diff" in system_msg.lower()

def test_qahelper_prompt():
    """Verify qahelper prompt has required fields"""
    qahelper = prompt_dict["qahelper"]
    
    assert "system_msg" in qahelper
    assert "model" in qahelper
    
    system_msg = qahelper["system_msg"]
    assert isinstance(system_msg, str)
    assert "question" in system_msg.lower()

def test_update_docstrings_prompt():
    """Verify update_docstrings prompt has required fields"""
    docstrings = prompt_dict["update_docstrings"]
    
    assert "system_msg" in docstrings
    assert "model" in docstrings
    
    system_msg = docstrings["system_msg"]
    assert isinstance(system_msg, str)
    assert "docstring" in system_msg.lower()
    assert "Google style" in system_msg

def test_all_prompts_have_models():
    """Ensure all prompts specify a model"""
    for key, value in prompt_dict.items():
        assert "model" in value, f"{key} missing model specification"
        assert isinstance(value["model"], str)
        assert len(value["model"]) > 0

def test_all_prompts_have_system_messages():
    """Ensure all prompts have non-empty system messages"""
    for key, value in prompt_dict.items():
        assert "system_msg" in value, f"{key} missing system_msg"
        assert isinstance(value["system_msg"], str)
        assert len(value["system_msg"].strip()) > 0
