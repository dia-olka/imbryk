"""Abstract channel strategy for social media posting."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PostResult:
    """Result of a single post attempt."""

    success: bool
    post_id: str | None = None
    post_url: str | None = None
    error: str | None = None


class ChannelStrategy(ABC):
    """Abstract base for social media channel backends."""

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the channel identifier (e.g. 'bluesky', 'twitter')."""

    @abstractmethod
    def post(self, text: str) -> PostResult:
        """Publish a single post. Returns result with post ID/URL on success."""

    @abstractmethod
    def post_thread(self, texts: list[str]) -> list[PostResult]:
        """Publish a thread (sequence of linked posts). Returns one result per post."""


class StubChannel(ChannelStrategy):
    """In-memory stub for testing."""

    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.posts: list[str] = []
        self.threads: list[list[str]] = []

    @property
    def channel_name(self) -> str:
        return "stub"

    def post(self, text: str) -> PostResult:
        self.posts.append(text)
        if self._should_fail:
            return PostResult(success=False, error="stub failure")
        return PostResult(
            success=True,
            post_id=f"stub-{len(self.posts)}",
            post_url=f"https://stub.example.com/post/{len(self.posts)}",
        )

    def post_thread(self, texts: list[str]) -> list[PostResult]:
        self.threads.append(texts)
        results = []
        for i, text in enumerate(texts):
            self.posts.append(text)
            if self._should_fail:
                results.append(PostResult(success=False, error="stub failure"))
            else:
                results.append(PostResult(
                    success=True,
                    post_id=f"stub-thread-{len(self.threads)}-{i}",
                    post_url=f"https://stub.example.com/post/thread-{len(self.threads)}-{i}",
                ))
        return results
