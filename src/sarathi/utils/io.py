def read_file(file_path):
    with open(file_path, "r") as f:
        text = f.read()
    return text
