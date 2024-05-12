import argparse
import os

from sarathi.code.codetasks import CodeTransformer
from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.prompts import prompt_dict
from sarathi.utils.io import get_filepaths, is_valid_directory, is_valid_file


def setup_args(subparsers, opname):
    """
    Adds arguments for setting up a command line parser.

    Args:
        subparsers: The subparsers object to add the arguments to.
        opname: The name of the operation.

    Returns:
        None
    """
    gendocstr_parser = subparsers.add_parser(opname)
    gendocstr_parser.add_argument(
        "-f",
        "--filepath",
        required=False,
        type=lambda x: is_valid_file(gendocstr_parser, x),
    )
    gendocstr_parser.add_argument(
        "-d",
        "--dirpath",
        required=False,
        type=lambda x: is_valid_directory(gendocstr_parser, x),
    )


def execute_cmd(args):
    """
    Execute a command based on the provided arguments.

    Args:
        args: A dictionary containing filepath and dirpath information.

    Returns:
        None
    """
    file_path = args.filepath
    dir_path = args.dirpath
    if file_path and dir_path:
        print("Please enter a file or a folder. Both arguments cannot be specified")
    elif file_path:
        print(f"Generating docstrings for file {file_path}")
        code_transformer = CodeTransformer(file_path)
        code_transformer.transform_code()
    elif dir_path:
        files_to_process = get_filepaths(dir_path)
        for fpath in files_to_process:
            print(f"Generating docstrings for file {fpath}")
            code_transformer = CodeTransformer(fpath)
            code_transformer.transform_code()
