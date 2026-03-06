"""Tests for pricing calculation."""

from ingestion_api.pricing import BASE_PRICE, calculate_cost


def test_zero_newspapers():
    assert calculate_cost(0) == 0.0


def test_single_newspaper():
    assert calculate_cost(1) == BASE_PRICE


def test_multiple_newspapers():
    assert calculate_cost(4) == BASE_PRICE * 4


# --- Weight multiplier tests ---


def test_multiplier_default_is_one():
    """calculate_cost with no multiplier should behave like multiplier=1."""
    assert calculate_cost(3) == calculate_cost(3, 1)


def test_multiplier_scales_price():
    assert calculate_cost(2, 10) == BASE_PRICE * 2 * 10


def test_multiplier_one_is_baseline():
    assert calculate_cost(5, 1) == BASE_PRICE * 5


def test_multiplier_max():
    assert calculate_cost(1, 100) == BASE_PRICE * 100
