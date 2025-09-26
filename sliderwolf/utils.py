from typing import Any

__all__ = ("clamp",)


def clamp(value: Any, min_value: Any, max_value: Any) -> Any:
    """
    Clamp a value between a minimum and a maximum
    """
    return max(min(value, max_value), min_value)
