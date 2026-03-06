"""Tests for image generation clients."""

from unittest.mock import MagicMock, patch

from newsroom_director.image_gen.client import (
    ImagenClient,
    StubImageClient,
)


class TestStubImageClient:
    def test_returns_webp_bytes_by_default(self):
        client = StubImageClient()
        result = client.generate("A photo of a cat")

        assert result is not None
        assert result.startswith(b"RIFF")
        assert b"WEBP" in result

    def test_tracks_calls(self):
        client = StubImageClient()
        client.generate("prompt 1")
        client.generate("prompt 2")

        assert client._calls == ["prompt 1", "prompt 2"]

    def test_returns_none_when_should_fail(self):
        client = StubImageClient(should_fail=True)
        result = client.generate("A photo of a cat")

        assert result is None
        assert client._calls == ["A photo of a cat"]


class TestImagenClient:
    def test_lazy_init(self):
        """Gen AI client is not created until generate() is called."""
        client = ImagenClient(project="test-project", location="global")
        assert client._client is None

    @patch("newsroom_director.image_gen.client.with_retry")
    def test_generate_success(self, mock_with_retry):
        fake_bytes = b"fake-image-data"
        mock_with_retry.return_value = fake_bytes

        with patch(
            "newsroom_director.image_gen.client.ImagenClient._get_client"
        ):
            client = ImagenClient(project="test-project")
            client._client = MagicMock()
            result = client.generate("A newspaper front page")

        assert result == fake_bytes
        mock_with_retry.assert_called_once()

    def test_generate_returns_none_on_exception(self):
        client = ImagenClient(project="test-project")

        with patch.object(
            client, "_get_client", side_effect=Exception("Gen AI error")
        ):
            result = client.generate("A prompt")

        assert result is None

    @patch("newsroom_director.image_gen.client.with_retry")
    def test_generate_returns_none_on_retry_failure(self, mock_with_retry):
        mock_with_retry.side_effect = Exception("max retries exceeded")

        with patch(
            "newsroom_director.image_gen.client.ImagenClient._get_client"
        ):
            client = ImagenClient(project="test-project")
            client._client = MagicMock()
            result = client.generate("A prompt")

        assert result is None

    def test_init_client_called_once(self):
        """_get_client is idempotent — subsequent calls return the same client."""
        client = ImagenClient(project="test-project")

        mock_genai = MagicMock()
        mock_genai_client = MagicMock()
        mock_genai.Client.return_value = mock_genai_client

        with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": mock_genai}):
            # Patch the import inside _get_client
            with patch("google.genai.Client", mock_genai.Client):
                result1 = client._get_client()
                result2 = client._get_client()

            assert result1 is result2
            assert client._client is not None
