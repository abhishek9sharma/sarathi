import argparse
import yaml
import os
from pathlib import Path
from sarathi.config.config_manager import config, DEFAULT_CONFIG

def setup_args(subparsers, opname="config"):
    parser = subparsers.add_parser(opname, help="Manage configuration")
    sub = parser.add_subparsers(dest="config_op")
    
    init_parser = sub.add_parser("init", help="Initialize a new configuration file")
    init_parser.add_argument("--global", dest="is_global", action="store_true", help="Create config in ~/.sarathi/config.yaml")
    
    show_parser = sub.add_parser("show", help="Show the current active configuration")

def execute_cmd(args):
    if args.config_op == "init":
        create_config(args.is_global)
    elif args.config_op == "show":
        print(yaml.dump(config._config, default_flow_style=False))
    else:
        print("Use 'sarathi config init' or 'sarathi config show'")

def create_config(is_global):
    if is_global:
        path = Path.home() / ".sarathi" / "config.yaml"
        # Ensure dir exists
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = Path.cwd() / "sarathi.yaml"
    
    if path.exists():
        overwrite = input(f"Config file {path} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            return
            
    with open(path, 'w') as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
    
    print(f"Configuration file created at {path}")
