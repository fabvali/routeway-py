from typing import Any, Dict, List, Optional, Union, Literal
from dataclasses import dataclass, field, asdict
from typing_extensions import TypedDict


@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "role": self.role,
            "content": self.content,
        }
        if self.name is not None:
            result["name"] = self.name
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class FunctionCall:
    name: str
    arguments: str


@dataclass
class ToolCall:
    id: str
    type: str
    function: FunctionCall


@dataclass
class Function:
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.description is not None:
            result["description"] = self.description
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result


@dataclass
class Tool:
    type: Literal["function"]
    function: Function

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "function": self.function.to_dict(),
        }


class Usage(TypedDict, total=False):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    reasoning_tokens: Optional[int]


class Choice(TypedDict):
    index: int
    message: Dict[str, Any]
    finish_reason: Optional[str]
    logprobs: Optional[Dict[str, Any]]


class ChatCompletionResponse(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage]
    system_fingerprint: Optional[str]


@dataclass
class StreamOptions:
    include_usage: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"include_usage": self.include_usage}


class Delta(TypedDict, total=False):
    role: Optional[str]
    content: Optional[str]
    tool_calls: Optional[List[Dict[str, Any]]]
    reasoning_content: Optional[str]


class StreamChoice(TypedDict):
    index: int
    delta: Delta
    finish_reason: Optional[str]
    logprobs: Optional[Dict[str, Any]]


class ChatCompletionChunk(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]
    usage: Optional[Usage]


class ErrorDetail(TypedDict):
    message: str
    type: str
    param: Optional[str]
    code: Optional[str]


class ErrorResponse(TypedDict):
    error: ErrorDetail


class ModelPermission(TypedDict, total=False):
    id: str
    object: str
    created: int
    allow_create_engine: bool
    allow_sampling: bool
    allow_logprobs: bool
    allow_search_indices: bool
    allow_view: bool
    allow_fine_tuning: bool
    organization: str
    group: Optional[str]
    is_blocking: bool


class Model(TypedDict):
    id: str
    object: str
    created: int
    owned_by: str
    permission: List[ModelPermission]
    root: str
    parent: Optional[str]


class ModelList(TypedDict):
    object: str
    data: List[Model]


@dataclass
class ReasoningConfig:
    type: Literal["enabled", "disabled"] = "enabled"
    max_tokens: Optional[int] = None
    budget: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        if self.max_tokens is not None:
            result["max_tokens"] = self.max_tokens
        if self.budget is not None:
            result["budget"] = self.budget
        return result


def create_message(
    role: str,
    content: str,
    name: Optional[str] = None,
) -> ChatMessage:
    return ChatMessage(role=role, content=content, name=name)


def create_user_message(content: str, name: Optional[str] = None) -> ChatMessage:
    return ChatMessage(role="user", content=content, name=name)


def create_assistant_message(
    content: str,
    name: Optional[str] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
) -> ChatMessage:
    return ChatMessage(role="assistant", content=content, name=name, tool_calls=tool_calls)


def create_system_message(content: str) -> ChatMessage:
    return ChatMessage(role="system", content=content)


def create_tool_message(
    content: str,
    tool_call_id: str,
    name: Optional[str] = None,
) -> ChatMessage:
    return ChatMessage(
        role="tool",
        content=content,
        tool_call_id=tool_call_id,
        name=name,
    )


def create_function(
    name: str,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Function:
    return Function(name=name, description=description, parameters=parameters)


def create_tool(function: Function) -> Tool:
    return Tool(type="function", function=function)
