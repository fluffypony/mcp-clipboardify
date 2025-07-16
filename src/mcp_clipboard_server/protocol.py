"""JSON-RPC 2.0 protocol handling for MCP communication."""

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union


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
            params=data.get("params")
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
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error is not None:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
        return response


# Standard JSON-RPC error codes
class ErrorCodes:
    """Standard JSON-RPC 2.0 error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000  # MCP server error


def parse_json_rpc_message(data: str) -> JsonRpcRequest:
    """
    Parse a JSON-RPC 2.0 message from string.
    
    Args:
        data: JSON string containing the message.
        
    Returns:
        JsonRpcRequest: Parsed request object.
        
    Raises:
        ValueError: If JSON is malformed or missing required fields.
    """
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Parse error: {str(e)}")
    
    if not isinstance(parsed, dict):
        raise ValueError("Invalid request: must be JSON object")
    
    # Validate required fields
    if parsed.get("jsonrpc") != "2.0":
        raise ValueError("Invalid request: jsonrpc must be '2.0'")
    
    if "method" not in parsed:
        raise ValueError("Invalid request: missing method")
    
    return JsonRpcRequest.from_dict(parsed)


def create_success_response(request_id: Optional[Union[str, int]], result: Any) -> str:
    """
    Create a successful JSON-RPC response.
    
    Args:
        request_id: The ID from the original request.
        result: The result data to return.
        
    Returns:
        str: JSON-encoded response.
    """
    response = JsonRpcResponse(
        jsonrpc="2.0",
        id=request_id,
        result=result
    )
    return json.dumps(response.to_dict())


def create_error_response(request_id: Optional[Union[str, int]], 
                         code: int, message: str, data: Any = None) -> str:
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
    response = JsonRpcResponse(
        jsonrpc="2.0",
        id=request_id,
        error=error
    )
    return json.dumps(response.to_dict())
