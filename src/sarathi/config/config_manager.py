import os
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "core": {"provider": "openai", "timeout": 30},
    "providers": {
        "openai": {"base_url": "https://api.openai.com/v1"},
        "ollama": {"base_url": "http://localhost:11434", "model": "llama3"},
    },
    "prompts": {
        "commit_generator": """Your task is to generate a commit message based on the diff provided. Please follow below guidelines while generating the commit message
- Think like a software developer
- Provide a high level description of changes
- Wrap lines at 72 characters
- In case of multiple lines add the character - in front of each line
- Provide High Level Description
- Use a maximum of 50 words
- Use standard English
- Try to be concise. Do not write multiple lines if not required
- If you think the diff fixes a comminbug, security issue or CVE which you know about, mention that in your response
- Do not repeat instructions in commit message""",
        "qahelper": """Your task is to answer the below question to the best of your knowledge. Please follow below guidelines
- Think like a principal software engineer who is assiting a junior developer
- Do not give any nasty comments or answers.
- If you do not know the answer do not make it up, just say 'sorry I do not know answer to that question'""",
        "update_docstrings": """Your task is to generate Google style docstrings format for the python code provided below. Please follow below guidelines while generating the docstring
- docstrings should be generated in Google style docstrings format. An example is mentioned below
        \"\"\"Reads the content of a file.

            Args:
                file_path: The path to the file to be read.

            Returns:
                The content of the file as a string.
        \"\"\"
- in your response only the docstrings should be send back, make sure not to send any code back in response
- if you cannot determine the type of parameter or arguments, do not make up the type values in docstrings
- do not mention any single quotes or double quotes in the response
- if you do not know the answer do not make it up, just say sorry I do not know that""",
        "generate_tests": """You are an expert Python developer specializing in writing comprehensive unit tests.

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

Return the path to the generated test file when complete.""",
        "edit_code": """You are an expert Python developer and code editor.

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

Be thorough but concise in your explanations.""",
        "file_analysis": """Analyze this git diff and provide a 1-line summary (max 15 words).
Focus on: what changed and why it matters. Be specific about the change.

{diff}""",
        "commit_coordination": """Generate a git commit message from these file summaries.

Rules:
- First line: imperative mood summary, max 50 chars (e.g., "Add user authentication")
- Blank line after first line
- Bullet points for each significant change
- Max 72 chars per line
- Be concise but informative

File changes:
{summaries}""",
        "chat_mode": """You are Sarathi, an intelligent coding assistant running in an interactive CLI.

Your capabilities:
- Answering technical questions
- Explaining code
- Editing code and generating tests (using available tools)
- Executing terminal commands
- Analyzing project structure

Guidelines:
- You are in a persistent conversation. Remember previous context.
- Be concise and helpful.
- Use code blocks for code.
- If you need to manipulate files, use the provided tools.
- If asked to "clear", "exit", or "quit", the user is using slash commands, but you should acknowledge them if they slip through.
- When running commands, ensure they are safe.

Current Directory: {current_dir}"""
    },
    "agents": {
        "commit_generator": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
        },
        "qahelper": {
            "provider": "openai",
            "model": "gpt-4o-mini",
        },
        "update_docstrings": {
            "provider": "openai",
            "model": "gpt-4o-mini",
        },
        "code_editor": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.3,
        },
        "chat": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.5,
        },
    },
}


import copy

class ConfigManager:
    def __init__(self):
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded_files = []
        self.load_configs()

    def load_configs(self, custom_path=None):
        """Loads configuration. If custom_path is provided, it uses that.
        Otherwise it defaults to:
        1. Local sarathi.yaml (current directory)
        2. Global ~/.sarathi/config.yaml
        """
        # Always start with defaults
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded_files = []

        if custom_path:
            config_path = Path(custom_path)
            if config_path.exists():
                self._merge_from_file(config_path)
            else:
                print(f"Warning: Configuration file not found at {custom_path}")
        else:
            # 1. Local Project Config (sarathi.yaml)
            local_config_path = Path("sarathi.yaml")
            if local_config_path.exists():
                self._merge_from_file(local_config_path)

            # 2. User Global Config (~/.sarathi/config.yaml)
            global_config_path = Path.home() / ".sarathi" / "config.yaml"
            if global_config_path.exists():
                self._merge_from_file(global_config_path)

        # Environment Variables (apply last for secrets)
        self._apply_env_overrides()

    def _merge_from_file(self, path):
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    # Security: Enforce that api_key cannot be loaded from yaml
                    if "providers" in data:
                        for provider in data["providers"].values():
                            if "api_key" in provider:
                                provider.pop("api_key", None)
                                print(
                                    "Warning: 'api_key' in configuration file is ignored for security. Use environment variables."
                                )

                    self._deep_merge(self._config, data)
                    self._loaded_files.append(str(path.absolute()))
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")

    def _deep_merge(self, base, update):
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self):
        # Allow legacy env vars to override the active provider config
        api_key = os.getenv("SARATHI_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if api_key:
            # We don't know which provider they mean if they just set OPENAI_API_KEY,
            # but historically it meant OpenAI.
            self._config["providers"]["openai"]["api_key"] = api_key

        model = os.getenv("OPENAI_MODEL_NAME")
        if model:
            # This is tricky as we don't know which agent checking the env var was meant for.
            # In legacy sarathi, it applied to everything.
            self._config["agents"]["commit_generator"]["model"] = model
            self._config["agents"]["qahelper"]["model"] = model

    def get(self, key_path, default=None):
        """Get a value using dot notation e.g. 'agents.commit_generator.model'"""
        keys = key_path.split(".")
        curr = self._config
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr

    def get_agent_config(self, agent_name):
        return self._config.get("agents", {}).get(agent_name, {})

    def get_provider_config(self, provider_name):
        return self._config.get("providers", {}).get(provider_name, {})


# Singleton instance
config = ConfigManager()
