def format_green(text):
    """
    Formats the given text in green color.

    :param text: The text to be printed in green.
    """
    # ANSI escape code for green text
    green = "\033[32m"
    # ANSI escape code to reset the color back to default
    reset = "\033[0m"
    return f"{green}{text}{reset}"
