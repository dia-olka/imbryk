"""Cloudflare R2 edition storage backend."""

from __future__ import annotations

import json
import logging

import boto3

from .config import (
    R2_ACCESS_KEY_ID,
    R2_ACCOUNT_ID,
    R2_BUCKET_NAME,
    R2_SECRET_ACCESS_KEY,
)
from .storage import EditionStorage

logger = logging.getLogger(__name__)


class R2EditionStorage(EditionStorage):
    """Writes edition JSON to Cloudflare R2 via S3-compatible API."""

    def __init__(
        self,
        account_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        bucket_name: str | None = None,
    ) -> None:
        acct = account_id or R2_ACCOUNT_ID
        self._bucket = bucket_name or R2_BUCKET_NAME
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{acct}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id or R2_ACCESS_KEY_ID,
            aws_secret_access_key=secret_access_key or R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )

    def write_edition(
        self, edition_id: str, date: str, articles: dict[str, str]
    ) -> None:
        key = f"editions/{date}/{edition_id}.json"
        body = json.dumps(
            {"edition_id": edition_id, "date": date, "articles": articles},
            ensure_ascii=False,
        )
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        logger.info(
            "Edition written to R2",
            extra={"edition_id": edition_id, "key": key},
        )

    def list_editions(self) -> list[dict]:
        response = self._client.list_objects_v2(
            Bucket=self._bucket, Prefix="editions/"
        )
        editions: list[dict] = []
        for obj in response.get("Contents", []):
            editions.append(
                {"key": obj["Key"], "last_modified": str(obj["LastModified"])}
            )
        return editions
