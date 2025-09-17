#!/usr/bin/env python3
"""
Unreal Blueprint MCP Server

This server provides MCP (Model Context Protocol) tools for controlling
Unreal Engine blueprints through WebSocket communication with the UnrealBlueprintMCP plugin.

The server operates as a WebSocket server that accepts connections from Unreal Engine clients,
translating MCP tool calls into JSON-RPC 2.0 messages for the Unreal plugin.
"""

import json
import logging
import asyncio
import websockets
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
import uuid
import traceback

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

# Global variables for WebSocket server management
WS_HOST = "localhost"
WS_PORT = 8080
CLIENTS: Set[websockets.WebSocketServerProtocol] = set()
unreal_client: Optional[websockets.WebSocketServerProtocol] = None
ws_server: Optional[websockets.WebSocketServer] = None
last_connection_attempt: Optional[datetime] = None
connection_status = "server_not_started"
server_start_time: Optional[datetime] = None

# WebSocket Connection Management
async def register_client(websocket: websockets.WebSocketServerProtocol, path: str):
    """Register a new Unreal Engine client connection"""
    global unreal_client, connection_status, last_connection_attempt

    CLIENTS.add(websocket)
    unreal_client = websocket
    last_connection_attempt = datetime.now()
    connection_status = "connected"

    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Unreal Engine client connected from {client_info}")

    try:
        # Keep connection alive and handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from Unreal: {data}")
                # Here we could handle unsolicited messages from Unreal if needed
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from client: {e}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_info} disconnected")
    except Exception as e:
        logger.error(f"Error handling client {client_info}: {e}")
    finally:
        await unregister_client(websocket)

async def unregister_client(websocket: websockets.WebSocketServerProtocol):
    """Unregister a client connection"""
    global unreal_client, connection_status

    CLIENTS.discard(websocket)
    if unreal_client == websocket:
        unreal_client = None
        connection_status = "disconnected"
        logger.info("Primary Unreal Engine client disconnected")

async def send_command_to_unreal(method: str, params: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
    """
    Send a command to connected Unreal Engine client via WebSocket

    Args:
        method: The RPC method to call (create_blueprint, set_property, etc.)
        params: Parameters for the method
        timeout: Maximum time to wait for response in seconds

    Returns:
        Response dictionary from Unreal Engine

    Raises:
        ConnectionError: If no Unreal client is connected
        TimeoutError: If Unreal doesn't respond within timeout
        ValueError: If Unreal returns an error response
    """
    global unreal_client, last_connection_attempt, connection_status

    if not unreal_client:
        connection_status = "no_client"
        raise ConnectionError("No Unreal Engine client is currently connected. Please ensure the UnrealBlueprintMCP plugin is running and connected.")

    # Generate unique message ID
    message_id = str(uuid.uuid4())

    # Create JSON-RPC 2.0 message
    message = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": method,
        "params": params
    }

    last_connection_attempt = datetime.now()
    logger.info(f"Sending to Unreal: {json.dumps(message)}")

    try:
        # Send message to Unreal
        await unreal_client.send(json.dumps(message))

        # Wait for response with timeout
        response_str = await asyncio.wait_for(unreal_client.recv(), timeout=timeout)
        response = json.loads(response_str)

        logger.info(f"Received from Unreal: {json.dumps(response)}")

        # Validate JSON-RPC response
        if response.get("jsonrpc") != "2.0":
            raise ValueError("Invalid JSON-RPC response from Unreal")

        if response.get("id") != message_id:
            raise ValueError("Response ID mismatch from Unreal")

        # Check for RPC error
        if "error" in response:
            error = response["error"]
            raise ValueError(f"Unreal RPC Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")

        connection_status = "connected"
        return response.get("result", {})

    except websockets.exceptions.ConnectionClosed:
        connection_status = "disconnected"
        logger.error("Connection to Unreal Engine was closed")
        await unregister_client(unreal_client)
        raise ConnectionError("Connection to Unreal Engine was closed during communication")

    except asyncio.TimeoutError:
        connection_status = "timeout"
        logger.error(f"Timeout waiting for response from Unreal Engine (>{timeout}s)")
        raise TimeoutError(f"No response from Unreal Engine within {timeout} seconds")

    except json.JSONDecodeError as e:
        connection_status = "protocol_error"
        logger.error(f"Invalid JSON response from Unreal: {e}")
        raise ValueError(f"Invalid JSON response from Unreal Engine: {e}")

    except Exception as e:
        connection_status = "error"
        logger.error(f"Unexpected error communicating with Unreal: {e}")
        raise

