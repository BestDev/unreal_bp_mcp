#!/usr/bin/env python3
"""
Test MCP Server for UnrealBlueprintMCP Plugin

This script implements a simple WebSocket server that mimics the Python MCP server
to test the Unreal Engine plugin's WebSocket client functionality.

It supports the JSON-RPC 2.0 protocol and handles the blueprint operations
that the Unreal plugin expects.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPTestServer:
    """Test MCP Server implementation for Unreal Engine plugin testing"""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.connected_clients = set()

    async def register_client(self, websocket):
        """Register a new client connection"""
        self.connected_clients.add(websocket)
        logger.info(f"Client connected from {websocket.remote_address}")

    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.connected_clients.discard(websocket)
        logger.info(f"Client disconnected from {websocket.remote_address}")

    async def handle_message(self, websocket, message: str) -> Optional[str]:
        """Handle incoming JSON-RPC 2.0 message from client"""
        try:
            data = json.loads(message)
            logger.info(f"Received message: {data}")

            # Validate JSON-RPC 2.0 format
            if not self.validate_jsonrpc(data):
                return self.create_error_response(None, -32600, "Invalid Request")

            # Extract request details
            request_id = data.get("id")
            method = data.get("method")
            params = data.get("params", {})

            # Process the request
            if method == "create_blueprint":
                return await self.handle_create_blueprint(request_id, params)
            elif method == "set_property":
                return await self.handle_set_property(request_id, params)
            elif method == "add_component":
                return await self.handle_add_component(request_id, params)
            elif method == "compile_blueprint":
                return await self.handle_compile_blueprint(request_id, params)
            elif method == "get_server_status":
                return await self.handle_get_server_status(request_id, params)
            else:
                return self.create_error_response(request_id, -32601, f"Method not found: {method}")

        except json.JSONDecodeError:
            return self.create_error_response(None, -32700, "Parse error")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return self.create_error_response(None, -32603, "Internal error")

    def validate_jsonrpc(self, data: Dict[str, Any]) -> bool:
        """Validate JSON-RPC 2.0 format"""
        return (
            isinstance(data, dict) and
            data.get("jsonrpc") == "2.0" and
            "method" in data and
            isinstance(data["method"], str)
        )

    def create_success_response(self, request_id: str, result: Dict[str, Any]) -> str:
        """Create a successful JSON-RPC 2.0 response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        return json.dumps(response)

    def create_error_response(self, request_id: Optional[str], code: int, message: str) -> str:
        """Create an error JSON-RPC 2.0 response"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        return json.dumps(response)

    async def handle_create_blueprint(self, request_id: str, params: Dict[str, Any]) -> str:
        """Handle create_blueprint request"""
        blueprint_name = params.get("blueprint_name", "")
        parent_class = params.get("parent_class", "Actor")
        asset_path = params.get("asset_path", "/Game/Blueprints/")

        logger.info(f"Creating blueprint: {blueprint_name} (parent: {parent_class}) at {asset_path}")

        # Simulate blueprint creation
        await asyncio.sleep(0.1)  # Simulate processing time

        result = {
            "success": True,
            "message": f"Blueprint '{blueprint_name}' created successfully",
            "blueprint_path": f"{asset_path}{blueprint_name}",
            "parent_class": parent_class,
            "timestamp": datetime.now().isoformat()
        }

        return self.create_success_response(request_id, result)

    async def handle_set_property(self, request_id: str, params: Dict[str, Any]) -> str:
        """Handle set_property request"""
        blueprint_path = params.get("blueprint_path", "")
        property_name = params.get("property_name", "")
        property_value = params.get("property_value", "")

        logger.info(f"Setting property {property_name} = {property_value} on {blueprint_path}")

        # Simulate property setting
        await asyncio.sleep(0.05)

        result = {
            "success": True,
            "message": f"Property '{property_name}' set to '{property_value}'",
            "blueprint_path": blueprint_path,
            "timestamp": datetime.now().isoformat()
        }

        return self.create_success_response(request_id, result)

    async def handle_add_component(self, request_id: str, params: Dict[str, Any]) -> str:
        """Handle add_component request"""
        blueprint_path = params.get("blueprint_path", "")
        component_type = params.get("component_type", "")
        component_name = params.get("component_name", "")

        logger.info(f"Adding component {component_name} ({component_type}) to {blueprint_path}")

        # Simulate component addition
        await asyncio.sleep(0.1)

        result = {
            "success": True,
            "message": f"Component '{component_name}' of type '{component_type}' added successfully",
            "blueprint_path": blueprint_path,
            "component_name": component_name,
            "component_type": component_type,
            "timestamp": datetime.now().isoformat()
        }

        return self.create_success_response(request_id, result)

    async def handle_compile_blueprint(self, request_id: str, params: Dict[str, Any]) -> str:
        """Handle compile_blueprint request"""
        blueprint_path = params.get("blueprint_path", "")

        logger.info(f"Compiling blueprint: {blueprint_path}")

        # Simulate compilation
        await asyncio.sleep(0.2)

        result = {
            "success": True,
            "message": f"Blueprint '{blueprint_path}' compiled successfully",
            "blueprint_path": blueprint_path,
            "compilation_time": "0.2s",
            "timestamp": datetime.now().isoformat()
        }

        return self.create_success_response(request_id, result)

    async def handle_get_server_status(self, request_id: str, params: Dict[str, Any]) -> str:
        """Handle get_server_status request"""
        logger.info("Getting server status")

        result = {
            "online": True,
            "version": "1.0.0-test",
            "server_name": "MCPTestServer",
            "uptime": "N/A",
            "connected_clients": len(self.connected_clients),
            "supported_operations": [
                "create_blueprint",
                "set_property",
                "add_component",
                "compile_blueprint",
                "get_server_status"
            ],
            "supported_parent_classes": [
                "Actor",
                "Pawn",
                "Character",
                "ActorComponent",
                "SceneComponent",
                "UserWidget",
                "Object"
            ],
            "timestamp": datetime.now().isoformat()
        }

        return self.create_success_response(request_id, result)

    async def handle_client(self, websocket, path):
        """Handle a client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                response = await self.handle_message(websocket, message)
                if response:
                    await websocket.send(response)
                    logger.info(f"Sent response: {response}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting MCP test server on {self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"MCP test server running on ws://{self.host}:{self.port}")
            logger.info("Waiting for connections from Unreal Engine plugin...")
            await asyncio.Future()  # Run forever

async def main():
    """Main entry point"""
    server = MCPTestServer()

    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())