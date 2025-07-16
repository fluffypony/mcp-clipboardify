"""Input validation utilities for MCP clipboard server."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


@dataclass
class ValidationError:
    """Represents a validation error with context."""

    field: str
    message: str
    limit: Optional[int] = None


class ValidationException(Exception):
    """Exception raised when validation fails."""

    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        messages = [f"{error.field}: {error.message}" for error in errors]
        super().__init__("; ".join(messages))


def validate_text_size(text: str, max_bytes: int = 1048576) -> None:
    """
    Validate text size against byte limit.

    Args:
        text: Text to validate
        max_bytes: Maximum allowed bytes (default: 1MB)

    Raises:
        ValidationException: If text exceeds limit
    """
    if not isinstance(text, str):
        raise ValidationException([ValidationError("text", "Must be a string")])

    byte_size = len(text.encode("utf-8"))
    if byte_size > max_bytes:
        raise ValidationException(
            [ValidationError("text", "Text exceeds 1MB limit", limit=max_bytes)]
        )


def validate_json_structure(
    data: Any, required_fields: Optional[List[str]] = None
) -> None:
    """
    Validate basic JSON structure requirements.

    Args:
        data: Parsed JSON data to validate
        required_fields: List of required field names

    Raises:
        ValidationException: If structure is invalid
    """
    errors = []

    if not isinstance(data, dict):
        errors.append(ValidationError("root", "Must be a JSON object"))
        raise ValidationException(errors)

    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(ValidationError(field, "Required field missing"))

    if errors:
        raise ValidationException(errors)


def validate_json_rpc_structure(data: Dict[str, Any]) -> None:
    """
    Validate JSON-RPC 2.0 message structure.

    Args:
        data: Parsed JSON-RPC message

    Raises:
        ValidationException: If message structure is invalid
    """
    errors = []

    # Check jsonrpc version
    if "jsonrpc" not in data:
        errors.append(ValidationError("jsonrpc", "Required field missing"))
    elif data["jsonrpc"] != "2.0":
        errors.append(ValidationError("jsonrpc", "Must be '2.0'"))

    # Check method for requests
    if "method" in data:
        if not isinstance(data["method"], str):
            errors.append(ValidationError("method", "Must be a string"))
        elif not data["method"]:
            errors.append(ValidationError("method", "Cannot be empty"))

    # Check id format if present
    if "id" in data:
        id_value = data["id"]
        if not isinstance(id_value, (str, int, type(None))):
            errors.append(ValidationError("id", "Must be string, number, or null"))

    if errors:
        raise ValidationException(errors)


def validate_with_json_schema(data: Any, schema: Dict[str, Any]) -> None:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate
        schema: JSON schema to validate against

    Raises:
        ValidationException: If validation fails
    """
    if not HAS_JSONSCHEMA:
        # Fallback to basic validation for required fields
        if schema.get("type") == "object":
            required = schema.get("required", [])
            validate_json_structure(data, required)
        return

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        # Convert jsonschema error to our format
        field_path = ".".join(str(p) for p in e.path) if e.path else "root"
        error = ValidationError(field_path, e.message)
        raise ValidationException([error]) from e
    except jsonschema.SchemaError as e:
        # Schema itself is invalid
        raise ValidationException(
            [ValidationError("schema", f"Invalid schema: {e.message}")]
        ) from e


def validate_clipboard_text(text: str) -> None:
    """
    Comprehensive validation for clipboard text content.

    Args:
        text: Text content to validate

    Raises:
        ValidationException: If validation fails
    """
    # Check type first
    if not isinstance(text, str):
        raise ValidationException([ValidationError("text", "Text must be a string")])

    # Check size limit (1MB)
    validate_text_size(text, 1048576)

    # Additional checks could be added here:
    # - Encoding validation
    # - Content sanitization
    # - Format-specific validation


def safe_json_parse(json_str: str) -> Dict[str, Any]:
    """
    Safely parse JSON string with validation.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed JSON data

    Raises:
        ValidationException: If JSON is invalid
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationException(
            [ValidationError("json", f"Invalid JSON: {e.msg}")]
        ) from e

    if not isinstance(data, dict):
        raise ValidationException(
            [ValidationError("json", "Top-level JSON must be an object")]
        )

    return data


def validate_parameter_types(params: Dict[str, Any], type_map: Dict[str, type]) -> None:
    """
    Validate parameter types against expected types.

    Args:
        params: Parameters to validate
        type_map: Mapping of parameter names to expected types

    Raises:
        ValidationException: If type validation fails
    """
    errors = []

    for param_name, expected_type in type_map.items():
        if param_name in params:
            value = params[param_name]
            if not isinstance(value, expected_type):
                errors.append(
                    ValidationError(
                        param_name,
                        f"Expected {expected_type.__name__}, got {type(value).__name__}",
                    )
                )

    if errors:
        raise ValidationException(errors)
