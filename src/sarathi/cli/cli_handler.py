import argparse

import sarathi.cli.gendocstrings as docstrgen
import sarathi.cli.qahelper as qahelper
import sarathi.cli.sgit as sgit


def parse_cmd_args():
    """This function parses command line arguments using argparse.

    Returns:
        argparse.Namespace: The parsed arguments from the command line."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="op")
    sgit.setup_args(subparsers, opname="git")
    qahelper.setup_args(subparsers, opname="ask")
    docstrgen.setup_args(subparsers, opname="docstrgen")
    return parser.parse_args()


def main():
    """This function is the entry point of the program.
    It parses the command line arguments and executes the corresponding command based on the value of op attribute in the parsed arguments.
    - If the op is git, it executes a git command.
    - If the op is ask, it executes a command related to question-answering.
    - If the op is docstrgen, it executes a command related to generating docstrings.
    """
    try:
        parsed_args = parse_cmd_args()
        if parsed_args.op == "git":
            sgit.execute_cmd(parsed_args)
        elif parsed_args.op == "ask":
            qahelper.execute_cmd(parsed_args)
        elif parsed_args.op == "docstrgen":
            docstrgen.execute_cmd(parsed_args)
        else:
            print("Unsupported Option")
    except Exception as e:
        print(f"Exception {e} occured while trying to parse the argument")
