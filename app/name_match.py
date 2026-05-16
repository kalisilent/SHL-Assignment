import re


def normalize_name_key(name: str) -> str:
    """Alphanumeric-only key for robust assessment name matching."""
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def names_match(expected: str, actual: str) -> bool:
    expected_key = normalize_name_key(expected)
    actual_key = normalize_name_key(actual)
    if not expected_key or not actual_key:
        return False
    return expected_key in actual_key or actual_key in expected_key
