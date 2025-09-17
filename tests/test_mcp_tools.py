#!/usr/bin/env python3
"""
Unit tests for MCP tools

Tests the individual MCP tools to ensure they respond correctly
to various input parameters and handle errors appropriately.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the send_command_to_unreal function since we're testing without Unreal
async def mock_send_command_success(method: str, params: dict):
    """Mock successful Unreal command"""
    return {
        "success": True,
        "message": f"Command '{method}' executed successfully",
        "timestamp": "2025-09-17T00:00:00.000Z",
        "data": params
    }

async def mock_send_command_failure(method: str, params: dict):
    """Mock failed Unreal command"""
    return {
        "success": False,
        "message": f"Command '{method}' failed",
        "error": "Simulated error",
        "timestamp": "2025-09-17T00:00:00.000Z"
    }

class TestMCPTools:
    """Test cases for MCP tools"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Import here to avoid import issues
        global unreal_blueprint_mcp_server
        import unreal_blueprint_mcp_server
        self.server_module = unreal_blueprint_mcp_server

    @pytest.mark.asyncio
    async def test_get_server_status(self):
        """Test get_server_status tool"""
        # Import the actual function implementation from the server module
        from unreal_blueprint_mcp_server import get_server_status

        status = get_server_status()

        assert isinstance(status, dict)
        assert "server_name" in status
        assert "version" in status
        assert "available_tools" in status
        assert status["server_name"] == "UnrealBlueprintMCPServer"
        assert len(status["available_tools"]) == 4  # Expected number of tools

    @pytest.mark.asyncio
    async def test_list_supported_blueprint_classes(self):
        """Test list_supported_blueprint_classes tool"""
        from unreal_blueprint_mcp_server import list_supported_blueprint_classes

        classes = list_supported_blueprint_classes()

        assert isinstance(classes, list)
        assert len(classes) == 7  # Expected number of supported classes
        assert "Actor" in classes
        assert "Pawn" in classes
        assert "Character" in classes
        assert "UserWidget" in classes

    @pytest.mark.asyncio
    @patch('unreal_blueprint_mcp_server.send_command_to_unreal', side_effect=mock_send_command_success)
    async def test_create_blueprint_success(self, mock_send):
        """Test successful blueprint creation"""
        from unreal_blueprint_mcp_server import create_blueprint, BlueprintCreateParams

        params = BlueprintCreateParams(
            blueprint_name="TestActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

        result = create_blueprint(params)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "blueprint_path" in result
        assert result["blueprint_path"] == "/Game/Blueprints/TestActor"
        assert result["parent_class"] == "Actor"

    @pytest.mark.asyncio
    @patch('unreal_blueprint_mcp_server.send_command_to_unreal', side_effect=mock_send_command_failure)
    async def test_create_blueprint_failure(self, mock_send):
        """Test blueprint creation failure"""
        from unreal_blueprint_mcp_server import create_blueprint, BlueprintCreateParams

        params = BlueprintCreateParams(
            blueprint_name="FailActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

        result = create_blueprint(params)

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    @patch('unreal_blueprint_mcp_server.send_command_to_unreal', side_effect=mock_send_command_success)
    async def test_set_blueprint_property_success(self, mock_send):
        """Test successful blueprint property setting"""
        from unreal_blueprint_mcp_server import set_blueprint_property, BlueprintPropertyParams

        params = BlueprintPropertyParams(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Health",
            property_value="100",
            property_type="int"
        )

        result = set_blueprint_property(params)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["property_name"] == "Health"
        assert result["property_value"] == "100"
        assert result["property_type"] == "int"

    @pytest.mark.asyncio
    @patch('unreal_blueprint_mcp_server.send_command_to_unreal', side_effect=mock_send_command_success)
    async def test_create_test_actor_blueprint(self, mock_send):
        """Test create_test_actor_blueprint tool"""
        from unreal_blueprint_mcp_server import create_test_actor_blueprint, Vector3D

        location = Vector3D(x=100, y=200, z=300)
        result = create_test_actor_blueprint("TestActor", location)

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "location" in result
        assert result["location"]["x"] == 100.0
        assert result["location"]["y"] == 200.0
        assert result["location"]["z"] == 300.0

    @pytest.mark.asyncio
    @patch('unreal_blueprint_mcp_server.send_command_to_unreal', side_effect=mock_send_command_success)
    async def test_test_unreal_connection(self, mock_send):
        """Test test_unreal_connection tool"""
        from unreal_blueprint_mcp_server import test_unreal_connection

        result = test_unreal_connection()

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "response_time_seconds" in result
        assert "connection_status" in result

class TestDataValidation:
    """Test data validation and Pydantic models"""

    def test_vector3d_validation(self):
        """Test Vector3D model validation"""
        from unreal_blueprint_mcp_server import Vector3D

        # Valid vector
        vector = Vector3D(x=1.0, y=2.0, z=3.0)
        assert vector.x == 1.0
        assert vector.y == 2.0
        assert vector.z == 3.0
        assert str(vector) == "1.0,2.0,3.0"

        # Default values
        vector_default = Vector3D()
        assert vector_default.x == 0.0
        assert vector_default.y == 0.0
        assert vector_default.z == 0.0

    def test_blueprint_create_params_validation(self):
        """Test BlueprintCreateParams model validation"""
        from unreal_blueprint_mcp_server import BlueprintCreateParams

        # Valid params
        params = BlueprintCreateParams(
            blueprint_name="TestActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )
        assert params.blueprint_name == "TestActor"
        assert params.parent_class == "Actor"
        assert params.asset_path == "/Game/Blueprints/"

        # Default values
        params_minimal = BlueprintCreateParams(blueprint_name="MinimalActor")
        assert params_minimal.blueprint_name == "MinimalActor"
        assert params_minimal.parent_class == "Actor"  # Default
        assert params_minimal.asset_path == "/Game/Blueprints/"  # Default

    def test_blueprint_property_params_validation(self):
        """Test BlueprintPropertyParams model validation"""
        from unreal_blueprint_mcp_server import BlueprintPropertyParams

        # Valid params with type
        params = BlueprintPropertyParams(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Health",
            property_value="100",
            property_type="int"
        )
        assert params.blueprint_path == "/Game/Blueprints/TestActor"
        assert params.property_name == "Health"
        assert params.property_value == "100"
        assert params.property_type == "int"

        # Valid params without type
        params_no_type = BlueprintPropertyParams(
            blueprint_path="/Game/Blueprints/TestActor",
            property_name="Name",
            property_value="TestName"
        )
        assert params_no_type.property_type is None

class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_blueprint_name(self):
        """Test handling of invalid blueprint names"""
        from unreal_blueprint_mcp_server import BlueprintCreateParams

        # Test empty name - should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            BlueprintCreateParams(blueprint_name="")

    @pytest.mark.asyncio
    async def test_invalid_parent_class(self):
        """Test handling of invalid parent classes"""
        from unreal_blueprint_mcp_server import BlueprintCreateParams

        # This should be valid at Pydantic level but caught at execution level
        params = BlueprintCreateParams(
            blueprint_name="TestActor",
            parent_class="InvalidClass"
        )
        assert params.parent_class == "InvalidClass"

    @pytest.mark.asyncio
    async def test_invalid_asset_path(self):
        """Test handling of invalid asset paths"""
        from unreal_blueprint_mcp_server import BlueprintCreateParams

        # This should be valid at Pydantic level but caught at execution level
        params = BlueprintCreateParams(
            blueprint_name="TestActor",
            asset_path="/Invalid/Path/"
        )
        assert params.asset_path == "/Invalid/Path/"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])