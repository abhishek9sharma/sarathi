import os
import re
import sys

try:
    import readline
except ImportError:
    readline = None
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from sarathi.cli.banner import print_banner
from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.tool_library import registry
from sarathi.utils.formatters import (
    format_bold,
    format_code,
    format_cyan,
    format_green,
    format_yellow,
)

console = Console()


class ChatSession:
    def __init__(self, agent_name="chat"):
        from sarathi.config.config_manager import config

        # Hydrate prompt with current directory
        raw_prompt = config.get(
            "prompts.chat_mode", "You are a helpful coding assistant."
        )
        system_prompt = raw_prompt.replace("{current_dir}", os.getcwd())

        self.agent = AgentEngine(
            agent_name=agent_name,
            system_prompt=system_prompt,
            tools=list(registry.tools.keys()),
            tool_confirmation_callback=self._confirm_tool,
        )
        self.running = True
        self.permissions = {}  # tool_name -> "always" | "ask" (default)
        self.project_files = []
        self._index_project()
        self._setup_readline()

    def process_input(self, user_input):
        """Processes a single input line (blocking)."""
        res = ""
        for token in self.process_input_stream(user_input):
            res += token
        return res

    def process_input_stream(self, user_input):
        """Processes input and yields streaming tokens."""
        from sarathi.config.config_manager import config

        processed_input = self._process_at_mentions(user_input)

        if config.get("core.debug"):
            print(f"\n{format_yellow('--- DEBUG: PROCESSED INPUT ---')}")
            print(processed_input)
            print(f"{format_yellow('--- END DEBUG ---')}\n")

        yield from self.agent.run_stream(processed_input)

    def _index_project(self):
        """Build a list of all files in the project for autocomplete."""
        self.project_files = []  # Full paths
        self.filename_to_path = {}  # name -> [list of full paths]

        ignore_ext = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".exe",
            ".DS_Store",
            ".o",
            ".bin",
        }
        ignore_dirs = {
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules",
            ".sarathi",
            ".pytest_cache",
            ".idea",
            ".vscode",
            "build",
            ".github",
        }

        try:
            for root, dirs, files in os.walk("."):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext in ignore_ext:
                        continue

                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    full_at_path = f"@{rel_path}"
                    self.project_files.append(full_at_path)

                    # Store filename mapping
                    if file not in self.filename_to_path:
                        self.filename_to_path[file] = []
                    self.filename_to_path[file].append(rel_path)

            if self.project_files:
                print(
                    f"Project indexed: {len(self.project_files)} files available for @-completion."
                )
        except Exception as e:
            print(f"Warning: Project indexing failed: {e}")

    def _setup_readline(self):
        """Configure readline for autocomplete."""
        if not readline:
            return

        readline.set_completer(self._completer)

        # Minimal delimiters to ensure @path/to/file is treated as one word
        # We only want to split on whitespace and quotes
        readline.set_completer_delims(" \t\n\"\\'`")

        if "libedit" in (readline.__doc__ or ""):
            # macOS default (libedit) binding
            readline.parse_and_bind("bind ^I rl_complete")
            # Show all matches if ambiguous (like bash)
            readline.parse_and_bind("set show-all-if-ambiguous on")
            # Display matches immediately
            readline.parse_and_bind("set completion-display-width 0")
        else:
            # GNU Readline binding - cycle through options
            readline.parse_and_bind("tab: menu-complete")
            readline.parse_and_bind("set show-all-if-ambiguous on")

    def _completer(self, text, state):
        """Readline completer for @mentions and slash commands."""
        if text is None:
            return None

        cmds = ["/exit", "/quit", "/clear", "/history", "/reindex", "/model"]

        # Get the full buffer to understand context
        buffer = readline.get_line_buffer()

        # Check if we're completing a file mention
        if "@" in buffer:
            # Extract query after the last @
            at_pos = buffer.rfind("@")
            query = buffer[at_pos + 1 : readline.get_endidx()].lower()

            options = []
            seen = set()

            # Match by filename first (most intuitive)
            for fname, paths in self.filename_to_path.items():
                if fname.lower().startswith(query):
                    for p in paths:
                        opt = f"@{p}"
                        if opt not in seen:
                            options.append(opt)
                            seen.add(opt)

            # Match by path substring
            for p in self.project_files:
                path_without_at = p[1:]  # Remove leading @
                if query in path_without_at.lower() and p not in seen:
                    options.append(p)
                    seen.add(p)

            # Sort: shorter paths first
            options.sort(key=lambda x: (len(x.split("/")), x.lower()))

            if state < len(options):
                result = options[state]
                # If text already has @, return full path with @
                # If text doesn't have @, return without @ (readline will add it)
                if text.startswith("@"):
                    return result + " "
                else:
                    return result[1:] + " "  # Strip @ since it's already in buffer

        elif buffer.lstrip().startswith("/"):
            # Slash command completion
            query = text.lower()
            options = [c for c in cmds if c.lower().startswith(query)]
            if state < len(options):
                return options[state] + " "

        return None

    def _confirm_tool(self, tool_name, tool_args):
        """Callback to confirm tool execution with user."""
        # Define sensitive tools
        sensitive_tools = [
            "write_file",
            "replace_file_content",
            "multi_replace_file_content",
            "run_command",
        ]

        if tool_name not in sensitive_tools:
            return True

        permission = self.permissions.get(tool_name, "ask")
        if permission == "always":
            return True

        print(f"\n{format_green('Permission Request')}")
        print(f"Agent wants to execute: {tool_name}")
        print(f"Arguments: {tool_args}")

        import questionary

        choice = questionary.select(
            f"Allow {tool_name} to execute?",
            choices=[
                questionary.Choice("Yes (Allow)", value="y"),
                questionary.Choice("No (Deny)", value="n"),
                questionary.Choice("Always allow for this tool", value="always"),
                questionary.Choice("Allow session (all tools)", value="session"),
            ],
            default="y",
        ).ask()

        if choice == "y":
            return True
        elif choice == "n":
            return False
        elif choice in ["always", "session"]:
            self.permissions[tool_name] = "always"
            return True
        return False  # Fallback

    def _process_at_mentions(self, user_input):
        """Parse @filename and inject content."""

        def replace_match(match):
            filepath = match.group(1)
            path = Path(filepath)
            if path.exists() and path.is_file():
                try:
                    content = path.read_text()
                    return f"\n--- Context from {filepath} ---\n{content}\n---------------------------------\n"
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
                    return match.group(0)  # Return original if read fails
            else:
                print(f"Warning: File not found: {filepath}")
                return match.group(0)

        # Regex for @filename (simple implementation, might need refinement for spaces)
        # Matches @ followed by non-whitespace characters
        return re.sub(r"@([\w./-]+)", replace_match, user_input)

    def start(self):
        print_banner()
        print(
            format_green(
                "Welcome! Type '/exit' to quit, '/clear' to reset, '/history' to view logs.\n"
            )
        )

        while self.running:
            try:
                user_input = input(format_green("sarathi> "))
                if not user_input.strip():
                    continue

                if user_input.startswith("/"):
                    self.handle_slash_command(user_input)
                    continue

                print(f"\n{format_green('Sarathi is thinking...')}")

                full_response = ""
                with Live(console=console, vertical_overflow="visible") as live:
                    for token in self.process_input_stream(user_input):
                        full_response += token
                        # Only render markdown if it looks like enough to be markdown
                        # to avoid jitter on single characters
                        live.update(Markdown(full_response))
                print()

            except KeyboardInterrupt:
                print("\nType '/exit' to quit.")
            except EOFError:
                self.running = False
                print("\nGoodbye!")
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")

    def handle_slash_command(self, command):
        cmd = command.split()[0].lower()
        if cmd in ["/exit", "/quit"]:
            self.running = False
            print("Goodbye!")
        elif cmd == "/clear":
            self.agent.messages = [self.agent.messages[0]]  # Keep system prompt
            print("Context cleared.")
        elif cmd == "/reindex":
            self._index_project()
            print(f"Project re-indexed. Found {len(self.project_files)} files.")
        elif cmd == "/history":
            for msg in self.agent.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content") or ""
                content_preview = content[:50] + "..." if content else ""
                if not content and msg.get("tool_calls"):
                    content_preview = f"<{len(msg['tool_calls'])} tool calls>"
                print(f"[{role}]: {content_preview}")
        elif cmd == "/model":
            parts = command.split()
            if len(parts) > 1:
                new_model = parts[1]
                from sarathi.config.config_manager import config

                config.update_agent_model("chat", new_model, save=False)
                print(f"Model for this chat session switched to: {new_model}")
            else:
                from sarathi.config.config_manager import config

                current_model = config.get("agents.chat.model")
                print(f"Current model: {current_model}")
                print("Usage: /model <model_name>")
        else:
            print(f"Unknown command: {cmd}")


def setup_args(subparsers, opname="chat"):
    parser = subparsers.add_parser(
        opname, help="Start an interactive chat session or ask a one-off question"
    )
    parser.add_argument("-q", "--question", help="Ask a single question and exit")


def execute_cmd(args):
    session = ChatSession()
    if getattr(args, "question", None):
        print(f"\n{format_green('Sarathi is thinking...')}")
        response = session.process_input(args.question)
        console.print(Markdown(response))
    else:
        session.start()
