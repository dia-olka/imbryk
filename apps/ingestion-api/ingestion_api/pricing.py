"""Pricing calculation for prompt routing."""

BASE_PRICE_CENTS = 100  # $1.00 in cents
BASE_PRICE = BASE_PRICE_CENTS / 100  # $1.00 — for display / backward compat


def calculate_cost_cents(newspapers_reached: int, weight_multiplier: int = 1) -> int:
    """Calculate the cost in cents based on number of newspapers reached and weight multiplier.

    Stripe requires amounts in the smallest currency unit (cents for USD).
    The weight multiplier lets users boost their prompt's editorial priority.
    A higher multiplier increases the stored payment amount, which flows into
    the newsroom-director's scorer (payment_amount_norm × uniqueness_bonus).
    """
    return BASE_PRICE_CENTS * newspapers_reached * weight_multiplier


def calculate_cost(newspapers_reached: int, weight_multiplier: int = 1) -> float:
    """Calculate the cost in dollars (for display and DB storage)."""
    return calculate_cost_cents(newspapers_reached, weight_multiplier) / 100
