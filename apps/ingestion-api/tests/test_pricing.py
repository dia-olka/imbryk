"""Tests for pricing calculation."""

from ingestion_api.pricing import BASE_PRICE, calculate_cost


def test_zero_newspapers():
    assert calculate_cost(0) == 0.0


def test_single_newspaper():
    assert calculate_cost(1) == BASE_PRICE


def test_multiple_newspapers():
    assert calculate_cost(4) == BASE_PRICE * 4
