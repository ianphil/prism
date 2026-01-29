"""Tests for Ollama chat client."""

import httpx
import pytest

from prism.llm.client import OllamaChatClient


class TestOllamaChatClientInit:
    """Tests for OllamaChatClient initialization."""

    def test_default_initialization(self) -> None:
        """Client should have sensible defaults."""
        client = OllamaChatClient()
        assert client.endpoint == "http://localhost:11434"
        assert client.model == "mistral"
        assert client.timeout == 30.0

    def test_custom_initialization(self) -> None:
        """Client should accept custom parameters."""
        client = OllamaChatClient(
            endpoint="http://custom:8080",
            model="llama3",
            timeout=60.0,
        )
        assert client.endpoint == "http://custom:8080"
        assert client.model == "llama3"
        assert client.timeout == 60.0

    def test_endpoint_trailing_slash_stripped(self) -> None:
        """Trailing slash on endpoint should be stripped."""
        client = OllamaChatClient(endpoint="http://localhost:11434/")
        assert client.endpoint == "http://localhost:11434"


class TestOllamaChatClientChat:
    """Tests for OllamaChatClient.chat() method."""

    @pytest.mark.anyio
    async def test_chat_sends_correct_request(self, httpx_mock) -> None:
        """Chat should send properly formatted request to Ollama."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:11434/api/chat",
            json={
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?",
                }
            },
        )

        client = OllamaChatClient()
        messages = [{"role": "user", "content": "Hello"}]
        response = await client.chat(messages)

        assert response == "Hello! How can I help you?"

        # Verify request was made correctly
        request = httpx_mock.get_request()
        assert request is not None
        assert request.url == "http://localhost:11434/api/chat"

    @pytest.mark.anyio
    async def test_chat_includes_model_in_payload(self, httpx_mock) -> None:
        """Chat should include model name in request payload."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:11434/api/chat",
            json={"message": {"role": "assistant", "content": "Response"}},
        )

        client = OllamaChatClient(model="llama3")
        await client.chat([{"role": "user", "content": "Test"}])

        request = httpx_mock.get_request()
        import json

        payload = json.loads(request.content)
        assert payload["model"] == "llama3"

    @pytest.mark.anyio
    async def test_chat_passes_extra_kwargs(self, httpx_mock) -> None:
        """Chat should pass extra kwargs to Ollama."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:11434/api/chat",
            json={"message": {"role": "assistant", "content": "Response"}},
        )

        client = OllamaChatClient()
        await client.chat(
            [{"role": "user", "content": "Test"}],
            temperature=0.5,
        )

        request = httpx_mock.get_request()
        import json

        payload = json.loads(request.content)
        assert payload["temperature"] == 0.5

    @pytest.mark.anyio
    async def test_chat_raises_on_http_error(self, httpx_mock) -> None:
        """Chat should raise HTTPStatusError on error response."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:11434/api/chat",
            status_code=500,
        )

        client = OllamaChatClient()
        with pytest.raises(httpx.HTTPStatusError):
            await client.chat([{"role": "user", "content": "Test"}])

    @pytest.mark.anyio
    async def test_chat_raises_on_timeout(self) -> None:
        """Chat should raise exception on unreachable endpoint."""
        # Use a very short timeout and an endpoint that won't respond
        client = OllamaChatClient(
            endpoint="http://10.255.255.1:11434",  # Non-routable IP
            timeout=0.001,
        )

        # Network behavior varies - may timeout, refuse connection, or proxy error
        with pytest.raises(
            (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError)
        ):
            await client.chat([{"role": "user", "content": "Test"}])


class TestOllamaChatClientRetry:
    """Tests for OllamaChatClient.chat_with_retry() method."""

    @pytest.mark.anyio
    async def test_retry_succeeds_on_first_try(self, httpx_mock) -> None:
        """Retry should return immediately if first attempt succeeds."""
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:11434/api/chat",
            json={"message": {"role": "assistant", "content": "Success"}},
        )

        client = OllamaChatClient()
        response = await client.chat_with_retry(
            [{"role": "user", "content": "Test"}],
            retries=2,
        )

        assert response == "Success"
        assert len(httpx_mock.get_requests()) == 1


@pytest.fixture
def httpx_mock():
    """Mock for httpx requests."""
    import json as json_module
    from unittest.mock import MagicMock, patch

    class MockResponse:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError(
                    "Error",
                    request=MagicMock(),
                    response=self,
                )

        def json(self):
            return self._json_data

    class HTTPXMock:
        def __init__(self):
            self._responses = []
            self._requests = []

        def add_response(
            self,
            method="GET",
            url=None,
            status_code=200,
            json=None,
        ):
            self._responses.append(
                {
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "json": json,
                }
            )

        def get_request(self):
            return self._requests[0] if self._requests else None

        def get_requests(self):
            return self._requests

        async def mock_post(self, url, **kwargs):
            class Request:
                def __init__(self, url, content):
                    self.url = url
                    self.content = (
                        json_module.dumps(content).encode()
                        if isinstance(content, dict)
                        else content
                    )

            request = Request(url, kwargs.get("json", {}))
            self._requests.append(request)

            for resp in self._responses:
                if resp["url"] == str(url) and resp["method"] == "POST":
                    return MockResponse(resp["status_code"], resp["json"])

            return MockResponse(404, {})

    mock = HTTPXMock()

    # Create a mock context manager
    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            return await mock.mock_post(url, **kwargs)

    with patch("prism.llm.client.httpx.AsyncClient", MockAsyncClient):
        yield mock
