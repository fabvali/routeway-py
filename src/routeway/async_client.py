import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, AsyncIterator

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from .errors import (
    RoutewayError,
    RoutewayAuthError,
    RoutewayRateLimitError,
    RoutewayServerError,
    RoutewayHTTPError,
)
from .types import (
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChunk,
    StreamOptions,
)

logger = logging.getLogger(__name__)


class AsyncRoutewayClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.routeway.ai/v1",
        timeout: Optional[float] = None,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for async support. "
                "Install it with: pip install routeway-py[async]"
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.api_key = api_key or os.getenv("ROUTEWAY_API_KEY")
        if not self.api_key:
            raise RoutewayAuthError(
                "API key is required. Please provide it via the api_key argument "
                "or set the ROUTEWAY_API_KEY environment variable."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if default_headers:
            headers.update(default_headers)

        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

        logger.debug("AsyncRoutewayClient initialized with base_url=%s", self.base_url)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        try:
            response = await self.client.request(
                method=method,
                url=endpoint.lstrip("/"),
                json=data,
            )
            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)
        except httpx.TimeoutException:
            raise RoutewayError("Request timed out")
        except httpx.ConnectError:
            raise RoutewayError("Connection failed")
        except httpx.RequestError as e:
            raise RoutewayError(f"Request failed: {str(e)}") from e

    async def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        try:
            error_data = error.response.json()
            error_message = error_data.get("error", {}).get("message", str(error))
        except (json.JSONDecodeError, AttributeError):
            error_message = str(error)

        status_code = error.response.status_code

        if status_code == 401:
            raise RoutewayAuthError(error_message)
        elif status_code == 429:
            raise RoutewayRateLimitError(error_message)
        elif 500 <= status_code < 600:
            raise RoutewayServerError(error_message)
        else:
            raise RoutewayHTTPError(error_message)

    def _validate_chat_params(
        self,
        model: str,
        messages: List[Union[Dict[str, str], ChatMessage]],
    ) -> List[Dict[str, Any]]:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model must be a non-empty string")

        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages must be a non-empty list")

        validated_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, dict):
                if "role" not in msg or "content" not in msg:
                    raise ValueError("Each message must have 'role' and 'content' keys")
                validated_messages.append(dict(msg))
            elif isinstance(msg, ChatMessage):
                validated_messages.append(msg.to_dict())
            else:
                raise ValueError("Each message must be a dict or ChatMessage instance")

        return validated_messages

    async def chat_completion(
        self,
        model: str,
        messages: List[Union[Dict[str, str], ChatMessage]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
        stream_options: Optional[StreamOptions] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletionResponse, AsyncIterator[ChatCompletionChunk]]:
        validated_messages = self._validate_chat_params(model, messages)

        data: Dict[str, Any] = {
            "model": model,
            "messages": validated_messages,
        }

        if stream:
            data["stream"] = True
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if top_p is not None:
            data["top_p"] = top_p
        if frequency_penalty is not None:
            data["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            data["presence_penalty"] = presence_penalty
        if stop is not None:
            data["stop"] = stop
        if tools is not None:
            data["tools"] = tools
        if tool_choice is not None:
            data["tool_choice"] = tool_choice
        if reasoning is not None:
            data["reasoning"] = reasoning
        if stream_options is not None:
            if isinstance(stream_options, dict):
                data["stream_options"] = stream_options
            else:
                data["stream_options"] = stream_options.to_dict()

        data.update(kwargs)

        logger.debug("Making async chat completion request")

        if stream:
            return self._stream_chat_completion(data)
        else:
            response = await self._make_request(
                method="POST",
                endpoint="chat/completions",
                data=data,
            )
            return response.json()

    async def _stream_chat_completion(
        self, data: Dict[str, Any]
    ) -> AsyncIterator[ChatCompletionChunk]:
        async with self.client.stream(
            "POST",
            "chat/completions",
            json=data,
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]
                    
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        yield chunk
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode JSON chunk: {e}")
                        continue

    async def models_list(self) -> Dict[str, Any]:
        response = await self._make_request(method="GET", endpoint="models")
        return response.json()

    async def model_retrieve(self, model: str) -> Dict[str, Any]:
        response = await self._make_request(method="GET", endpoint=f"models/{model}")
        return response.json()

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncRoutewayClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()