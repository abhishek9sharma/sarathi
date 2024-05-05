from src.sarathi.llm.call_llm import call_llm_model
from src.sarathi.llm.prompts import prompt_dict


def setup_args(subparsers, opname):

    qa_parser = subparsers.add_parser(opname)
    qa_parser.add_argument("-q", "--question", required=True)


def execute_cmd(args):
    question_asked = args.question
    llm_response = call_llm_model(prompt_dict["qahelper"], question_asked)
    if "Error" not in llm_response:
        answer = llm_response["choices"][0]["message"]["content"]
        print(answer)
        # print(answer)
    else:
        print(llm_response["Error"])
