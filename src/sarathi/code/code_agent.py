"""
Code editing agent for generating tests and modifying code.

Uses the AgentEngine with specialized tools for code analysis and modification.
"""
from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.prompts import prompt_dict


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
        system_prompt = f"""You are an expert Python developer specializing in writing comprehensive unit tests.

Your task is to generate tests for Python code using {test_framework}.

Follow these steps:
1. Use `read_file` to read the source code
2. Use `parse_python_ast` to understand the code structure
3. Use `check_test_exists` to see if tests already exist
4. Generate comprehensive test cases covering:
   - Normal cases
   - Edge cases
   - Error handling
   - Different input types
5. Use `write_file` to create the test file
6. Use `run_pytest` to verify the tests run

Guidelines:
- Write clear, descriptive test names
- Use fixtures when appropriate
- Mock external dependencies
- Aim for high code coverage
- Include docstrings in test functions
- Follow PEP 8 style guidelines

Return the path to the generated test file when complete."""

        tools = [
            "read_file",
            "write_file",
            "parse_python_ast",
            "get_function_code",
            "check_test_exists",
            "run_pytest",
            "run_command"
        ]
        
        agent = AgentEngine(
            agent_name=self.agent_name,
            system_prompt=system_prompt,
            tools=tools
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
        system_prompt = """You are an expert Python developer and code editor.

You can help with:
- Generating new code
- Refactoring existing code
- Adding features
- Fixing bugs
- Generating tests
- Adding documentation

Available tools:
- File operations: read_file, write_file, list_files, find_python_files
- Code analysis: parse_python_ast, get_function_code
- Git operations: get_git_diff, get_git_status
- Testing: run_pytest, check_test_exists
- Command execution: run_command
- Project structure: get_project_structure

Always:
1. Understand the request fully
2. Read relevant files to understand context
3. Make changes carefully
4. Verify changes work (run tests if applicable)
5. Explain what you did

Be thorough but concise in your explanations."""

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
            "get_project_structure"
        ]
        
        # Add context from files if provided
        if context_files:
            context = "\n\nContext files:\n"
            for file in context_files:
                try:
                    with open(file, 'r') as f:
                        context += f"\n--- {file} ---\n{f.read()}\n"
                except Exception as e:
                    context += f"\n--- {file} ---\nError reading: {e}\n"
            user_request = user_request + context
        
        agent = AgentEngine(
            agent_name=self.agent_name,
            system_prompt=system_prompt,
            tools=tools
        )
        
        print(f"🤖 Processing request...")
        result = agent.run(user_request)
        print(f"✅ Complete!")
        
        return result
