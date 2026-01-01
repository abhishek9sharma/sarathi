from black import FileMode, format_str


def format_green(text):
    """
    Formats the given text in green color.

    :param text: The text to be printed in green.
    """
    green = "\x1b[32m"
    reset = "\x1b[0m"
    return f"{green}{text}{reset}"


def format_cyan(text):
    """Formats text in cyan."""
    cyan = "\x1b[36m"
    reset = "\x1b[0m"
    return f"{cyan}{text}{reset}"


def format_yellow(text):
    """Formats text in yellow."""
    yellow = "\x1b[33m"
    reset = "\x1b[0m"
    return f"{yellow}{text}{reset}"


def format_bold(text):
    """Formats text in bold."""
    bold = "\x1b[1m"
    reset = "\x1b[0m"
    return f"{bold}{text}{reset}"


def format_code(code):
    """
    Formats the input code using the specified mode.

    Args:
        code: The input code to be formatted.

    Returns:
        The formatted code.
    """
    out = format_str(code, mode=FileMode())
    return out


def clean_llm_response(text):
    """
    Cleans the LLM response by removing markdown code blocks (```).

    Args:
        text (str): The raw response from LLM.

    Returns:
        str: The cleaned text.
    """
    if not text:
        return text

    # Strip leading/trailing whitespace
    text = text.strip()

    # Check for triple backtick blocks
    if text.startswith("```") and text.endswith("```"):
        # Remove the first line if it contains a language identifier (e.g. ```text or ```markdown)
        lines = text.splitlines()
        content_lines = lines[1:-1]
        return "\n".join(content_lines).strip()

    return text
