"""Bluesky channel — posts via the AT Protocol."""

from __future__ import annotations

import logging

from .base import ChannelStrategy, PostResult

logger = logging.getLogger(__name__)


class BlueskyChannel(ChannelStrategy):
    """Posts to Bluesky via the atproto SDK."""

    # Bluesky post character limit (grapheme count).
    MAX_POST_LENGTH = 300

    def __init__(self, handle: str, app_password: str) -> None:
        self._handle = handle
        self._app_password = app_password
        self._client = None

    def _get_client(self):
        if self._client is None:
            from atproto import Client

            self._client = Client()
            self._client.login(self._handle, self._app_password)
            logger.info("Bluesky login successful for %s", self._handle)
        return self._client

    @property
    def channel_name(self) -> str:
        return "bluesky"

    def post(self, text: str) -> PostResult:
        try:
            client = self._get_client()
            text = text[: self.MAX_POST_LENGTH]
            response = client.send_post(text=text)
            post_uri = response.uri
            # Build web URL from AT URI: at://did/app.bsky.feed.post/rkey
            rkey = post_uri.rsplit("/", 1)[-1] if post_uri else ""
            post_url = f"https://bsky.app/profile/{self._handle}/post/{rkey}"
            logger.info(
                "Bluesky post published: %s",
                post_url,
                extra={"post_uri": post_uri, "post_url": post_url},
            )
            return PostResult(
                success=True,
                post_id=post_uri,
                post_url=post_url,
            )
        except Exception as exc:
            logger.warning(
                "Bluesky post failed: %s | text: %.100s",
                exc,
                text,
                exc_info=True,
            )
            return PostResult(success=False, error=str(exc))

    def post_thread(self, texts: list[str]) -> list[PostResult]:
        results: list[PostResult] = []
        parent_ref = None
        root_ref = None

        try:
            from atproto import models

            client = self._get_client()

            for i, text in enumerate(texts):
                text = text[: self.MAX_POST_LENGTH]

                reply_to = None
                if parent_ref is not None and root_ref is not None:
                    reply_to = models.AppBskyFeedPost.ReplyRef(
                        parent=parent_ref,
                        root=root_ref,
                    )

                response = client.send_post(text=text, reply_to=reply_to)
                post_uri = response.uri

                rkey = post_uri.rsplit("/", 1)[-1] if post_uri else ""
                post_url = f"https://bsky.app/profile/{self._handle}/post/{rkey}"

                # Build strong ref for threading
                ref = models.create_strong_ref(response)
                parent_ref = ref
                if root_ref is None:
                    root_ref = ref

                logger.info(
                    "Bluesky thread post %d/%d published: %s",
                    i + 1,
                    len(texts),
                    post_url,
                )
                results.append(PostResult(
                    success=True,
                    post_id=post_uri,
                    post_url=post_url,
                ))

        except Exception as exc:
            logger.warning(
                "Bluesky thread failed at post %d: %s",
                len(results) + 1,
                exc,
                exc_info=True,
            )
            # The AT Protocol has no concept of transactions: posts 0..N-1 are
            # already live on Bluesky and cannot be rolled back. We mark the
            # remaining posts as failed so the DB accurately reflects what was
            # actually published.
            for _ in range(len(texts) - len(results)):
                results.append(PostResult(success=False, error=str(exc)))

        return results
