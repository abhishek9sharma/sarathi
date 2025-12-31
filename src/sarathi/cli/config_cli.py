import argparse
import copy
import os
import textwrap
from pathlib import Path

import yaml

from sarathi.config.config_manager import DEFAULT_CONFIG, config


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
    
    info_parser = sub.add_parser("info", help="Show information about loaded configuration files")

    set_parser = sub.add_parser("set", help="Set a configuration value")
    set_parser.add_argument("key", help="Configuration key (dot notation, e.g., core.timeout)")
    set_parser.add_argument("value", help="Value to set")
    set_parser.add_argument("--no-save", action="store_true", help="Do not save to file")


def execute_cmd(args):
    if args.config_op == "init":
        create_config(args.path)
    elif args.config_op == "show":
        print(yaml.dump(config._config, default_flow_style=False))
    elif args.config_op == "info":
        print("Active Configuration Sources:")
        if config._loaded_files:
            for file_path in config._loaded_files:
                print(f"  - {file_path}")
        else:
            print("  - Defaults (no config files loaded)")
    elif args.config_op == "set":
        val = args.value
        # Attempt to parse as int/float/bool if possible
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        else:
            try:
                if "." in val:
                    val = float(val)
                else:
                    val = int(val)
            except ValueError:
                pass
        
        config.set(args.key, val, save=not args.no_save)
        print(f"Set {args.key} = {val}")
    else:
        print("Use 'sarathi config init', 'sarathi config show', 'sarathi config info', or 'sarathi config set'")


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
