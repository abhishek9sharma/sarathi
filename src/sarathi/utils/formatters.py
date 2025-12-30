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
