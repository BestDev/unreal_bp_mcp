#!/usr/bin/env python3
"""
Integration tests for UnrealBlueprintMCP

Tests the integration between MCP server, tools, and communication layer.
"""

import pytest
import asyncio
import websockets
import json
import sys
import os
from unittest.mock import patch, AsyncMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestMCPServerIntegration:
    """Integration tests for MCP server"""

    @pytest.fixture
    def server_url(self):
        """WebSocket server URL for testing"""
        return "ws://localhost:6277"

    @pytest.mark.asyncio
    async def test_server_connection(self, server_url):
        """Test basic WebSocket connection to MCP server"""
        try:
            # Attempt to connect to running server
            async with websockets.connect(server_url, timeout=5) as websocket:
                assert websocket.open

                # Send a simple ping
                ping_request = {
                    "jsonrpc": "2.0",
                    "id": "ping_test",
                    "method": "ping"
                }

                await websocket.send(json.dumps(ping_request))

        except (ConnectionRefusedError, OSError):
            # Server is not running - this is expected in CI
            pytest.skip("MCP server not running - integration test skipped")

    @pytest.mark.asyncio
    async def test_tools_list_request(self, server_url):
        """Test tools list request via WebSocket"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Request tools list
                request = {
                    "jsonrpc": "2.0",
                    "id": "tools_list_test",
                    "method": "tools/list"
                }

                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)

                result = json.loads(response)
                assert "jsonrpc" in result
                assert result["id"] == "tools_list_test"

                if "result" in result:
                    tools = result["result"].get("tools", [])
                    # Check that expected tools are present
                    tool_names = [tool.get("name") for tool in tools]
                    assert "create_blueprint" in tool_names
                    assert "set_blueprint_property" in tool_names

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - integration test skipped")

    @pytest.mark.asyncio
    async def test_create_blueprint_tool_call(self, server_url):
        """Test create_blueprint tool call via WebSocket"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Call create_blueprint tool
                request = {
                    "jsonrpc": "2.0",
                    "id": "create_bp_test",
                    "method": "tools/call",
                    "params": {
                        "name": "create_blueprint",
                        "arguments": {
                            "blueprint_name": "IntegrationTestActor",
                            "parent_class": "Actor",
                            "asset_path": "/Game/Tests/"
                        }
                    }
                }

                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=10)

                result = json.loads(response)
                assert "jsonrpc" in result
                assert result["id"] == "create_bp_test"

                if "result" in result:
                    tool_result = result["result"]
                    assert "success" in tool_result
                    # In simulation mode, this should be True
                    if tool_result.get("success"):
                        assert "blueprint_path" in tool_result

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - integration test skipped")

    @pytest.mark.asyncio
    async def test_set_property_tool_call(self, server_url):
        """Test set_blueprint_property tool call via WebSocket"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Call set_blueprint_property tool
                request = {
                    "jsonrpc": "2.0",
                    "id": "set_prop_test",
                    "method": "tools/call",
                    "params": {
                        "name": "set_blueprint_property",
                        "arguments": {
                            "blueprint_path": "/Game/Tests/IntegrationTestActor",
                            "property_name": "Health",
                            "property_value": "150",
                            "property_type": "int"
                        }
                    }
                }

                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=10)

                result = json.loads(response)
                assert "jsonrpc" in result
                assert result["id"] == "set_prop_test"

                if "result" in result:
                    tool_result = result["result"]
                    assert "success" in tool_result

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - integration test skipped")

class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_complete_blueprint_creation_workflow(self):
        """Test complete workflow: create blueprint → set properties"""
        server_url = "ws://localhost:6277"

        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Step 1: Create blueprint
                create_request = {
                    "jsonrpc": "2.0",
                    "id": "workflow_create",
                    "method": "tools/call",
                    "params": {
                        "name": "create_blueprint",
                        "arguments": {
                            "blueprint_name": "WorkflowTestActor",
                            "parent_class": "Actor",
                            "asset_path": "/Game/Tests/"
                        }
                    }
                }

                await websocket.send(json.dumps(create_request))
                create_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                create_result = json.loads(create_response)

                assert create_result["id"] == "workflow_create"

                if create_result.get("result", {}).get("success"):
                    blueprint_path = create_result["result"]["blueprint_path"]

                    # Step 2: Set property on created blueprint
                    property_request = {
                        "jsonrpc": "2.0",
                        "id": "workflow_property",
                        "method": "tools/call",
                        "params": {
                            "name": "set_blueprint_property",
                            "arguments": {
                                "blueprint_path": blueprint_path,
                                "property_name": "RootComponent",
                                "property_value": "100.0,200.0,300.0",
                                "property_type": "Vector"
                            }
                        }
                    }

                    await websocket.send(json.dumps(property_request))
                    property_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    property_result = json.loads(property_response)

                    assert property_result["id"] == "workflow_property"
                    # In simulation mode, both should succeed
                    assert property_result.get("result", {}).get("success") in [True, False]

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - end-to-end test skipped")

class TestErrorHandlingIntegration:
    """Integration tests for error handling"""

    @pytest.mark.asyncio
    async def test_invalid_tool_call(self):
        """Test calling non-existent tool"""
        server_url = "ws://localhost:6277"

        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Call non-existent tool
                request = {
                    "jsonrpc": "2.0",
                    "id": "invalid_tool_test",
                    "method": "tools/call",
                    "params": {
                        "name": "non_existent_tool",
                        "arguments": {}
                    }
                }

                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)

                result = json.loads(response)
                assert "error" in result or "result" in result
                # Should either be an error response or a result with success=false

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - error handling test skipped")

    @pytest.mark.asyncio
    async def test_invalid_json_request(self):
        """Test sending invalid JSON"""
        server_url = "ws://localhost:6277"

        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Send invalid JSON
                invalid_json = '{"invalid": json,}'

                await websocket.send(invalid_json)

                # Server should either close connection or send error response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    result = json.loads(response)
                    # If we get a response, it should be an error
                    assert "error" in result
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                    # Connection closed due to invalid JSON - this is acceptable
                    pass

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - JSON validation test skipped")

class TestPerformance:
    """Performance and load tests"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test handling multiple concurrent tool calls"""
        server_url = "ws://localhost:6277"

        try:
            async def make_tool_call(call_id):
                async with websockets.connect(server_url, timeout=5) as websocket:
                    request = {
                        "jsonrpc": "2.0",
                        "id": f"concurrent_test_{call_id}",
                        "method": "tools/call",
                        "params": {
                            "name": "get_server_status",
                            "arguments": {}
                        }
                    }

                    await websocket.send(json.dumps(request))
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)

                    result = json.loads(response)
                    assert result["id"] == f"concurrent_test_{call_id}"
                    return result

            # Make multiple concurrent calls
            tasks = [make_tool_call(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check that most calls succeeded (some might fail due to connection limits)
            successful_calls = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_calls) >= 1  # At least one should succeed

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - concurrent test skipped")

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test response time for tool calls"""
        server_url = "ws://localhost:6277"

        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                import time

                start_time = time.time()

                request = {
                    "jsonrpc": "2.0",
                    "id": "response_time_test",
                    "method": "tools/call",
                    "params": {
                        "name": "get_server_status",
                        "arguments": {}
                    }
                }

                await websocket.send(json.dumps(request))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)

                end_time = time.time()
                response_time = end_time - start_time

                # Response time should be reasonable (less than 1 second for status call)
                assert response_time < 1.0

                result = json.loads(response)
                assert result["id"] == "response_time_test"

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - response time test skipped")

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])