#!/usr/bin/env python3
"""
Security Tests for UnrealBlueprintMCP Server

This module contains comprehensive security tests for the UnrealBlueprintMCP server,
ensuring that all security measures are properly implemented and effective.
"""

import pytest
import json
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from security_utils import (
    SecurityValidator, SecurityError,
    validate_blueprint_creation_params,
    validate_property_setting_params
)
from unreal_blueprint_mcp_server import BlueprintCreateParams, BlueprintPropertyParams


class TestSecurityValidator:
    """Test cases for SecurityValidator class"""

    def test_valid_blueprint_name(self):
        """Test valid blueprint names"""
        valid_names = ["MyActor", "TestCharacter", "Player_Controller", "UI_Widget123"]

        for name in valid_names:
            result = SecurityValidator.validate_blueprint_name(name)
            assert result["valid"], f"'{name}' should be valid: {result['errors']}"

    def test_invalid_blueprint_name(self):
        """Test invalid blueprint names"""
        invalid_names = [
            "",  # Empty name
            "123Actor",  # Starts with number
            "My-Actor",  # Contains hyphen
            "My Actor",  # Contains space
            "Actor<Script>",  # Contains dangerous characters
            "class",  # Reserved keyword
            "a" * 65,  # Too long
        ]

        for name in invalid_names:
            result = SecurityValidator.validate_blueprint_name(name)
            assert not result["valid"], f"'{name}' should be invalid but was accepted"

    def test_valid_property_name(self):
        """Test valid property names"""
        valid_names = ["Health", "MaxSpeed", "Player_Name", "item_count"]

        for name in valid_names:
            result = SecurityValidator.validate_property_name(name)
            assert result["valid"], f"'{name}' should be valid: {result['errors']}"

    def test_invalid_property_name(self):
        """Test invalid property names"""
        invalid_names = [
            "",  # Empty name
            "123health",  # Starts with number
            "health-value",  # Contains hyphen
            "health value",  # Contains space
            "a" * 65,  # Too long
        ]

        for name in invalid_names:
            result = SecurityValidator.validate_property_name(name)
            assert not result["valid"], f"'{name}' should be invalid but was accepted"

    def test_valid_property_value(self):
        """Test valid property values"""
        valid_values = [
            "100",
            "Hello World",
            "true",
            "Vector(1,2,3)",
            None
        ]

        for value in valid_values:
            result = SecurityValidator.validate_property_value(value)
            assert result["valid"], f"'{value}' should be valid: {result['errors']}"

    def test_xss_prevention_in_property_value(self):
        """Test XSS prevention in property values"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "eval('malicious code')",
        ]

        for xss in xss_attempts:
            result = SecurityValidator.validate_property_value(xss)
            # Should either be invalid or sanitized
            if result["valid"]:
                # If valid, must be sanitized (HTML escaped)
                assert "&lt;" in result["sanitized_value"] or "javascript:" not in result["sanitized_value"]
            else:
                # If invalid, should have appropriate error
                assert any("dangerous" in error.lower() for error in result["errors"])

    def test_valid_asset_path(self):
        """Test valid asset paths"""
        valid_paths = [
            "/Game/Blueprints/",
            "/Game/Characters/",
            "/Game/UI/Widgets/",
            "/Game/Items/Weapons/"
        ]

        for path in valid_paths:
            result = SecurityValidator.validate_asset_path(path)
            assert result["valid"], f"'{path}' should be valid: {result['errors']}"

    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        malicious_paths = [
            "/Game/../../../etc/passwd",
            "/Game/Blueprints/../../../secret",
            "/Game/Blueprints/../../..",
            "../Game/Blueprints/",
            "/Game/./../../etc/",
        ]

        for path in malicious_paths:
            result = SecurityValidator.validate_asset_path(path)
            assert not result["valid"], f"'{path}' should be blocked as potential path traversal"

    def test_invalid_asset_path(self):
        """Test invalid asset paths"""
        invalid_paths = [
            "",  # Empty
            "/InvalidRoot/",  # Doesn't start with /Game/
            "/Game/Path<script>",  # Dangerous characters
            "/Game/Path|pipe",  # Pipe character
            "/Game/Path?query",  # Query character
            "a" * 300,  # Too long
        ]

        for path in invalid_paths:
            result = SecurityValidator.validate_asset_path(path)
            assert not result["valid"], f"'{path}' should be invalid but was accepted"

    def test_valid_parent_class(self):
        """Test valid parent classes"""
        valid_classes = ["Actor", "Pawn", "Character", "UserWidget", "ActorComponent"]

        for cls in valid_classes:
            result = SecurityValidator.validate_parent_class(cls)
            assert result["valid"], f"'{cls}' should be valid: {result['errors']}"

    def test_invalid_parent_class(self):
        """Test invalid parent classes"""
        invalid_classes = [
            "",  # Empty
            "CustomClass",  # Not in whitelist
            "Script",  # Dangerous
            "<script>",  # XSS attempt
            "System.Object",  # System class
        ]

        for cls in invalid_classes:
            result = SecurityValidator.validate_parent_class(cls)
            assert not result["valid"], f"'{cls}' should be invalid but was accepted"

    def test_json_rpc_sanitization(self):
        """Test JSON-RPC parameter sanitization"""
        dangerous_params = {
            "normal_key": "normal_value",
            "xss_attempt": "<script>alert('xss')</script>",
            "injection": "'; DROP TABLE blueprints; --",
            "html_content": "<b>Bold</b> text",
            "number_value": 123,
            "boolean_value": True,
            "null_value": None,
        }

        sanitized = SecurityValidator.sanitize_json_rpc_params(dangerous_params)

        # Normal values should remain
        assert sanitized["normal_key"] == "normal_value"
        assert sanitized["number_value"] == 123
        assert sanitized["boolean_value"] is True
        assert sanitized["null_value"] is None

        # Dangerous content should be escaped
        assert "&lt;script&gt;" in sanitized["xss_attempt"]
        assert "&lt;b&gt;" in sanitized["html_content"]

    def test_websocket_message_size_validation(self):
        """Test WebSocket message size validation"""
        # Normal size message should pass
        normal_message = "Hello, World!"
        assert SecurityValidator.validate_websocket_message_size(normal_message)

        # Oversized message should fail
        oversized_message = "x" * (1024 * 1024 + 1)  # > 1MB
        assert not SecurityValidator.validate_websocket_message_size(oversized_message)

        # Custom size limit
        medium_message = "x" * 1000
        assert SecurityValidator.validate_websocket_message_size(medium_message, max_size=500) is False
        assert SecurityValidator.validate_websocket_message_size(medium_message, max_size=2000) is True

    def test_url_validation(self):
        """Test URL validation for WebSocket connections"""
        valid_urls = [
            "ws://localhost:8080",
            "wss://secure.example.com:443",
            "ws://127.0.0.1:6277"
        ]

        for url in valid_urls:
            result = SecurityValidator.validate_url(url)
            assert result["valid"], f"'{url}' should be valid: {result['errors']}"

        invalid_urls = [
            "",  # Empty
            "http://example.com",  # Wrong protocol
            "ftp://example.com",  # Wrong protocol
            "ws://",  # No hostname
            "invalid-url",  # Invalid format
        ]

        for url in invalid_urls:
            result = SecurityValidator.validate_url(url)
            assert not result["valid"], f"'{url}' should be invalid but was accepted"


class TestPydanticValidation:
    """Test Pydantic model validation with security constraints"""

    def test_valid_blueprint_create_params(self):
        """Test valid blueprint creation parameters"""
        valid_params = BlueprintCreateParams(
            blueprint_name="TestActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

        assert valid_params.blueprint_name == "TestActor"
        assert valid_params.parent_class == "Actor"
        assert valid_params.asset_path == "/Game/Blueprints/"

    def test_invalid_blueprint_create_params(self):
        """Test invalid blueprint creation parameters"""
        with pytest.raises(ValueError, match="Invalid blueprint name"):
            BlueprintCreateParams(
                blueprint_name="123Invalid",
                parent_class="Actor",
                asset_path="/Game/Blueprints/"
            )

        with pytest.raises(ValueError, match="Invalid parent class"):
            BlueprintCreateParams(
                blueprint_name="TestActor",
                parent_class="InvalidClass",
                asset_path="/Game/Blueprints/"
            )

        with pytest.raises(ValueError, match="Invalid asset path"):
            BlueprintCreateParams(
                blueprint_name="TestActor",
                parent_class="Actor",
                asset_path="/InvalidPath/"
            )

    def test_valid_blueprint_property_params(self):
        """Test valid blueprint property parameters"""
        valid_params = BlueprintPropertyParams(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Health",
            property_value="100",
            property_type="int"
        )

        assert valid_params.blueprint_path == "/Game/Blueprints/TestActor/"
        assert valid_params.property_name == "Health"
        assert valid_params.property_value == "100"

    def test_xss_sanitization_in_property_params(self):
        """Test XSS sanitization in property parameters"""
        # Test with safe content that gets sanitized
        params = BlueprintPropertyParams(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Description",
            property_value="<b>Bold</b> text with safe HTML",
            property_type="string"
        )

        # Property value should be HTML escaped
        assert "&lt;b&gt;" in params.property_value
        assert "<b>" not in params.property_value

        # Test that dangerous scripts are rejected
        with pytest.raises(ValueError, match="dangerous content"):
            BlueprintPropertyParams(
                blueprint_path="/Game/Blueprints/TestActor",
                property_name="Description",
                property_value="<script>alert('xss')</script>Safe Text",
                property_type="string"
            )


class TestSecurityHelpers:
    """Test security helper functions"""

    def test_validate_blueprint_creation_params_success(self):
        """Test successful blueprint creation parameter validation"""
        # Should not raise exception
        validate_blueprint_creation_params(
            blueprint_name="TestActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

    def test_validate_blueprint_creation_params_failure(self):
        """Test blueprint creation parameter validation failure"""
        with pytest.raises(SecurityError) as exc_info:
            validate_blueprint_creation_params(
                blueprint_name="123Invalid",
                parent_class="InvalidClass",
                asset_path="/InvalidPath/"
            )

        # Should contain multiple errors
        assert len(exc_info.value.errors) >= 3

    def test_validate_property_setting_params_success(self):
        """Test successful property setting parameter validation"""
        result = validate_property_setting_params(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Health",
            property_value="100"
        )

        assert "blueprint_path" in result
        assert "property_name" in result
        assert "property_value" in result

    def test_validate_property_setting_params_failure(self):
        """Test property setting parameter validation failure"""
        with pytest.raises(SecurityError) as exc_info:
            validate_property_setting_params(
                blueprint_path="/InvalidPath/",
                property_name="123Invalid",
                property_value="<script>alert('xss')</script>"
            )

        # Should contain errors
        assert len(exc_info.value.errors) >= 2


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v"])