import argparse
import os

from sarathi.code.codetasks import CodeTransformer
from sarathi.utils.io import get_filepaths, is_valid_directory, is_valid_file


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
