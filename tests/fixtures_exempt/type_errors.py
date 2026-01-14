"""Test fixture with type errors for mypy testing."""


def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def bad_return() -> int:
    """This function has a type error."""
    return "not an int"  # type error: incompatible return type


def missing_annotation(x):
    """This function has missing type annotations."""
    return x * 2


result: str = add_numbers(1, 2)  # type error: incompatible assignment
