import os
import sys
import re
try:
    import readline
except ImportError:
    readline = None
from pathlib import Path
from sarathi.llm.agent_engine import AgentEngine
from sarathi.llm.tool_library import registry
from sarathi.utils.formatters import format_green, format_code, format_cyan, format_yellow, format_bold
from sarathi.cli.banner import print_banner

class ChatSession:
    def __init__(self):
        from sarathi.config.config_manager import config
        
        # Hydrate prompt with current directory
        raw_prompt = config.get("prompts.chat_mode", "You are a helpful coding assistant.")
        system_prompt = raw_prompt.replace("{current_dir}", os.getcwd())
        
        self.agent = AgentEngine(
            agent_name="chat",
            system_prompt=system_prompt,
            tools=list(registry.tools.keys()),
            tool_confirmation_callback=self._confirm_tool
        )
        self.running = True
        self.permissions = {} # tool_name -> "always" | "ask" (default)
        self.project_files = []
        self._index_project()
        self._setup_readline()

    def _index_project(self):
        """Build a list of all files in the project for autocomplete."""
        self.project_files = [] # Full paths
        self.filename_to_path = {} # name -> [list of full paths]
        
        ignore_ext = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.DS_Store', '.o', '.bin'}
        ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.sarathi', '.pytest_cache', '.idea', '.vscode'}
        
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
                print(f"Project indexed: {len(self.project_files)} files available for @-completion.")
        except Exception as e:
            print(f"Warning: Project indexing failed: {e}")

    def _setup_readline(self):
        """Configure readline for autocomplete."""
        if not readline:
            return
            
        readline.set_completer(self._completer)
        if 'libedit' in readline.__doc__:
            # macOS default (libedit) setup for cycling
            readline.parse_and_bind("bind ^I menu-complete")
        else:
            # GNU Readline setup for cycling
            readline.parse_and_bind("tab: menu-complete")
            
        # Treat @, /, and . as part of the word for completion
        delims = readline.get_completer_delims()
        for char in "@/.-":
            delims = delims.replace(char, "")
        readline.set_completer_delims(delims)

    def _completer(self, text, state):
        """Readline completer for @mentions and slash commands."""
        cmds = ["/exit", "/quit", "/clear", "/history", "/reindex", "/model"]
        
        if text.startswith("@"):
            query = text[1:]
            options = []
            
            # 1. Match by filename first (Claude-like)
            for fname, paths in self.filename_to_path.items():
                if fname.startswith(query):
                    for p in paths:
                        options.append(f"@{p}")
            
            # 2. Match by path if no filename matches or to be thorough
            # We use a set to avoid duplicates from step 1
            path_matches = [f for f in self.project_files if text in f and f not in options]
            options.extend(path_matches)
            
            # Sort options: prioritize shorter paths for same filename
            options.sort(key=lambda x: (len(x.split('/')), x))
            
            if state < len(options):
                return options[state]
        elif text.startswith("/"):
            options = [c for c in cmds if c.startswith(text)]
            if state < len(options):
                return options[state]
        return None

    def _confirm_tool(self, tool_name, tool_args):
        """Callback to confirm tool execution with user."""
        # Define sensitive tools
        sensitive_tools = ["write_file", "replace_file_content", "multi_replace_file_content", "run_command"]
        
        if tool_name not in sensitive_tools:
            return True
            
        permission = self.permissions.get(tool_name, "ask")
        if permission == "always":
            return True
            
        print(f"\n{format_green('Permission Request')}")
        print(f"Agent wants to execute: {tool_name}")
        print(f"Arguments: {tool_args}")
        
        while True:
            choice = input(f"Allow? [y/n/always/session] (default: y): ").strip().lower()
            if not choice:
                choice = "y"
                
            if choice == "y":
                return True
            elif choice == "n":
                return False
            elif choice in ["always", "session"]:
                self.permissions[tool_name] = "always"
                return True
            else:
                print("Invalid choice. Please enter y, n, always, or session.")

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
                    return match.group(0) # Return original if read fails
            else:
                print(f"Warning: File not found: {filepath}")
                return match.group(0)

        # Regex for @filename (simple implementation, might need refinement for spaces)
        # Matches @ followed by non-whitespace characters
        return re.sub(r'@([\w./-]+)', replace_match, user_input)

    def start(self):
        print_banner()
        print(format_green("Welcome! Type '/exit' to quit, '/clear' to reset, '/history' to view logs.\n"))
        
        while self.running:
            try:
                user_input = input(format_green("sarathi> "))
                if not user_input.strip():
                    continue

                if user_input.startswith("/"):
                    self.handle_slash_command(user_input)
                    continue

                print(f"\n{format_green('Sarathi is thinking...')}")
                
                # Pre-process input for @mentions
                processed_input = self._process_at_mentions(user_input)
                
                response = self.agent.run(processed_input)
                print(f"\n{response}\n")

            except KeyboardInterrupt:
                print("\nType '/exit' to quit.")
            except EOFError:
                self.running = False
                print("\nGoodbye!")
            except Exception as e:
                print(f"\nError: {e}")

    def handle_slash_command(self, command):
        cmd = command.split()[0].lower()
        if cmd in ["/exit", "/quit"]:
            self.running = False
            print("Goodbye!")
        elif cmd == "/clear":
            self.agent.messages = [self.agent.messages[0]] # Keep system prompt
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
    parser = subparsers.add_parser(opname, help="Start an interactive chat session")

def execute_cmd(args):
    session = ChatSession()
    session.start()
