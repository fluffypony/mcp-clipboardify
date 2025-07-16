"""JSON-RPC 2.0 protocol handling for MCP communication with batch request support."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class JsonRpcRequest:
    """JSON-RPC 2.0 request message."""

    jsonrpc: str
    method: str
    id: Optional[Union[str, int]]
    params: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JsonRpcRequest":
        """Create request from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", ""),
            method=data.get("method", ""),
            id=data.get("id"),
            params=data.get("params"),
        )


@dataclass
class JsonRpcError:
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class JsonRpcResponse:
    """JSON-RPC 2.0 response message."""

    jsonrpc: str
    id: Optional[Union[str, int]]
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
        return response


def _validate_json_rpc_object(obj: dict) -> None:
    """Validate a single JSON-RPC object."""
    if obj.get("jsonrpc") != "2.0":
        raise ValueError("Invalid request: jsonrpc must be '2.0'")

    if "method" not in obj:
        raise ValueError("Invalid request: missing method")


def _parse_batch_request(parsed: list) -> List[JsonRpcRequest]:
    """Parse a batch JSON-RPC request."""
    if not parsed:  # Empty batch not allowed
        raise ValueError("Invalid request: empty batch")

    requests = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("Invalid request: batch items must be JSON objects")

        _validate_json_rpc_object(item)
        requests.append(JsonRpcRequest.from_dict(item))

    return requests


def _parse_single_request(parsed: dict) -> JsonRpcRequest:
    """Parse a single JSON-RPC request."""
    _validate_json_rpc_object(parsed)
    return JsonRpcRequest.from_dict(parsed)


def parse_json_rpc_message(data: str) -> Union[JsonRpcRequest, List[JsonRpcRequest]]:
    """
    Parse a JSON-RPC 2.0 message from string.

    Args:
        data: JSON string containing the message.

    Returns:
        JsonRpcRequest for single requests, List[JsonRpcRequest] for batch requests.

    Raises:
        ValueError: If JSON is malformed or missing required fields.
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Parse error: {str(e)}") from e

    # Check if it's a batch request (array)
    if isinstance(parsed, list):
        return _parse_batch_request(parsed)

    # Single request
    if not isinstance(parsed, dict):
        raise ValueError("Invalid request: must be JSON object")

    return _parse_single_request(parsed)


def create_success_response(request_id: Optional[Union[str, int]], result: Any) -> str:
    """
    Create a successful JSON-RPC response.

    Args:
        request_id: The ID from the original request.
        result: The result data to return.

    Returns:
        str: JSON-encoded response.
    """
    response = JsonRpcResponse(jsonrpc="2.0", id=request_id, result=result)
    return json.dumps(response.to_dict())


def create_error_response(
    request_id: Optional[Union[str, int]], code: int, message: str, data: Any = None
) -> str:
    """
    Create an error JSON-RPC response.

    Args:
        request_id: The ID from the original request.
        code: Error code.
        message: Error message.
        data: Optional additional error data.

    Returns:
        str: JSON-encoded error response.
    """
    error = JsonRpcError(code=code, message=message, data=data)
    response = JsonRpcResponse(jsonrpc="2.0", id=request_id, error=error)
    return json.dumps(response.to_dict())


def create_batch_response(responses: List[Optional[str]]) -> str:
    """
    Create a batch JSON-RPC response from individual responses.

    Args:
        responses: List of individual response strings (None for notifications).

    Returns:
        str: JSON-encoded batch response array.
    """
    # Filter out None responses (notifications)
    valid_responses = [resp for resp in responses if resp is not None]

    # If no valid responses, return empty (per JSON-RPC spec)
    if not valid_responses:
        return ""

    # Parse each response and collect into array
    response_objects = []
    for resp in valid_responses:
        response_objects.append(json.loads(resp))

    return json.dumps(response_objects)
