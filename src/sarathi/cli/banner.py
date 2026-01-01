from sarathi.utils.formatters import format_bold, format_cyan, format_yellow


def print_banner():
    """Prints the Sarathi Chariot ASCII banner."""

    # User requested ejm98 ASCII art with split colors
    # Chariot (Yellow) | Horse (Cyan-ish)

    # Line 1:  ..
    l1 = format_yellow("     ..")

    # Line 2:  |_0                  ,~
    l2 = format_yellow("      |_0                  ") + format_cyan(",~")

    # Line 3:    |\_              ~/(\\
    l3 = format_yellow("        |\\_              ") + format_cyan("~/(\\\\")

    # Line 4:    |   /| ~~~______~//  @@
    l4 = (
        format_yellow("        |   /|~~~~~~")
        + format_cyan("______")
        + format_cyan("~// @@")
    )

    # Line 5:    |\-/ |===(=)===|(_|_
    l5 = (
        format_yellow("        |\\-/ |~~~~~~")
        + format_cyan("(=)===|")
        + format_cyan("(_|_")
    )

    # Line 6:   /((+ )|   |/\_  _/   \
    l6 = (
        format_yellow("       /((+ )|      ")
        + format_cyan("|/\\_  ")
        + format_cyan("_/   \\")
    )

    # Line 7:      -'    /             S A R A T H I...
    l7 = (
        format_yellow("          -'       ")
        + format_bold(format_cyan("/               "))
        + format_bold(format_cyan("S A R A T H I - Your AI Charioteer"))
    )

    banner = f"\n{l1}\n{l2}\n{l3}\n{l4}\n{l5}\n{l6}\n{l7}\n"
    print(banner)
