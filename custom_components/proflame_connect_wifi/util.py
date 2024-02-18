"""General helper objects used by the rest of the module."""

from typing import Any, Self


def coalesce(*args: list[Any]) -> Any | None:
    """Return the first non-null argument."""
    try:
        return next(x for x in args if x is not None)
    except StopIteration:
        return None

def constrain(value: int, min_value: int, max_value: int):
    """Constrain a number to a specified range."""
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

class Temperature:
    """Helper class for interacting with temperature."""

    @staticmethod
    def celcius(value) -> Self:
        """Create temperature from Celcius value."""
        return Temperature(value)

    @staticmethod
    def fahrenheit(value) -> Self:
        """Create temperature from Fahrenheit value."""
        return Temperature((value - 32) * 5/9)

    def __init__(self, celcius) -> None:
        """Create new instance of the Temperature class."""
        self._value = celcius

    def to_celcius(self) -> float:
        """Return the temperature value as Celcius."""
        return self._value

    def to_fahrenheit(self) -> float:
        """Return the temperature value as Fahrenheit."""
        return (self._value * 9/5) + 32
