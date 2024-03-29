import argparse

import sarathi.cli.sgit as sgit


def parse_cmd_args():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="op")

    sgit.setup_args(subparsers, opname="git")

    return parser.parse_args()


def main():
    try:
        parsed_args = parse_cmd_args()
        if parsed_args.op == "git":
            sgit.execute_cmd(parsed_args)
        else:
            print("Unsupported Options")
    except Exception as e:
        print(f"Exception {e} occured while trying to parse the argument")
