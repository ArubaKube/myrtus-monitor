"""The utils module provides utility functions for the monitoring service."""

import sys


def cexit(msg: str, code: int = 1) -> None:
    """Exit the program with a message and a specific exit code.

    Args:
        msg (str): The message to display before exiting.
        code (int): The exit code. Defaults to 1.
    """
    print(msg, file=sys.stderr)  # noqa: T201 # Print is ok in this context
    sys.exit(code)
