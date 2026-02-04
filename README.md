# routeway-py

A Python SDK for the [Routeway API](https://routeway.ai). It's OpenAI-compatible, so if you've used the OpenAI Python client, this will feel familiar.

## What it does

- **Streaming**: Get responses chunk by chunk instead of waiting for the full response
- **Async**: Built on `httpx` for non-blocking requests
- **Tool calling**: Function calling support for structured outputs
- **Reasoning modes**: Extended thinking for complex tasks
- **Type hints**: Fully typed with `TypedDict` and dataclasses

## Install

```bash
pip install routeway-py
```

For async support:

```bash
pip install routeway-py[async]
```

## Usage

### Basic

```python
from routeway import RoutewayClient

client = RoutewayClient(api_key="your-api-key")

response = client.chat_completion(
    model="model_id",
    messages=[{"role": "user", "content": "Hello, how are you?"}],
)

print(response["choices"][0]["message"]["content"])
client.close()
```

Or use it as a context manager so cleanup happens automatically:

```python
from routeway import RoutewayClient

with RoutewayClient(api_key="your-api-key") as client:
    response = client.chat_completion(
        model="model_id",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response["choices"][0]["message"]["content"])
```

### Streaming

```python
from routeway import RoutewayClient, StreamOptions

client = RoutewayClient(api_key="your-api-key")

stream = client.chat_completion(
    model="model_id",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
    stream_options=StreamOptions(include_usage=True),
)

for chunk in stream:
    if chunk["choices"]:
        delta = chunk["choices"][0].get("delta", {})
        if content := delta.get("content"):
            print(content, end="", flush=True)

client.close()
```

### Async

```python
import asyncio
from routeway import AsyncRoutewayClient

async def main():
    async with AsyncRoutewayClient(api_key="your-api-key") as client:
        response = await client.chat_completion(
            model="model_id",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response["choices"][0]["message"]["content"])

asyncio.run(main())
```

### Function calling

```python
from routeway import RoutewayClient, create_function, create_tool

weather_function = create_function(
    name="get_weather",
    description="Get the current weather in a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city, e.g. San Francisco",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
            },
        },
        "required": ["location"],
    },
)

tool = create_tool(weather_function)

with RoutewayClient(api_key="your-api-key") as client:
    response = client.chat_completion(
        model="gpt-4",
        messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        tools=[tool.to_dict()],
        tool_choice="auto",
    )

    message = response["choices"][0]["message"]
    if tool_calls := message.get("tool_calls"):
        for call in tool_calls:
            print(f"Function: {call['function']['name']}")
            print(f"Arguments: {call['function']['arguments']}")
```

## Configuration

Set your API key via environment variable:

```bash
export ROUTEWAY_API_KEY="your-api-key"
```

Then initialize without passing the key:

```python
from routeway import RoutewayClient

client = RoutewayClient()
```

Or configure manually:

```python
client = RoutewayClient(
    api_key="your-api-key",
    base_url="https://api.routeway.ai/v1",
    timeout=30.0,
    max_retries=3,
)
```

## Error handling

```python
from routeway import (
    RoutewayError,
    RoutewayAuthError,
    RoutewayRateLimitError,
    RoutewayServerError,
)

try:
    response = client.chat_completion(...)
except RoutewayAuthError:
    print("Check your API key")
except RoutewayRateLimitError:
    print("Hit the rate limit")
except RoutewayServerError:
    print("Server error, try again")
except RoutewayError as e:
    print(f"Something went wrong: {e}")
```

## Requirements

- Python 3.9+
- `requests` >= 2.31.0
- `httpx` >= 0.24.0 (optional, for async)

## License

MIT © [fabvali](https://github.com/fabvali)

## Links

- [Routeway API](https://routeway.ai)
- [GitHub](https://github.com/fabvali/routeway.js)

<h3 align="center">☕ Support My Work</h3>
<div align="center">
  <a href="https://ko-fi.com/nevika">
    <img src="https://img.shields.io/badge/Ko--fi-Support%20Me%20%E2%98%95%EF%B8%8F-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Support me on Ko-fi" height="40">
  </a>
</div>
