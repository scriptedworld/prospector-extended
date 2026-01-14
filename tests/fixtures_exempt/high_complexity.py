"""Test fixture with high cognitive complexity for complexipy testing."""


def simple_function(x: int) -> int:
    """A simple function with low complexity."""
    return x * 2


def complex_function(data: list[dict], mode: str, threshold: int) -> list[str]:
    """A complex function with high cognitive complexity.

    This function intentionally has many branches and nested logic
    to trigger the complexity threshold.
    """
    results = []

    for item in data:
        if "name" not in item:
            continue

        if mode == "strict":
            if item.get("value", 0) > threshold:
                if item.get("active", False):
                    if item.get("verified", False):
                        results.append(f"strict-verified: {item['name']}")
                    else:
                        results.append(f"strict-unverified: {item['name']}")
                else:
                    if item.get("pending", False):
                        results.append(f"strict-pending: {item['name']}")
                    else:
                        results.append(f"strict-inactive: {item['name']}")
            else:
                if item.get("priority", 0) > 5:
                    results.append(f"strict-priority: {item['name']}")
                else:
                    results.append(f"strict-low: {item['name']}")
        elif mode == "relaxed":
            if item.get("value", 0) > threshold / 2:
                results.append(f"relaxed: {item['name']}")
            elif item.get("fallback", False):
                results.append(f"relaxed-fallback: {item['name']}")
            else:
                results.append(f"relaxed-skip: {item['name']}")
        else:
            if threshold > 100:
                if item.get("special", False):
                    results.append(f"default-special: {item['name']}")
                else:
                    results.append(f"default-normal: {item['name']}")
            else:
                results.append(f"default: {item['name']}")

    return results
