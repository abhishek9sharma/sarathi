import argparse

from sarathi.config.config_manager import config


def setup_args(subparsers, opname="model"):
    parser = subparsers.add_parser(opname, help="Switch LLM models")
    parser.add_argument(
        "model_name",
        nargs="?",
        help="Name of the model to use (leave empty to show current model)",
    )
    parser.add_argument(
        "--agent",
        "-a",
        help="Specific agent to update (default: update all relevant agents)",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Do not save to config file"
    )


def execute_cmd(args):
    agents_to_update = []
    if args.agent:
        agents_to_update = [args.agent]
    else:
        # Default agents to update
        agents_to_update = [
            "commit_generator",
            "qahelper",
            "update_docstrings",
            "code_editor",
            "chat",
        ]

    if not args.model_name:
        # Show mode
        print("Current Model Configuration:")
        for agent in agents_to_update:
            model = (
                config.get(f"agents.{agent}.model")
                or "Not configured (using provider default)"
            )
            print(f"  - {agent}: {model}")
        return

    # Update mode
    for agent in agents_to_update:
        config.update_agent_model(agent, args.model_name, save=False)

    if not args.no_save:
        config.save_to_file()

    print(f"Model set to '{args.model_name}' for agents: {', '.join(agents_to_update)}")
