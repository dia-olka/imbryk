"""Azure Translator client — translates text via the Azure Cognitive Services API."""

from __future__ import annotations

import json
import logging
import urllib.request

from .client import TranslationResult, TranslationStrategy

logger = logging.getLogger(__name__)

_DEFAULT_ENDPOINT = "https://api.cognitive.microsofttranslator.com"


class AzureTranslationClient(TranslationStrategy):
    """Calls Azure Translator to translate text segments.

    Uses the batch endpoint (up to 25 segments / 50K chars per request).
    See: https://learn.microsoft.com/en-us/azure/ai-services/translator/reference/v3-0-translate
    """

    def __init__(
        self,
        subscription_key: str,
        region: str,
        endpoint: str = _DEFAULT_ENDPOINT,
    ) -> None:
        self._subscription_key = subscription_key
        self._region = region
        self._endpoint = endpoint.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "azure"

    @property
    def max_batch_size(self) -> int:
        return 25

    @property
    def max_chars_per_request(self) -> int:
        return 50_000

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

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                response_data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            logger.warning(
                "Azure Translator API call failed for %d texts -> %s",
                len(texts),
                target_lang,
                exc_info=True,
            )
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
