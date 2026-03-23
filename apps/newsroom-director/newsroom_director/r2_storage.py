"""Cloudflare R2 edition storage backend."""

from __future__ import annotations

import json
import logging

import boto3

from .config import (
    R2_ACCESS_KEY_ID,
    R2_ACCOUNT_ID,
    R2_BUCKET_NAME,
    R2_PUBLIC_URL,
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
        public_url: str | None = None,
    ) -> None:
        acct = account_id or R2_ACCOUNT_ID
        self._bucket = bucket_name or R2_BUCKET_NAME
        self._public_url = (public_url or R2_PUBLIC_URL).rstrip("/")
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

    @staticmethod
    def _content_type_for(filename: str) -> str:
        if filename.endswith(".webp"):
            return "image/webp"
        if filename.endswith(".png"):
            return "image/png"
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            return "image/jpeg"
        return "application/octet-stream"

    def write_image(
        self,
        edition_id: str,
        newspaper_id: str,
        filename: str,
        image_bytes: bytes,
    ) -> str:
        key = f"editions/{edition_id}/{newspaper_id}/{filename}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=image_bytes,
            ContentType=self._content_type_for(filename),
            CacheControl="public, max-age=31536000, immutable",
        )
        logger.info(
            "Image written to R2",
            extra={
                "edition_id": edition_id,
                "newspaper_id": newspaper_id,
                "key": key,
            },
        )
        return key

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

    def write_index(self, editions: list[dict]) -> None:
        """Write editions/index.json manifest to R2."""
        body = json.dumps(editions, ensure_ascii=False)
        self._client.put_object(
            Bucket=self._bucket,
            Key="editions/index.json",
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        logger.info(
            "Index manifest written to R2",
            extra={"edition_count": len(editions)},
        )

    def read_json(self, key: str) -> dict | list | None:
        """Read a JSON object from R2 by key. Returns None if missing."""
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=key)
            return json.loads(resp["Body"].read().decode("utf-8"))
        except self._client.exceptions.NoSuchKey:
            return None
        except Exception:
            logger.warning("Failed to read %s from R2", key, exc_info=True)
            return None

    def write_raw(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Write raw bytes to R2 at *key*."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
