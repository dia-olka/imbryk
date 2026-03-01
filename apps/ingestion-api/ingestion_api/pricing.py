"""Pricing calculation for prompt routing."""

BASE_PRICE = 1.00


def calculate_cost(newspapers_reached: int) -> float:
    """Calculate the cost based on number of newspapers reached."""
    return BASE_PRICE * newspapers_reached
