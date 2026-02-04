__version__ = "0.2.0"

from .client import RoutewayClient, create_client
from .errors import (
    RoutewayError,
    RoutewayAuthError,
    RoutewayRateLimitError,
    RoutewayServerError,
    RoutewayHTTPError,
    RoutewayTimeoutError,
    RoutewayConnectionError,
    RoutewayValidationError,
    RoutewayStreamError,
)
from .types import (
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChunk,
    StreamOptions,
    Function,
    Tool,
    FunctionCall,
    ToolCall,
    ReasoningConfig,
    create_message,
    create_user_message,
    create_assistant_message,
    create_system_message,
    create_tool_message,
    create_function,
    create_tool,
)

try:
    from .async_client import AsyncRoutewayClient
    __all_async__ = ["AsyncRoutewayClient"]
except ImportError:
    __all_async__ = []

__all__ = [
    "__version__",
    "RoutewayClient",
    "create_client",
    "RoutewayError",
    "RoutewayAuthError",
    "RoutewayRateLimitError",
    "RoutewayServerError",
    "RoutewayHTTPError",
    "RoutewayTimeoutError",
    "RoutewayConnectionError",
    "RoutewayValidationError",
    "RoutewayStreamError",
    "ChatMessage",
    "ChatCompletionResponse",
    "ChatCompletionChunk",
    "StreamOptions",
    "Function",
    "Tool",
    "FunctionCall",
    "ToolCall",
    "ReasoningConfig",
    "create_message",
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    "create_tool_message",
    "create_function",
    "create_tool",
] + __all_async__