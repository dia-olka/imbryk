"""Azure Translator client — translates text via the Azure Cognitive Services API."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from .client import TranslationResult, TranslationStrategy

logger = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = "https://api.cognitive.microsofttranslator.com"


class AzureTranslationClient(TranslationStrategy):
    """Calls Azure Translator to translate text segments.

    Designed for the F0 (free) tier limits:
      - 2,000,000 characters / month
      - 33,300 characters / minute
      - 10,000 characters / request
      - Rate limit resets 60 seconds after a 429

    Throttles inter-request delay based on characters sent to stay within
    the per-minute cap. Respects ``Retry-After`` on 429 responses.

    See: https://learn.microsoft.com/en-us/azure/ai-services/translator/reference/v3-0-translate
    """

    # F0 free tier: 33,300 chars/minute
    _CHARS_PER_MINUTE = 33_300
    # Default wait when a 429 doesn't include a Retry-After header
    _RATE_LIMIT_RESET_S = 60

    def __init__(
        self,
        subscription_key: str,
        region: str,
        endpoint: str = _DEFAULT_ENDPOINT,
    ) -> None:
        self._subscription_key = subscription_key
        self._region = region
        self._endpoint = endpoint.rstrip("/")
        self._last_request_time: float = 0.0
        self._last_request_chars: int = 0

    @property
    def provider_name(self) -> str:
        return "azure"

    @property
    def max_batch_size(self) -> int:
        return 100

    @property
    def max_chars_per_request(self) -> int:
        return 10_000

    def _throttle(self, chars_to_send: int) -> None:
        """Wait if needed to stay within the per-minute character rate limit.

        After sending N chars, we must wait at least N / (33300/60) seconds
        before the next request to avoid exceeding 33,300 chars/minute.
        """
        if self._last_request_chars == 0:
            return
        min_gap = self._last_request_chars / (self._CHARS_PER_MINUTE / 60)
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < min_gap:
            time.sleep(min_gap - elapsed)

    def translate_batch(
        self,
        texts: list[str],
        target_lang: str,
        source_lang: str = "en",
    ) -> list[TranslationResult | None]:
        if not texts:
            return []

        url = (
            f"{self._endpoint}/translate"
            f"?api-version=3.0&from={source_lang}&to={target_lang}"
        )
        body = [{"Text": t} for t in texts]

        headers = {
            "Ocp-Apim-Subscription-Key": self._subscription_key,
            "Ocp-Apim-Subscription-Region": self._region,
            "Content-Type": "application/json",
        }

        total_chars = sum(len(t) for t in texts)
        max_retries = 3
        response_data = None
        for attempt in range(max_retries):
            self._throttle(total_chars)
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                    response_data = json.loads(resp.read().decode("utf-8"))
                self._last_request_time = time.monotonic()
                self._last_request_chars = total_chars
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    retry_after = e.headers.get("Retry-After")
                    wait = int(retry_after) if retry_after else self._RATE_LIMIT_RESET_S
                    logger.warning("Rate limited (429), waiting %ds before retry", wait)
                    time.sleep(wait)
                    self._last_request_time = time.monotonic()
                    self._last_request_chars = 0
                    continue
                logger.warning(
                    "Azure Translator API call failed for %d texts -> %s",
                    len(texts), target_lang, exc_info=True,
                )
                return [None] * len(texts)
            except Exception:
                logger.warning(
                    "Azure Translator API call failed for %d texts -> %s",
                    len(texts), target_lang, exc_info=True,
                )
                return [None] * len(texts)

        if response_data is None:
            return [None] * len(texts)

        results: list[TranslationResult | None] = []
        for i, item in enumerate(response_data):
            try:
                translations = item.get("translations", [])
                if not translations:
                    results.append(None)
                    continue
                translated_text = translations[0].get("text", "")
                results.append(TranslationResult(
                    source_text=texts[i],
                    translated_text=translated_text,
                    target_lang=target_lang,
                    chars_used=len(texts[i]),
                ))
            except (IndexError, KeyError, TypeError):
                logger.warning(
                    "Failed to parse Azure response for segment %d", i,
                    exc_info=True,
                )
                results.append(None)

        # Pad if response is shorter than input (shouldn't happen, but be safe)
        while len(results) < len(texts):
            results.append(None)

        return results
