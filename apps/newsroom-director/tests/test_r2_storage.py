"""Tests for R2 edition storage with mocked boto3."""

import json
from unittest.mock import MagicMock, patch

import pytest

from newsroom_director.r2_storage import R2EditionStorage


@pytest.fixture()
def mock_s3_client():
    with patch("newsroom_director.r2_storage.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        yield mock_client


class TestR2EditionStorage:
    def test_write_edition(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        articles = {"sovereign": "Article text", "curator": "Synthesis"}
        storage.write_edition("ed-001", "2026-03-01", articles)

        mock_s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "editions/2026-03-01/ed-001.json"
        assert call_kwargs["ContentType"] == "application/json"

        body = json.loads(call_kwargs["Body"].decode("utf-8"))
        assert body["edition_id"] == "ed-001"
        assert body["date"] == "2026-03-01"
        assert body["articles"]["sovereign"] == "Article text"

    def test_list_editions(self, mock_s3_client):
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "editions/2026-03-01/ed-001.json",
                    "LastModified": "2026-03-01T06:00:00Z",
                },
                {
                    "Key": "editions/2026-03-02/ed-002.json",
                    "LastModified": "2026-03-02T06:00:00Z",
                },
            ]
        }

        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        editions = storage.list_editions()
        assert len(editions) == 2
        assert editions[0]["key"] == "editions/2026-03-01/ed-001.json"

    def test_list_editions_empty(self, mock_s3_client):
        mock_s3_client.list_objects_v2.return_value = {}

        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        editions = storage.list_editions()
        assert editions == []

    def test_endpoint_url_uses_account_id(self):
        with patch("newsroom_director.r2_storage.boto3") as mock_boto3:
            R2EditionStorage(
                account_id="my-account",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="bucket",
            )
            call_kwargs = mock_boto3.client.call_args[1]
            assert (
                call_kwargs["endpoint_url"]
                == "https://my-account.r2.cloudflarestorage.com"
            )

    def test_write_edition_json_format(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        storage.write_edition("ed-002", "2026-03-02", {"owner": "Markets up"})

        body_bytes = mock_s3_client.put_object.call_args[1]["Body"]
        data = json.loads(body_bytes.decode("utf-8"))
        assert "edition_id" in data
        assert "date" in data
        assert "articles" in data

    def test_write_image_returns_custom_domain_url(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
            public_url="https://editions.example.com",
        )

        url = storage.write_image("2026-03-01", "sovereign", "hero.webp", b"img")

        assert url == "https://editions.example.com/editions/2026-03-01/sovereign/hero.webp"
        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "image/webp"
        assert call_kwargs["CacheControl"] == "public, max-age=31536000, immutable"

    def test_write_image_strips_trailing_slash(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
            public_url="https://editions.example.com/",
        )

        url = storage.write_image("2026-03-01", "owner", "0.webp", b"img")

        assert url == "https://editions.example.com/editions/2026-03-01/owner/0.webp"

    def test_write_index(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        index = [
            {"edition_id": "2026-03-02", "date": "2026-03-02", "newspaper_ids": ["sovereign"]},
            {"edition_id": "2026-03-01", "date": "2026-03-01", "newspaper_ids": ["owner"]},
        ]
        storage.write_index(index)

        call_kwargs = mock_s3_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "editions/index.json"
        assert call_kwargs["ContentType"] == "application/json"

        body = json.loads(call_kwargs["Body"].decode("utf-8"))
        assert len(body) == 2
        assert body[0]["edition_id"] == "2026-03-02"

    def test_write_index_empty(self, mock_s3_client):
        storage = R2EditionStorage(
            account_id="test-acct",
            access_key_id="key",
            secret_access_key="secret",
            bucket_name="test-bucket",
        )

        storage.write_index([])

        body_bytes = mock_s3_client.put_object.call_args[1]["Body"]
        data = json.loads(body_bytes.decode("utf-8"))
        assert data == []
