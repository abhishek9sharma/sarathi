import argparse
import importlib
import sys

from sarathi.cli.registry import CLI_REGISTRY
from sarathi.utils.io import is_valid_directory, is_valid_file

# Map string type names to actual functions if needed
TYPE_MAP = {
    "is_valid_file": lambda parser, x: is_valid_file(parser, x),
    "is_valid_directory": lambda parser, x: is_valid_directory(parser, x),
}


def resolve_type(type_name, parser):
    """Resolves a string type name to a callable, passing parser if needed."""
    if isinstance(type_name, str) and type_name in TYPE_MAP:
        return lambda x: TYPE_MAP[type_name](parser, x)
    return type_name


def parse_cmd_args():
    parser = argparse.ArgumentParser(description="Sarathi - AI Coding Assistant")
    parser.add_argument(
        "--config", "-c", help="Path to a custom configuration YAML file"
    )
    subparsers = parser.add_subparsers(dest="op")

    for cmd_name, config_item in CLI_REGISTRY.items():
        # Dynamic Import
        module = importlib.import_module(config_item["module"])

        if config_item.get("custom_setup"):
            # Let the module handle subparser creation entirely
            if hasattr(module, "setup_args"):
                module.setup_args(subparsers, opname=cmd_name)
        else:
            # Create parser for simple commands
            cmd_parser = subparsers.add_parser(cmd_name, help=config_item.get("help"))

            for arg_def in config_item.get("args", []):
                flags = arg_def["flags"]
                kwargs = arg_def["kwargs"].copy()
                if "type" in kwargs:
                    kwargs["type"] = resolve_type(kwargs["type"], cmd_parser)
                cmd_parser.add_argument(*flags, **kwargs)

    return parser.parse_args()


BANNER = r"""
   ____                  _   _     _ 
  / ___|  __ _ _ __ __ _| |_| |__ (_)
  \___ \ / _` | '__/ _` | __| '_ \| |
   ___) | (_| | | | (_| | |_| | | | |
  |____/ \__,_|_|  \__,_|\__|_| |_|_|
                                     
  AI Coding Assistant
"""

def print_banner():
    print(BANNER)

def check_config_nudge():
    from pathlib import Path
    import os
    from sarathi.config.config_manager import config
    
    config_path = Path.home() / ".sarathi" / "config.yaml"
    
    # 1. If no config, show banner and nudge
    if not config_path.exists():
        print_banner()
        print("\033[93mTip: Welcome! Run 'sarathi config init' to set up your LLM configuration.\033[0m")
        print("-" * 50)
        return True # Showed something
    
    # 2. If config exists but key missing, just show the warning (no banner)
    active_provider = config.get("core.provider")
    if active_provider == "openai":
        api_key = os.getenv("SARATHI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\033[93mTip: OpenAI is active but OPENAI_API_KEY is not set.\033[0m")
            print("-" * 50)
            return True # Showed something
    return False

def main():
    try:
        from sarathi.config.config_manager import config

        parsed_args = parse_cmd_args()

        # Load custom config if provided
        if parsed_args.config:
            config.load_configs(parsed_args.config)

        # Logic for banner and nudges
        displayed_nudge = False
        if parsed_args.op != "config":
             displayed_nudge = check_config_nudge()

        if not parsed_args.op:
            # Only print banner here if nudge didn't already print it
            if not displayed_nudge:
                print_banner()
            print("No command specified. Use --help to see available commands.")
            return

        if parsed_args.op in CLI_REGISTRY:
            conf = CLI_REGISTRY[parsed_args.op]
            module = importlib.import_module(conf["module"])
            handler = getattr(module, conf["handler"])
            handler(parsed_args)
        else:
            print(f"Unknown command: {parsed_args.op}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