@mcp.tool()
async def create_blueprint(params: BlueprintCreateParams) -> Dict[str, Any]:
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

    try:
        # Send command to Unreal Engine
        result = await send_command_to_unreal("create_blueprint", unreal_params)

        # Construct the expected blueprint path
        blueprint_path = f"{params.asset_path.rstrip('/')}/{params.blueprint_name}"

        return {
            "success": True,
            "message": f"Blueprint '{params.blueprint_name}' created successfully",
            "blueprint_path": blueprint_path,
            "parent_class": params.parent_class,
            "unreal_response": result
        }

    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error(f"Failed to create blueprint: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create blueprint '{params.blueprint_name}': {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error creating blueprint: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "message": f"Failed to create blueprint '{params.blueprint_name}' due to unexpected error"
        }

@mcp.tool()
async def set_blueprint_property(params: BlueprintPropertyParams) -> Dict[str, Any]:
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

    try:
        # Send command to Unreal Engine
        result = await send_command_to_unreal("set_property", unreal_params)

        return {
            "success": True,
            "message": f"Property '{params.property_name}' set successfully",
            "blueprint_path": params.blueprint_path,
            "property_name": params.property_name,
            "property_value": params.property_value,
            "property_type": params.property_type,
            "unreal_response": result
        }

    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error(f"Failed to set property: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to set property '{params.property_name}': {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error setting property: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "message": f"Failed to set property '{params.property_name}' due to unexpected error"
        }

@mcp.tool()
async def get_server_status() -> Dict[str, Any]:
    """
    Gets the current status of the MCP server and its connection to Unreal Engine.

    Returns:
        Status information including connection state, last attempt time, and server info
    """
    global last_connection_attempt, connection_status, server_start_time, ws_server

    # Count active connections
    active_connections = len(CLIENTS)
    has_primary_client = unreal_client is not None

    # WebSocket server status
    ws_server_status = "stopped"
    if ws_server:
        if ws_server.is_serving():
            ws_server_status = "running"
        else:
            ws_server_status = "stopped"

    return {
        "server_name": "UnrealBlueprintMCPServer",
        "version": "2.0.0",
        "websocket_server": {
            "status": ws_server_status,
            "host": WS_HOST,
            "port": WS_PORT,
            "url": f"ws://{WS_HOST}:{WS_PORT}"
        },
        "connection_status": connection_status,
        "client_connections": {
            "active_count": active_connections,
            "has_primary_client": has_primary_client,
            "primary_client_address": f"{unreal_client.remote_address[0]}:{unreal_client.remote_address[1]}" if unreal_client else None
        },
        "last_connection_attempt": last_connection_attempt.isoformat() if last_connection_attempt else None,
        "server_start_time": server_start_time.isoformat() if server_start_time else None,
        "timestamp": datetime.now().isoformat(),
        "available_tools": [
            "create_blueprint",
            "set_blueprint_property",
            "list_supported_blueprint_classes",
            "create_test_actor_blueprint",
            "test_unreal_connection",
            "start_websocket_server",
            "stop_websocket_server"
        ]
    }

@mcp.tool()
async def list_supported_blueprint_classes() -> List[str]:
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
async def create_test_actor_blueprint(
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

        create_result = await create_blueprint(create_params)

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

        property_result = await set_blueprint_property(property_params)

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
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Failed to create test actor blueprint: {blueprint_name}",
            "error": str(e)
        }

# Additional debugging and utility tools

