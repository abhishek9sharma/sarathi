import os


def read_file(file_path):
    with open(file_path, "r") as f:
        text = f.read()
    return text


def is_valid_file(parser, arg):
    if not os.path.isfile(arg):
        parser.error("The file {} does not exist!".format(arg))
    else:
        return arg


def is_valid_directory(parser, arg):
    if not os.path.isdir(arg):
        parser.error("The directory {} does not exist!".format(arg))
    else:
        return arg


def get_filepaths(directory, ignore_extensions=None, ignore_files=None):
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
                    file_paths.append(filepath)  # Add it to the list.

    return file_paths
