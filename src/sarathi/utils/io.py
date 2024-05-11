import os


def read_file(file_path):
    """Reads the content of a file.

    Args:
        file_path: The path to the file to be read.

    Returns:
        The content of the file as a string."""
    with open(file_path, "r") as f:
        text = f.read()
    return text


def is_valid_file(parser, arg):
    """Check if the input file path is valid and exists.

    Args:
        parser: The ArgumentParser object.
        arg: The file path to be checked.

    Returns:
        The input file path if it is valid."""
    if not os.path.isfile(arg):
        parser.error("The file {} does not exist!".format(arg))
    else:
        return arg


def is_valid_directory(parser, arg):
    """Check if the given directory path is valid.

    Args:
        parser: The parser object.
        arg: The directory path to be validated.

    Returns:
        The valid directory path if it exists.

    Raises:
        Argument error: If the directory does not exist."""
    if not os.path.isdir(arg):
        parser.error("The directory {} does not exist!".format(arg))
    else:
        return arg


def get_filepaths(directory, ignore_extensions=None, ignore_files=None):
    """
    This function returns a list of file paths in the specified directory while ignoring certain file extensions and filenames.

    Args:
        directory: A string representing the directory path for which file paths need to be retrieved.
        ignore_extensions: An optional list of strings representing file extensions to be ignored. Default value is [.pycache, .pyc, .pyo].
        ignore_files: An optional list of strings representing file names to be ignored. Default value is [__init__.py].

    Returns"""
    if ignore_extensions is None:
        ignore_extensions = [".pycache", ".pyc", ".pyo"]
    if ignore_files is None:
        ignore_files = ["__init__.py"]
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            if not any(filename.endswith(ext) for ext in ignore_extensions):
                if filename not in ignore_files:
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath)
    return file_paths
