import re
from pathlib import Path


def _process_at_mentions(user_input):
    def replace_match(match):
        filepath = match.group(1)
        path = Path(filepath)
        if path.exists() and path.is_file():
            try:
                content = "CONTENT_FOUND"
                return f"\n--- Context from {filepath} ---\n{content}\n---------------------------------\n"
            except Exception as e:
                return match.group(0)
        else:
            print(f"Warning: File not found: {filepath}")
            return match.group(0)

    return re.sub(r"@([\w./-]+)", replace_match, user_input)


# Test cases
print(f"Test 1: {_process_at_mentions('Check @README.md please')}")
print(f"Test 2: {_process_at_mentions('Check @README.md ')}")
print(f"Test 3: {_process_at_mentions('Check @src/sarathi/cli/chat_cli.py')}")

# Test with duplicate @ if completion failed
print(f"Test 4: {_process_at_mentions('Check @@README.md')}")
