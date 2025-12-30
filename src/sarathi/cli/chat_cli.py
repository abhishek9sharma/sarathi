import os
import sys
import re
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
        elif cmd == "/history":
            for msg in self.agent.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content") or ""
                content_preview = content[:50] + "..." if content else ""
                if not content and msg.get("tool_calls"):
                    content_preview = f"<{len(msg['tool_calls'])} tool calls>"
                print(f"[{role}]: {content_preview}")
        else:
            print(f"Unknown command: {cmd}")

def setup_args(subparsers, opname="chat"):
    parser = subparsers.add_parser(opname, help="Start an interactive chat session")

def execute_cmd(args):
    session = ChatSession()
    session.start()
