"""A clean Python file with no issues."""


def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        Sum of a and b.
    """
    return a + b


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial: int = 0) -> None:
        """Initialize calculator with optional initial value.

        Args:
            initial: Starting value, defaults to 0.
        """
        self.value = initial

    def add(self, x: int) -> int:
        """Add x to current value.

        Args:
            x: Value to add.

        Returns:
            New current value.
        """
        self.value += x
        return self.value

    def reset(self) -> None:
        """Reset calculator to zero."""
        self.value = 0
