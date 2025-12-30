import subprocess
import os
from sarathi.llm.tools import registry

@registry.register(name="get_git_diff", description="Get staged changes in the current git repository.")
def get_git_diff():
    return subprocess.run(
        ["git", "diff", "--staged"], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")

@registry.register(name="list_files", description="List files in a directory.")
def list_files(directory="."):
    return os.listdir(directory)

@registry.register(name="read_file", description="Read the content of a file.")
def read_file(filepath):
    with open(filepath, "r") as f:
        return f.read()

@registry.register(name="run_command", description="Run a shell command.")
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
    except Exception as e:
        return str(e)
