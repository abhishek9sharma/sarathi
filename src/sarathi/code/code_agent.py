from sarathi.config.config_manager import config
from sarathi.llm.agent_engine import AgentEngine


class CodeEditAgent:
    """Agent for code editing tasks like test generation."""

    def __init__(self):
        """Initialize the code edit agent."""
        self.agent_name = "code_editor"

    def generate_tests(self, source_file: str, test_framework: str = "pytest") -> str:
        """
        Generate tests for a Python source file.

        Args:
            source_file: Path to the source file to generate tests for.
            test_framework: Testing framework to use (default: pytest).

        Returns:
            Path to the generated test file or error message.
        """
        # Load prompt from config
        default_prompt = """You are an expert Python developer specializing in writing comprehensive unit tests.
Your task is to generate tests for Python code using {test_framework}.
Return the path to the generated test file when complete."""

        system_prompt_template = config.get("prompts.generate_tests", default_prompt)
        system_prompt = system_prompt_template.format(test_framework=test_framework)

        tools = [
            "read_file",
            "write_file",
            "parse_python_ast",
            "get_function_code",
            "check_test_exists",
            "run_pytest",
            "run_command",
        ]

        agent = AgentEngine(
            agent_name=self.agent_name, system_prompt=system_prompt, tools=tools
        )

        user_request = f"Generate comprehensive unit tests for the file: {source_file}"

        print(f"🧪 Starting test generation for {source_file}...")
        result = agent.run(user_request)
        print(f"✅ Test generation complete!")

        return result

    def edit_code(self, user_request: str, context_files: list = None) -> str:
        """
        General code editing based on user request.

        Args:
            user_request: Natural language description of what to do.
            context_files: Optional list of files to provide as context.

        Returns:
            Agent's response describing what was done.
        """
        # Load prompt from config
        default_prompt = """You are an expert Python developer and code editor.
Explain what you did after making changes."""

        system_prompt = config.get("prompts.edit_code", default_prompt)

        tools = [
            "read_file",
            "write_file",
            "list_files",
            "find_python_files",
            "parse_python_ast",
            "get_function_code",
            "check_test_exists",
            "run_pytest",
            "run_command",
            "get_git_diff",
            "get_git_status",
            "get_project_structure",
        ]

        # Add context from files if provided
        if context_files:
            context = "\n\nContext files:\n"
            for file in context_files:
                try:
                    with open(file, "r") as f:
                        context += f"\n--- {file} ---\n{f.read()}\n"
                except Exception as e:
                    context += f"\n--- {file} ---\nError reading: {e}\n"
            user_request = user_request + context

        agent = AgentEngine(
            agent_name=self.agent_name, system_prompt=system_prompt, tools=tools
        )

        print(f"🤖 Processing request...")
        result = agent.run(user_request)
        print(f"✅ Complete!")

        return result
