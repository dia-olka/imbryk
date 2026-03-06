"""Pricing calculation for prompt routing."""

BASE_PRICE = 1.00


def calculate_cost(newspapers_reached: int, weight_multiplier: int = 1) -> float:
    """Calculate the cost based on number of newspapers reached and weight multiplier.

    The weight multiplier lets users boost their prompt's editorial priority.
    A higher multiplier increases the stored payment amount, which flows into
    the newsroom-director's scorer (payment_amount_norm × uniqueness_bonus).
    """
    return BASE_PRICE * newspapers_reached * weight_multiplier
