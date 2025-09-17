#!/usr/bin/env python3
"""
Security Utilities for UnrealBlueprintMCP Server

This module provides input validation, sanitization, and security utilities
to prevent various security vulnerabilities such as path traversal, injection attacks,
and invalid input handling.
"""

import re
import html
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class SecurityValidator:
    """Security validation utilities for input sanitization and validation"""

    # Valid blueprint name pattern: starts with letter, alphanumeric + underscore only
    BLUEPRINT_NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

    # Valid property name pattern: similar to blueprint name
    PROPERTY_NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

    # Maximum length constraints
    MAX_BLUEPRINT_NAME_LENGTH = 64
    MAX_PROPERTY_NAME_LENGTH = 64
    MAX_PROPERTY_VALUE_LENGTH = 1024
    MAX_ASSET_PATH_LENGTH = 256

    # Valid asset path pattern: must start with /Game/ and contain only valid chars
    ASSET_PATH_PATTERN = re.compile(r'^/Game/[A-Za-z0-9_/]+/$')

    # Valid parent classes (whitelist approach for security)
    VALID_PARENT_CLASSES = {
        "Actor", "Pawn", "Character", "ActorComponent", "SceneComponent",
        "UserWidget", "Object", "StaticMeshActor", "GameModeBase",
        "PlayerController", "GameState", "PlayerState"
    }

    @staticmethod
    def validate_blueprint_name(name: str) -> Dict[str, Any]:
        """
        Validate blueprint name for security and format compliance.

        Args:
            name: Blueprint name to validate

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []

        if not name:
            errors.append("Blueprint name cannot be empty")
            return {"valid": False, "errors": errors}

        if not isinstance(name, str):
            errors.append("Blueprint name must be a string")
            return {"valid": False, "errors": errors}

        # Length check
        if len(name) > SecurityValidator.MAX_BLUEPRINT_NAME_LENGTH:
            errors.append(f"Blueprint name too long (max {SecurityValidator.MAX_BLUEPRINT_NAME_LENGTH} characters)")

        # Pattern check
        if not SecurityValidator.BLUEPRINT_NAME_PATTERN.match(name):
            errors.append("Blueprint name must start with a letter and contain only letters, numbers, and underscores")

        # Reserved keywords check
        reserved_keywords = {"class", "struct", "enum", "namespace", "using", "template"}
        if name.lower() in reserved_keywords:
            errors.append(f"Blueprint name '{name}' is a reserved keyword")

        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def validate_property_name(name: str) -> Dict[str, Any]:
        """
        Validate property name for security and format compliance.

        Args:
            name: Property name to validate

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []

        if not name:
            errors.append("Property name cannot be empty")
            return {"valid": False, "errors": errors}

        if not isinstance(name, str):
            errors.append("Property name must be a string")
            return {"valid": False, "errors": errors}

        # Length check
        if len(name) > SecurityValidator.MAX_PROPERTY_NAME_LENGTH:
            errors.append(f"Property name too long (max {SecurityValidator.MAX_PROPERTY_NAME_LENGTH} characters)")

        # Pattern check
        if not SecurityValidator.PROPERTY_NAME_PATTERN.match(name):
            errors.append("Property name must start with a letter and contain only letters, numbers, and underscores")

        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def validate_property_value(value: Any, max_length: int = None) -> Dict[str, Any]:
        """
        Validate and sanitize property value.

        Args:
            value: Property value to validate
            max_length: Maximum string length (defaults to MAX_PROPERTY_VALUE_LENGTH)

        Returns:
            Dict with 'valid' boolean, 'errors' list, and 'sanitized_value'
        """
        errors = []
        max_length = max_length or SecurityValidator.MAX_PROPERTY_VALUE_LENGTH

        if value is None:
            return {"valid": True, "errors": [], "sanitized_value": ""}

        # Convert to string for validation
        str_value = str(value)

        # Length check
        if len(str_value) > max_length:
            errors.append(f"Property value too long (max {max_length} characters)")
            return {"valid": False, "errors": errors, "sanitized_value": None}

        # HTML escape for XSS prevention
        sanitized_value = html.escape(str_value, quote=True)

        # Check for potential injection patterns
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'expression\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, str_value, re.IGNORECASE):
                errors.append(f"Property value contains potentially dangerous content: {pattern}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized_value": sanitized_value
        }

    @staticmethod
    def validate_asset_path(path: str) -> Dict[str, Any]:
        """
        Validate asset path for security (path traversal prevention).

        Args:
            path: Asset path to validate

        Returns:
            Dict with 'valid' boolean, 'errors' list, and 'normalized_path'
        """
        errors = []

        if not path:
            errors.append("Asset path cannot be empty")
            return {"valid": False, "errors": errors, "normalized_path": None}

        if not isinstance(path, str):
            errors.append("Asset path must be a string")
            return {"valid": False, "errors": errors, "normalized_path": None}

        # Length check
        if len(path) > SecurityValidator.MAX_ASSET_PATH_LENGTH:
            errors.append(f"Asset path too long (max {SecurityValidator.MAX_ASSET_PATH_LENGTH} characters)")

        # Must start with /Game/
        if not path.startswith('/Game/'):
            errors.append("Asset path must start with '/Game/'")

        # Normalize path to prevent traversal attacks
        try:
            normalized = os.path.normpath(path)
        except (ValueError, TypeError):
            errors.append("Invalid asset path format")
            return {"valid": False, "errors": errors, "normalized_path": None}

        # Check for path traversal attempts
        if '..' in path:
            errors.append("Path traversal detected in asset path")

        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in path:
                errors.append(f"Asset path contains dangerous character: {char}")

        # Ensure it ends with / for directory paths (if original path didn't end with /)
        if not path.endswith('/'):
            normalized = normalized + '/'
        else:
            normalized = path

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "normalized_path": normalized
        }

    @staticmethod
    def validate_parent_class(parent_class: str) -> Dict[str, Any]:
        """
        Validate parent class against whitelist.

        Args:
            parent_class: Parent class name to validate

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []

        if not parent_class:
            errors.append("Parent class cannot be empty")
            return {"valid": False, "errors": errors}

        if not isinstance(parent_class, str):
            errors.append("Parent class must be a string")
            return {"valid": False, "errors": errors}

        if parent_class not in SecurityValidator.VALID_PARENT_CLASSES:
            errors.append(f"Invalid parent class '{parent_class}'. Must be one of: {', '.join(sorted(SecurityValidator.VALID_PARENT_CLASSES))}")

        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def sanitize_json_rpc_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize JSON-RPC parameters for safe transmission.

        Args:
            params: Parameters dictionary to sanitize

        Returns:
            Sanitized parameters dictionary
        """
        if not isinstance(params, dict):
            return {}

        sanitized = {}
        for key, value in params.items():
            # Sanitize key - allow alphanumeric and underscore
            if isinstance(key, str) and re.match(r'^[A-Za-z0-9_]+$', key):
                # Sanitize value
                if isinstance(value, str):
                    sanitized[key] = html.escape(value, quote=True)
                elif isinstance(value, (int, float, bool)):
                    sanitized[key] = value
                elif value is None:
                    sanitized[key] = None
                else:
                    # Convert other types to string and sanitize
                    sanitized[key] = html.escape(str(value), quote=True)

        return sanitized

    @staticmethod
    def validate_websocket_message_size(message: str, max_size: int = 1024 * 1024) -> bool:
        """
        Validate WebSocket message size to prevent DoS attacks.

        Args:
            message: Message to validate
            max_size: Maximum allowed message size in bytes (default 1MB)

        Returns:
            True if message size is acceptable, False otherwise
        """
        if not isinstance(message, str):
            return False

        return len(message.encode('utf-8')) <= max_size

    @staticmethod
    def validate_url(url: str) -> Dict[str, Any]:
        """
        Validate URL format and security.

        Args:
            url: URL to validate

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []

        if not url:
            errors.append("URL cannot be empty")
            return {"valid": False, "errors": errors}

        try:
            parsed = urlparse(url)
        except Exception:
            errors.append("Invalid URL format")
            return {"valid": False, "errors": errors}

        # Only allow websocket protocols
        if parsed.scheme not in ['ws', 'wss']:
            errors.append("URL must use 'ws://' or 'wss://' protocol")

        # Validate hostname (basic check)
        if not parsed.hostname:
            errors.append("URL must have a valid hostname")

        return {"valid": len(errors) == 0, "errors": errors}


class SecurityError(Exception):
    """Custom exception for security validation failures"""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


def validate_blueprint_creation_params(blueprint_name: str, parent_class: str, asset_path: str) -> None:
    """
    Comprehensive validation for blueprint creation parameters.

    Args:
        blueprint_name: Name of the blueprint
        parent_class: Parent class for the blueprint
        asset_path: Asset path where blueprint will be created

    Raises:
        SecurityError: If any validation fails
    """
    all_errors = []

    # Validate blueprint name
    name_result = SecurityValidator.validate_blueprint_name(blueprint_name)
    if not name_result["valid"]:
        all_errors.extend(name_result["errors"])

    # Validate parent class
    parent_result = SecurityValidator.validate_parent_class(parent_class)
    if not parent_result["valid"]:
        all_errors.extend(parent_result["errors"])

    # Validate asset path
    path_result = SecurityValidator.validate_asset_path(asset_path)
    if not path_result["valid"]:
        all_errors.extend(path_result["errors"])

    if all_errors:
        raise SecurityError("Blueprint creation parameters validation failed", all_errors)


def validate_property_setting_params(blueprint_path: str, property_name: str, property_value: Any) -> Dict[str, Any]:
    """
    Comprehensive validation for property setting parameters.

    Args:
        blueprint_path: Path to the blueprint
        property_name: Name of the property
        property_value: Value to set

    Returns:
        Dict with validation results and sanitized values

    Raises:
        SecurityError: If any validation fails
    """
    all_errors = []
    sanitized_values = {}

    # Validate blueprint path
    path_result = SecurityValidator.validate_asset_path(blueprint_path)
    if not path_result["valid"]:
        all_errors.extend(path_result["errors"])
    else:
        sanitized_values["blueprint_path"] = path_result["normalized_path"]

    # Validate property name
    name_result = SecurityValidator.validate_property_name(property_name)
    if not name_result["valid"]:
        all_errors.extend(name_result["errors"])
    else:
        sanitized_values["property_name"] = property_name

    # Validate and sanitize property value
    value_result = SecurityValidator.validate_property_value(property_value)
    if not value_result["valid"]:
        all_errors.extend(value_result["errors"])
    else:
        sanitized_values["property_value"] = value_result["sanitized_value"]

    if all_errors:
        raise SecurityError("Property setting parameters validation failed", all_errors)

    return sanitized_values