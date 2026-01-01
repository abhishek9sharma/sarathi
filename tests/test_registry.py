import pytest

from sarathi.cli.registry import CLI_REGISTRY
from sarathi.utils.io import is_valid_directory, is_valid_file


def test_cli_registry_structure():
    """
    Test that each command in the CLI_REGISTRY has the required structure.
    """
    required_keys = {"help", "module", "handler"}
    for command, config in CLI_REGISTRY.items():
        assert required_keys.issubset(config.keys()), f"Missing keys in {command}"


def test_cli_registry_args_structure():
    """
    Test that the 'args' key, when present, is a list and contains dictionaries with the expected structure.
    """
    for command, config in CLI_REGISTRY.items():
        if "args" in config:
            assert isinstance(config["args"], list), f"Args for {command} is not a list"
            for arg in config["args"]:
                assert (
                    "flags" in arg and "kwargs" in arg
                ), f"Invalid arg structure in {command}"
                assert isinstance(
                    arg["flags"], list
                ), f"Flags for {command} is not a list"
                assert isinstance(
                    arg["kwargs"], dict
                ), f"Kwargs for {command} is not a dict"


def test_cli_registry_function_mappings():
    """
    Test that the 'type' strings in 'args' correspond to actual functions.
    """
    type_function_map = {
        "is_valid_file": is_valid_file,
        "is_valid_directory": is_valid_directory,
    }
    for command, config in CLI_REGISTRY.items():
        if "args" in config:
            for arg in config["args"]:
                if "type" in arg["kwargs"]:
                    type_str = arg["kwargs"]["type"]
                    assert (
                        type_str in type_function_map
                    ), f"Unknown type {type_str} in {command}"
                    assert callable(
                        type_function_map[type_str]
                    ), f"Type {type_str} is not callable in {command}"


def test_cli_registry_custom_setup():
    """
    Test that commands with 'custom_setup' are correctly identified.
    """
    for command, config in CLI_REGISTRY.items():
        if "custom_setup" in config:
            assert isinstance(
                config["custom_setup"], bool
            ), f"Custom setup for {command} is not a boolean"
            assert (
                config["custom_setup"] is True
            ), f"Custom setup for {command} is not True when expected"
