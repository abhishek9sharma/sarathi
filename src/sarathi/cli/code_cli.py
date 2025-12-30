"""
CLI commands for code editing operations.

Provides commands for test generation and general code editing.
"""
from sarathi.code.code_agent import CodeEditAgent


def setup_args(subparsers, opname):
    """
    Set up argument parser for code editing commands.
    
    Args:
        subparsers: The argument parser subparsers object.
        opname: The operation name for this command group.
    """
    code_parser = subparsers.add_parser(opname, help="Code editing and test generation")
    code_sub_cmd = code_parser.add_subparsers(dest="code_sub_cmd")
    
    # Test generation command
    gentest_parser = code_sub_cmd.add_parser(
        "gentest",
        help="Generate unit tests for a Python file"
    )
    gentest_parser.add_argument(
        "-f", "--file",
        required=True,
        help="Path to the Python file to generate tests for"
    )
    gentest_parser.add_argument(
        "--framework",
        default="pytest",
        choices=["pytest", "unittest"],
        help="Testing framework to use (default: pytest)"
    )
    
    # General code editing command
    edit_parser = code_sub_cmd.add_parser(
        "edit",
        help="Edit code based on natural language request"
    )
    edit_parser.add_argument(
        "request",
        help="Natural language description of what to do"
    )
    edit_parser.add_argument(
        "-c", "--context",
        nargs="+",
        help="Context files to provide to the agent"
    )


def execute_cmd(args):
    """
    Execute code editing commands.
    
    Args:
        args: Parsed command line arguments.
    """
    agent = CodeEditAgent()
    
    if args.code_sub_cmd == "gentest":
        result = agent.generate_tests(
            source_file=args.file,
            test_framework=args.framework
        )
        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        print(result)
        
    elif args.code_sub_cmd == "edit":
        result = agent.edit_code(
            user_request=args.request,
            context_files=args.context
        )
        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        print(result)
    
    else:
        print("Unknown code subcommand. Use --help for available commands.")
