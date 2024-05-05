from black import FileMode, format_str


def format_green(text):
    """
    Formats the given text in green color.

    :param text: The text to be printed in green.
    """
    green = "\x1b[32m"
    reset = "\x1b[0m"
    return f"{green}{text}{reset}"


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
