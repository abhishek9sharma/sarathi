import argparse
import copy
import os
import textwrap
from pathlib import Path

import yaml

from sarathi.config.config_manager import DEFAULT_CONFIG, config
from sarathi.llm.prompts import prompt_dict


def setup_args(subparsers, opname="config"):
    parser = subparsers.add_parser(opname, help="Manage configuration")
    sub = parser.add_subparsers(dest="config_op")

    init_parser = sub.add_parser("init", help="Initialize a new configuration file")
    init_parser.add_argument(
        "--path",
        "-p",
        help="Path where the config file should be created (defaults to ~/.sarathi/config.yaml)",
    )

    show_parser = sub.add_parser("show", help="Show the current active configuration")


def execute_cmd(args):
    if args.config_op == "init":
        create_config(args.path)
    elif args.config_op == "show":
        print(yaml.dump(config._config, default_flow_style=False))
    else:
        print("Use 'sarathi config init' or 'sarathi config show'")


def create_config(custom_path=None):
    if custom_path:
        path = Path(custom_path)
    else:
        path = Path.home() / ".sarathi" / "config.yaml"

    # Ensure dir exists
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        overwrite = input(f"Config file {path} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != "y":
            return

    # Create an expanded config with prompts for the user file
    full_config = copy.deepcopy(DEFAULT_CONFIG)

    # Map agent names to keys in prompt_dict
    prompt_map = {
        "commit_generator": "autocommit",
        "qahelper": "qahelper",
        "update_docstrings": "update_docstrings",
    }

    for agent_name, prompt_key in prompt_map.items():
        if agent_name in full_config.get("agents", {}):
            if prompt_key in prompt_dict:
                raw_prompt = prompt_dict[prompt_key]["system_msg"]
                # Clean up the prompt formatting so it looks nice in YAML
                full_config["agents"][agent_name]["system_prompt"] = textwrap.dedent(raw_prompt).strip()

    # Security: Ensure we don't dump None-keys that we removed
    if "providers" in full_config:
        for p in full_config["providers"].values():
            p.pop("api_key", None)

    # Configure YAML to use block style for multiline strings
    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    # Use a custom Dumper to ensure we don't affect global state if imported elsewhere
    yaml.add_representer(str, str_presenter)

    with open(path, "w") as f:
        # We must use Dumper=yaml.Dumper to ensure the python-based add_representer works
        yaml.dump(full_config, f, default_flow_style=False, sort_keys=False, Dumper=yaml.Dumper)

    print(f"Configuration file created at {path}")
