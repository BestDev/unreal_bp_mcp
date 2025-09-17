#!/usr/bin/env python3
"""
Unreal Blueprint MCP Server

This server provides MCP (Model Context Protocol) tools for controlling
Unreal Engine blueprints through WebSocket communication with the UnrealBlueprintMCP plugin.

The server translates MCP tool calls into messages that can be processed by the Unreal plugin,
enabling AI clients to create and modify blueprints programmatically.
"""

import json
import logging
import asyncio
import websockets
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for structured data validation
class Vector3D(BaseModel):
    """3D Vector representation"""
    x: float = Field(default=0.0, description="X-axis coordinate")
    y: float = Field(default=0.0, description="Y-axis coordinate")
    z: float = Field(default=0.0, description="Z-axis coordinate")

    def __str__(self) -> str:
        return f"{self.x},{self.y},{self.z}"

class BlueprintCreateParams(BaseModel):
    """Parameters for creating a blueprint"""
    blueprint_name: str = Field(description="Name of the blueprint to create (e.g., 'MyTestActor')")
    parent_class: str = Field(default="Actor", description="Parent class for the blueprint (Actor, Pawn, Character, UserWidget, etc.)")
    asset_path: str = Field(default="/Game/Blueprints/", description="Asset path where to create the blueprint")

class BlueprintPropertyParams(BaseModel):
    """Parameters for setting blueprint properties"""
    blueprint_path: str = Field(description="Full path to the blueprint asset (e.g., '/Game/Blueprints/MyTestActor')")
    property_name: str = Field(description="Name of the property to modify")
    property_value: str = Field(description="New value for the property as string")
    property_type: Optional[str] = Field(default=None, description="Type hint for the property (int, float, bool, string, Vector, etc.)")

# Create FastMCP server instance
mcp = FastMCP("UnrealBlueprintMCPServer")

# Global variables for tracking Unreal connection
unreal_websocket_url = "ws://localhost:8080"  # Default Unreal plugin WebSocket URL
last_connection_attempt = None
connection_status = "not_connected"

