from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.prompts import prompt_dict


def setup_args(subparsers, opname):
    """Setup the arguments for a subparser.

    Args:
        subparsers: The subparsers object to add the argument parser to.
        opname: The name of the operation.

    Returns:
        None
    """
    qa_parser = subparsers.add_parser(opname)
    qa_parser.add_argument("-q", "--question", required=True)


def execute_cmd(args):
    """Execute a command.

    Args:
        args: A dictionary containing the command arguments.

    Returns:
        None
    """
    question_asked = args.question
    llm_response = call_llm_model(prompt_dict["qahelper"], question_asked)
    if "Error" not in llm_response:
        answer = llm_response["choices"][0]["message"]["content"]
        print(answer)
    else:
        print(llm_response["Error"])
