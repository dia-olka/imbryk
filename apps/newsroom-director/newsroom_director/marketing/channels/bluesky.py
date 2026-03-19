"""Bluesky channel — posts via the AT Protocol."""

from __future__ import annotations

import logging
import re
import urllib.request
from html.parser import HTMLParser

from .base import ChannelStrategy, PostResult

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://[^\s\)\]\}>\"']+")


class _OGParser(HTMLParser):
    """Minimal HTML parser that extracts OpenGraph meta tags."""

    def __init__(self):
        super().__init__()
        self.og: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag != "meta":
            return
        attr_dict = dict(attrs)
        prop = attr_dict.get("property", "")
        content = attr_dict.get("content")
        if prop.startswith("og:") and content:
            self.og[prop] = content


def _fetch_og_metadata(url: str) -> dict[str, str]:
    """Fetch OpenGraph metadata (title, description, image) from *url*.

    Returns a dict with keys ``og:title``, ``og:description``, ``og:image``
    (any of which may be absent).
    """
    req = urllib.request.Request(url, headers={"User-Agent": "ImbrykBot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        # Read only the first 64 KB — OG tags are always in <head>.
        html = resp.read(65_536).decode("utf-8", errors="replace")
    parser = _OGParser()
    parser.feed(html)
    return parser.og


def _build_rich_text(text: str):
    """Convert plain *text* into a ``TextBuilder`` with clickable URL facets."""
    from atproto import client_utils

    tb = client_utils.TextBuilder()
    last_end = 0
    for m in _URL_RE.finditer(text):
        if m.start() > last_end:
            tb.text(text[last_end : m.start()])
        tb.link(m.group(), m.group())
        last_end = m.end()
    if last_end < len(text):
        tb.text(text[last_end:])
    return tb


def _build_embed_card(url: str, client):
    """Fetch OG metadata for *url* and return an embed-external record.

    Returns ``None`` if metadata cannot be fetched or is incomplete.
    """
    from atproto import models

    try:
        og = _fetch_og_metadata(url)
    except Exception:
        logger.debug("Failed to fetch OG metadata for %s", url, exc_info=True)
        return None

    title = og.get("og:title", "")
    description = og.get("og:description", "")
    if not title:
        return None

    thumb = None
    image_url = og.get("og:image")
    if image_url:
        try:
            req = urllib.request.Request(
                image_url, headers={"User-Agent": "ImbrykBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                image_data = resp.read()
            upload_resp = client.upload_blob(image_data)
            thumb = upload_resp.blob
        except Exception:
            logger.debug(
                "Failed to fetch/upload OG image %s", image_url, exc_info=True
            )

    return models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            uri=url,
            title=title,
            description=description,
            thumb=thumb,
        )
    )


def _first_url(text: str) -> str | None:
    """Return the first URL found in *text*, or ``None``."""
    m = _URL_RE.search(text)
    return m.group() if m else None


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

    def post(self, text: str, url: str | None = None) -> PostResult:
        try:
            client = self._get_client()
            text = text[: self.MAX_POST_LENGTH]

            # Build rich text with clickable URL facets
            rich_text = _build_rich_text(text)

            # Build embed card — prefer explicit URL, fall back to first in text
            embed_url = url or _first_url(text)
            embed = _build_embed_card(embed_url, client) if embed_url else None

            response = client.send_post(
                text=rich_text, embed=embed
            )
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

    def post_thread(
        self, texts: list[str], urls: list[str] | None = None,
    ) -> list[PostResult]:
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

                # Build rich text with clickable URL facets
                rich_text = _build_rich_text(text)

                # Build embed card — prefer explicit URL, fall back to first in text
                explicit_url = urls[i] if urls and i < len(urls) else None
                embed_url = explicit_url or _first_url(text)
                embed = _build_embed_card(embed_url, client) if embed_url else None

                response = client.send_post(
                    text=rich_text, reply_to=reply_to, embed=embed
                )
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