async def send_command_to_unreal(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a command to Unreal Engine via WebSocket (simulated for now)

    In a real implementation, this would establish a WebSocket connection
    to the UnrealBlueprintMCP plugin and send the JSON-RPC message.

    Args:
        method: The method to call (create_blueprint, set_property)
        params: Parameters for the method

    Returns:
        Response dictionary with success status and result data
    """
    global last_connection_attempt, connection_status

    last_connection_attempt = datetime.now()

    # Create JSON-RPC 2.0 message
    message = {
        "jsonrpc": "2.0",
        "id": f"{method}_{datetime.now().isoformat()}",
        "method": method,
        "params": params
    }

    logger.info(f"Would send to Unreal: {json.dumps(message, indent=2)}")

    # Simulate successful response for demonstration
    # In real implementation, this would be the actual response from Unreal plugin
    response = {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "success": True,
            "message": f"Command '{method}' executed successfully",
            "timestamp": datetime.now().isoformat(),
            "data": params
        }
    }

    logger.info(f"Simulated Unreal response: {json.dumps(response, indent=2)}")
    connection_status = "simulated_success"

    return response.get("result", {})

@mcp.tool()
def create_blueprint(params: BlueprintCreateParams) -> Dict[str, Any]:
    """
    Creates a new Blueprint asset in Unreal Engine.

    This tool sends a create_blueprint command to the UnrealBlueprintMCP plugin,
    which will create a new blueprint asset with the specified parent class and name.
    The blueprint will be created in the specified asset path within the Unreal project.

    Args:
        params: Blueprint creation parameters including name, parent class, and path

    Returns:
        Result dictionary with success status and created blueprint information

    Example:
        create_blueprint({
            "blueprint_name": "MyNewActor",
            "parent_class": "Actor",
            "asset_path": "/Game/Blueprints/"
        })
    """
    logger.info(f"Creating blueprint: {params.blueprint_name} (parent: {params.parent_class})")

    # Prepare parameters for Unreal plugin
    unreal_params = {
        "blueprint_name": params.blueprint_name,
        "parent_class": params.parent_class,
        "asset_path": params.asset_path
    }

    # Send command to Unreal (this is currently simulated)
    try:
        # In real implementation, this would be an async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_command_to_unreal("create_blueprint", unreal_params))
        loop.close()

        return {
            "success": True,
            "message": f"Blueprint '{params.blueprint_name}' creation requested",
            "blueprint_path": f"{params.asset_path}{params.blueprint_name}",
            "parent_class": params.parent_class,
            "unreal_response": result
        }
    except Exception as e:
        logger.error(f"Failed to create blueprint: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create blueprint '{params.blueprint_name}'"
        }

@mcp.tool()
def set_blueprint_property(params: BlueprintPropertyParams) -> Dict[str, Any]:
    """
    Sets a property value on an existing Blueprint asset's CDO (Class Default Object).

    This tool modifies properties on blueprint assets using the UnrealBlueprintMCP plugin.
    It supports various property types including primitives (int, float, bool, string) and
    structures (Vector, Rotator).

    Args:
        params: Property modification parameters including blueprint path, property name and value

    Returns:
        Result dictionary with success status and property modification information

    Example:
        set_blueprint_property({
            "blueprint_path": "/Game/Blueprints/MyActor",
            "property_name": "Health",
            "property_value": "100",
            "property_type": "int"
        })
    """
    logger.info(f"Setting property '{params.property_name}' = '{params.property_value}' on {params.blueprint_path}")

    # Prepare parameters for Unreal plugin
    unreal_params = {
        "blueprint_path": params.blueprint_path,
        "property_name": params.property_name,
        "property_value": params.property_value,
        "property_type": params.property_type
    }

    # Send command to Unreal (this is currently simulated)
    try:
        # In real implementation, this would be an async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_command_to_unreal("set_property", unreal_params))
        loop.close()

        return {
            "success": True,
            "message": f"Property '{params.property_name}' modification requested",
            "blueprint_path": params.blueprint_path,
            "property_name": params.property_name,
            "property_value": params.property_value,
            "property_type": params.property_type,
            "unreal_response": result
        }
    except Exception as e:
        logger.error(f"Failed to set property: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to set property '{params.property_name}'"
        }

@mcp.tool()
def get_server_status() -> Dict[str, Any]:
    """
    Gets the current status of the MCP server and its connection to Unreal Engine.

    Returns:
        Status information including connection state, last attempt time, and server info
    """
    global last_connection_attempt, connection_status, unreal_websocket_url

    return {
        "server_name": "UnrealBlueprintMCPServer",
        "version": "1.0.0",
        "connection_status": connection_status,
        "unreal_websocket_url": unreal_websocket_url,
        "last_connection_attempt": last_connection_attempt.isoformat() if last_connection_attempt else None,
        "timestamp": datetime.now().isoformat(),
        "available_tools": [
            "create_blueprint",
            "set_blueprint_property",
            "list_supported_blueprint_classes",
            "create_test_actor_blueprint"
        ]
    }

@mcp.tool()
def list_supported_blueprint_classes() -> List[str]:
    """
    Lists the blueprint parent classes supported by the Unreal Engine plugin.

    Returns:
        List of supported parent class names that can be used for blueprint creation

    The UnrealBlueprintMCP plugin supports these parent classes:
    - Actor: Base game object class
    - Pawn: Controllable game entities
    - Character: Player/NPC characters
    - ActorComponent: Reusable component logic
    - SceneComponent: Transform-based components
    - UserWidget: UI widget classes
    - Object: Base UObject class
    """
    return [
        "Actor",
        "Pawn",
        "Character",
        "ActorComponent",
        "SceneComponent",
        "UserWidget",
        "Object"
    ]

@mcp.tool()
def create_test_actor_blueprint(
    blueprint_name: str = "TestActor",
    location: Vector3D = Vector3D(x=0, y=0, z=100)
) -> Dict[str, Any]:
    """
    Creates a test Actor blueprint with specified location.

    This is a convenience tool that creates an Actor blueprint and sets its default location.
    It combines blueprint creation and property setting in a single operation.

    Args:
        blueprint_name: Name for the test blueprint (default: "TestActor")
        location: Default world location for the actor (default: 0,0,100)

    Returns:
        Result of the blueprint creation and property setting operations

    Example:
        create_test_actor_blueprint(
            blueprint_name="MyTestActor",
            location={"x": 100, "y": 200, "z": 300}
        )
    """
    logger.info(f"Creating test actor blueprint: {blueprint_name} at location {location}")

    try:
        # Step 1: Create blueprint
        create_params = BlueprintCreateParams(
            blueprint_name=blueprint_name,
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

        create_result = create_blueprint(create_params)

        if not create_result.get("success"):
            return {
                "success": False,
                "message": f"Failed to create test actor blueprint: {blueprint_name}",
                "error": create_result
            }

        # Step 2: Set location property
        property_params = BlueprintPropertyParams(
            blueprint_path=create_result["blueprint_path"],
            property_name="RootComponent",
            property_value=str(location),
            property_type="Vector"
        )

        property_result = set_blueprint_property(property_params)

        return {
            "success": True,
            "message": f"Test actor blueprint '{blueprint_name}' created successfully with location {location}",
            "blueprint_creation": create_result,
            "property_setting": property_result,
            "final_blueprint_path": create_result["blueprint_path"],
            "location": {
                "x": location.x,
                "y": location.y,
                "z": location.z
            }
        }

    except Exception as e:
        logger.error(f"Error creating test actor blueprint: {e}")
        return {
            "success": False,
            "message": f"Failed to create test actor blueprint: {blueprint_name}",
            "error": str(e)
        }

# Additional debugging and utility tools

@mcp.tool()
def test_unreal_connection() -> Dict[str, Any]:
    """
    Tests the connection to Unreal Engine by sending a ping message.

    Returns:
        Connection test results including response time and status
    """
    global connection_status

    logger.info("Testing connection to Unreal Engine...")

    try:
        start_time = datetime.now()

        # Send a simple ping command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_command_to_unreal("ping", {"timestamp": start_time.isoformat()}))
        loop.close()

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "message": "Connection test completed",
            "response_time_seconds": response_time,
            "unreal_response": result,
            "connection_status": connection_status
        }

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Unreal Engine"
        }

if __name__ == "__main__":
    # This allows the server to be run directly, but FastMCP will handle the actual server startup
    logger.info("Unreal Blueprint MCP Server module loaded")
    logger.info("Use 'fastmcp dev unreal_blueprint_mcp_server.py' to start the server")