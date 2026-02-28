"""Newsroom director unit tests."""

import pytest

from newsroom_director.main import run_morning_press


def test_run_morning_press_not_implemented():
    with pytest.raises(NotImplementedError):
        run_morning_press()
