from sarathi.utils.io import is_valid_directory, is_valid_file

# Registry of all available CLI commands
# Structure:
# "command_name": {
#     "help": "Help text",
#     "module": "module.path",
#     "handler": "function_name",
#     "args": [
#         {"flags": ["-f", "--flag"], "kwargs": {"help": "..."}}
#     ],
#     "subcommands": { ... } # Optional nested structure
# }

CLI_REGISTRY = {
    "git": {
        "help": "Git operations helper",
        "module": "sarathi.cli.sgit",
        "handler": "execute_cmd",
        # Git uses its own internal subparser logic for now which is complex
        # So we keep using its setup_args for the specific arguments,
        # but we route it dynamically.
        "custom_setup": True,
    },
    "docstrgen": {
        "help": "Generate Python docstrings",
        "module": "sarathi.cli.gendocstrings",
        "handler": "execute_cmd",
        "args": [
            {
                "flags": ["-f", "--filepath"],
                "kwargs": {
                    "required": False,
                    "help": "Path to a specific file",
                    "type": "is_valid_file",  # Special string we'll map to function
                },
            },
            {
                "flags": ["-d", "--dirpath"],
                "kwargs": {
                    "required": False,
                    "help": "Path to a directory",
                    "type": "is_valid_directory",
                },
            },
        ],
    },
    "config": {
        "help": "Manage configuration",
        "module": "sarathi.cli.config_cli",
        "handler": "execute_cmd",
        "custom_setup": True,  # Config has subcommands (init, show)
    },
    "code": {
        "help": "Code editing and test generation",
        "module": "sarathi.cli.code_cli",
        "handler": "execute_cmd",
        "custom_setup": True,  # Code has subcommands (gentest, edit)
    },
    "chat": {
        "help": "Ask a question or start an interactive chat session",
        "module": "sarathi.cli.chat_cli",
        "handler": "execute_cmd",
        "custom_setup": True,
    },
    "model": {
        "help": "Switch LLM models",
        "module": "sarathi.cli.model_cli",
        "handler": "execute_cmd",
        "custom_setup": True,
    },
}
