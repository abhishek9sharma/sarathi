import subprocess

from sarathi.llm.call_llm import send_prompt_to_api
from sarathi.llm.prompts import prompt_formats


def get_staged_diff():
    return subprocess.run(
        ["git", "diff", "--staged"], stdout=subprocess.PIPE
    ).stdout.decode("utf-8")


def generate_commit_message():
    diff = get_staged_diff()
    prompt = prompt_formats["autocommit"]
    llm_response = send_prompt_to_api(prompt, diff)
    return llm_response["choices"][0]["message"]["content"]


def get_user_confirmation():
    return input("Do you want to proceed y/n: ").strip() == "y"


def setup_args(subparsers, opname):

    git_parser = subparsers.add_parser(opname)
    git_sub_cmd = git_parser.add_subparsers(dest="git_sub_cmd")

    commit_op = git_sub_cmd.add_parser("autocommit")


def execute_cmd(args):
    if args.git_sub_cmd == "autocommit":
        generated_commit_msg = generate_commit_message()

        if generated_commit_msg:
            print(generated_commit_msg)
            if get_user_confirmation():
                subprocess.run(["git", "commit", "-m", generated_commit_msg])
            else:
                print("I would try to generate a better commit msgs next time")