@mcp.tool()
async def test_unreal_connection() -> Dict[str, Any]:
    """
    Tests the connection to Unreal Engine by sending a ping message.

    Returns:
        Connection test results including response time and status
    """
    global connection_status

    logger.info("Testing connection to Unreal Engine...")

    try:
        start_time = datetime.now()

        # Send a simple ping command with current timestamp
        result = await send_command_to_unreal("ping", {
            "timestamp": start_time.isoformat(),
            "test_message": "Connection test from MCP server"
        })

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "message": "Connection test completed successfully",
            "response_time_seconds": response_time,
            "test_timestamp": start_time.isoformat(),
            "unreal_response": result,
            "connection_status": connection_status
        }

    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Connection test failed: {e}",
            "connection_status": connection_status
        }
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "message": "Connection test failed due to unexpected error"
        }

# WebSocket Server Management Tools

@mcp.tool()
async def start_websocket_server() -> Dict[str, Any]:
    """
    Starts the WebSocket server to accept connections from Unreal Engine clients.

    Returns:
        Status of the server start operation
    """
    global ws_server, server_start_time, connection_status

    if ws_server and ws_server.is_serving():
        return {
            "success": False,
            "message": "WebSocket server is already running",
            "server_url": f"ws://{WS_HOST}:{WS_PORT}",
            "start_time": server_start_time.isoformat() if server_start_time else None
        }

    try:
        # Start WebSocket server
        ws_server = await websockets.serve(register_client, WS_HOST, WS_PORT)
        server_start_time = datetime.now()
        connection_status = "server_running"

        logger.info(f"WebSocket server started on ws://{WS_HOST}:{WS_PORT}")

        return {
            "success": True,
            "message": "WebSocket server started successfully",
            "server_url": f"ws://{WS_HOST}:{WS_PORT}",
            "start_time": server_start_time.isoformat(),
            "host": WS_HOST,
            "port": WS_PORT
        }

    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"Port {WS_PORT} is already in use")
            return {
                "success": False,
                "error": f"Port {WS_PORT} is already in use",
                "message": "Another application is using the WebSocket port"
            }
        else:
            logger.error(f"Failed to start WebSocket server: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start WebSocket server"
            }
    except Exception as e:
        logger.error(f"Unexpected error starting WebSocket server: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to start WebSocket server due to unexpected error"
        }

@mcp.tool()
async def stop_websocket_server() -> Dict[str, Any]:
    """
    Stops the WebSocket server and disconnects all clients.

    Returns:
        Status of the server stop operation
    """
    global ws_server, connection_status, unreal_client

    if not ws_server or not ws_server.is_serving():
        return {
            "success": False,
            "message": "WebSocket server is not running"
        }

    try:
        # Close all client connections
        if CLIENTS:
            await asyncio.gather(
                *[client.close() for client in CLIENTS.copy()],
                return_exceptions=True
            )
            CLIENTS.clear()

        # Stop the server
        ws_server.close()
        await ws_server.wait_closed()

        ws_server = None
        unreal_client = None
        connection_status = "server_stopped"

        logger.info("WebSocket server stopped")

        return {
            "success": True,
            "message": "WebSocket server stopped successfully"
        }

    except Exception as e:
        logger.error(f"Error stopping WebSocket server: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to stop WebSocket server"
        }

# Server initialization - this will be called by FastMCP
async def initialize_server():
    """
    Initialize the WebSocket server when the MCP server starts.
    This function can be called during server startup.
    """
    try:
        result = await start_websocket_server()
        if result["success"]:
            logger.info("WebSocket server initialized successfully")
        else:
            logger.warning(f"Failed to initialize WebSocket server: {result['message']}")
    except Exception as e:
        logger.error(f"Error during server initialization: {e}")

if __name__ == "__main__":
    # This allows the server to be run directly, but FastMCP will handle the actual server startup
    logger.info("Unreal Blueprint MCP Server module loaded")
    logger.info("WebSocket server management enabled")
    logger.info("Use 'fastmcp dev unreal_blueprint_mcp_server.py' to start the MCP server")
    logger.info(f"WebSocket server will be available at ws://{WS_HOST}:{WS_PORT}")

    # For direct testing, you can run the WebSocket server
    # asyncio.run(initialize_server())