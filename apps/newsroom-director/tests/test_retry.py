"""Tests for the retry module."""

from unittest.mock import patch

import pytest

from newsroom_director.retry import _is_rate_limit, _is_retryable, with_retry


class _ServerError(Exception):
    def __init__(self):
        self.code = 503


class _RateLimitError(Exception):
    def __init__(self):
        self.code = 429


class _NonRetryable(Exception):
    pass


class TestIsRetryable:
    def test_server_error(self):
        assert _is_retryable(_ServerError()) is True

    def test_non_retryable(self):
        assert _is_retryable(_NonRetryable()) is False

    def test_rate_limit_is_retryable(self):
        assert _is_retryable(_RateLimitError()) is True

    def test_500_is_retryable(self):
        class Err(Exception):
            def __init__(self):
                self.code = 500

        assert _is_retryable(Err()) is True

    def test_502_is_retryable(self):
        class Err(Exception):
            def __init__(self):
                self.code = 502

        assert _is_retryable(Err()) is True

    def test_400_not_retryable(self):
        """Safety rejections (400) must not be retried."""

        class Err(Exception):
            def __init__(self):
                self.code = 400

        assert _is_retryable(Err()) is False

    def test_no_code_not_retryable(self):
        assert _is_retryable(RuntimeError("boom")) is False


class TestIsRateLimit:
    def test_429_is_rate_limit(self):
        assert _is_rate_limit(_RateLimitError()) is True

    def test_server_error_not_rate_limit(self):
        assert _is_rate_limit(_ServerError()) is False

    def test_no_code_not_rate_limit(self):
        assert _is_rate_limit(_NonRetryable()) is False


class TestWithRetry:
    def test_succeeds_first_try(self):
        with patch("newsroom_director.retry.throttle"):
            result = with_retry(lambda: 42)
        assert result == 42

    @patch("newsroom_director.retry.throttle")
    @patch("newsroom_director.retry.time.sleep")
    def test_retries_on_transient_error(self, mock_sleep, _mock_throttle):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise _ServerError()
            return "ok"

        result = with_retry(flaky, max_retries=3, backoff_base=1.0)
        assert result == "ok"
        assert call_count == 3

    def test_raises_non_retryable_immediately(self):
        def bad():
            raise _NonRetryable("nope")

        with pytest.raises(_NonRetryable), patch("newsroom_director.retry.throttle"):
            with_retry(bad, max_retries=3)

    @patch("newsroom_director.retry.throttle")
    @patch("newsroom_director.retry.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep, _mock_throttle):
        def always_fail():
            raise _ServerError()

        with pytest.raises(_ServerError):
            with_retry(always_fail, max_retries=2, backoff_base=1.0)

    @patch("newsroom_director.retry.throttle")
    @patch("newsroom_director.retry.time.sleep")
    def test_passes_args_and_kwargs(self, mock_sleep, _mock_throttle):
        def add(a, b, extra=0):
            return a + b + extra

        result = with_retry(add, 1, 2, extra=10)
        assert result == 13

    @patch("newsroom_director.retry.throttle")
    @patch("newsroom_director.retry.time.sleep")
    def test_exponential_backoff_transient(self, mock_sleep, _mock_throttle):
        """Non-rate-limit errors use standard exponential backoff."""
        call_count = 0

        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise _ServerError()
            return "done"

        with_retry(fail_twice, max_retries=3, backoff_base=2.0)
        assert mock_sleep.call_count == 2
        # First delay: 2^0 + jitter (1.0 to 2.0)
        assert 1.0 <= mock_sleep.call_args_list[0][0][0] <= 2.0
        # Second delay: 2^1 + jitter (2.0 to 3.0)
        assert 2.0 <= mock_sleep.call_args_list[1][0][0] <= 3.0

    @patch("newsroom_director.retry.throttle")
    @patch("newsroom_director.retry.time.sleep")
    def test_rate_limit_uses_longer_backoff(self, mock_sleep, _mock_throttle):
        """429 errors use a longer backoff."""
        call_count = 0

        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _RateLimitError()
            return "ok"

        with_retry(fail_once, max_retries=3, backoff_base=2.0)
        assert mock_sleep.call_count == 1
        # First delay: 15 * 2^0 + jitter(0,3) → 15.0 to 18.0
        assert 15.0 <= mock_sleep.call_args_list[0][0][0] <= 18.0
