import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, Iterator
import requests
from requests.adapters import HTTPAdapter, Retry

from .errors import (
    RoutewayError,
    RoutewayAuthError,
    RoutewayRateLimitError,
    RoutewayServerError,
    RoutewayHTTPError,
)
from .types import ChatMessage, ChatCompletionResponse, ChatCompletionChunk, StreamOptions

logger = logging.getLogger(__name__)


class RoutewayClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.routeway.ai/v1",
        timeout: Optional[float] = None,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.api_key = api_key or os.getenv("ROUTEWAY_API_KEY")
        if not self.api_key:
            raise RoutewayAuthError("API key required. Set ROUTEWAY_API_KEY or pass api_key.")

        self.session = requests.Session()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if default_headers:
            headers.update(default_headers)
        self.session.headers.update(headers)

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        logger.debug(f"RoutewayClient init: {self.base_url}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout,
                stream=stream,
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.Timeout:
            raise RoutewayError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise RoutewayError("Connection failed")
        except requests.exceptions.RequestException as e:
            raise RoutewayError(f"Request failed: {e}") from e

    def _handle_http_error(self, error: requests.exceptions.HTTPError):
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

    def _validate_chat_params(self, model: str, messages):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model must be non-empty string")

        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages must be non-empty list")

        validated_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                if "role" not in msg or "content" not in msg:
                    raise ValueError("Message needs 'role' and 'content' keys")
                validated_messages.append(dict(msg))
            elif isinstance(msg, ChatMessage):
                validated_messages.append(msg.to_dict())
            else:
                raise ValueError("Message must be dict or ChatMessage")

        return validated_messages

    def chat_completion(
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
    ) -> Union[ChatCompletionResponse, Iterator[ChatCompletionChunk]]:
        validated_messages = self._validate_chat_params(model, messages)

        data = {
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

        logger.debug(f"chat_completion: {len(validated_messages)} messages")

        if stream:
            return self._stream_chat_completion(data)
        
        response = self._make_request(
            method="POST",
            endpoint="chat/completions",
            data=data,
        )
        return response.json()

    def _stream_chat_completion(self, data: Dict[str, Any]):
        response = self._make_request(
            method="POST",
            endpoint="chat/completions",
            data=data,
            stream=True,
        )

        try:
            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")
                
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        yield chunk
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to decode chunk: {e}")
                        continue
        finally:
            response.close()

    def models_list(self) -> Dict[str, Any]:
        response = self._make_request(method="GET", endpoint="models")
        return response.json()

    def model_retrieve(self, model: str) -> Dict[str, Any]:
        response = self._make_request(method="GET", endpoint=f"models/{model}")
        return response.json()

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_client(api_key: Optional[str] = None, **kwargs: Any) -> RoutewayClient:
    return RoutewayClient(api_key=api_key, **kwargs)
