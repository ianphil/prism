"""Ollama chat client implementation."""

import httpx


class OllamaChatClient:
    """HTTP client for Ollama's chat API.

    Provides async chat completion using Ollama's REST API.

    Attributes:
        endpoint: Base URL for Ollama API (e.g., "http://localhost:11434").
        model: Model name to use (e.g., "mistral", "llama3").
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "mistral",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Ollama chat client.

        Args:
            endpoint: Base URL for Ollama API.
            model: Model name to use for completions.
            timeout: Request timeout in seconds.
        """
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> str:
        """Send messages to Ollama and get a response.

        Args:
            messages: List of message dicts with "role" and "content" keys.
                Roles can be "system", "user", or "assistant".
            **kwargs: Additional parameters passed to Ollama API.

        Returns:
            The model's response text.

        Raises:
            httpx.TimeoutException: If request times out.
            httpx.HTTPStatusError: If Ollama returns an error status.
            httpx.ConnectError: If cannot connect to Ollama.
        """
        url = f"{self.endpoint}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        data = response.json()
        return data["message"]["content"]

    async def chat_with_retry(
        self,
        messages: list[dict[str, str]],
        retries: int = 1,
        **kwargs,
    ) -> str:
        """Send messages with automatic retry on timeout.

        Args:
            messages: List of message dicts.
            retries: Number of retries on timeout (default 1).
            **kwargs: Additional parameters passed to Ollama API.

        Returns:
            The model's response text.

        Raises:
            httpx.TimeoutException: If all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                return await self.chat(messages, **kwargs)
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < retries:
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise last_error  # type: ignore
