#!/usr/bin/env python3
"""
WebSocket communication tests

Tests the WebSocket communication layer between MCP server and clients.
"""

import pytest
import asyncio
import websockets
import json
import time
from unittest.mock import patch, AsyncMock

class TestWebSocketCommunication:
    """Test WebSocket communication functionality"""

    @pytest.fixture
    def server_url(self):
        """WebSocket server URL for testing"""
        return "ws://localhost:6277"

    @pytest.mark.asyncio
    async def test_basic_websocket_connection(self, server_url):
        """Test basic WebSocket connection establishment"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                assert websocket.open
                assert websocket.state == websockets.protocol.State.OPEN

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - WebSocket test skipped")

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, server_url):
        """Test WebSocket ping/pong mechanism"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Send ping
                pong_waiter = await websocket.ping()

                # Wait for pong with timeout
                await asyncio.wait_for(pong_waiter, timeout=5)

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - WebSocket ping test skipped")

    @pytest.mark.asyncio
    async def test_json_message_sending(self, server_url):
        """Test sending and receiving JSON messages"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Send JSON message
                test_message = {
                    "jsonrpc": "2.0",
                    "id": "test_json_message",
                    "method": "tools/list"
                }

                await websocket.send(json.dumps(test_message))

                # Receive response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                parsed_response = json.loads(response)

                assert "jsonrpc" in parsed_response
                assert parsed_response.get("id") == "test_json_message"

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - JSON message test skipped")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self, server_url):
        """Test handling multiple concurrent WebSocket connections"""
        try:
            async def create_connection(connection_id):
                async with websockets.connect(server_url, timeout=5) as websocket:
                    # Send a message to verify connection works
                    message = {
                        "jsonrpc": "2.0",
                        "id": f"concurrent_conn_{connection_id}",
                        "method": "tools/list"
                    }

                    await websocket.send(json.dumps(message))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)

                    return json.loads(response)

            # Create multiple concurrent connections
            tasks = [create_connection(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check that connections succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) >= 1

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - concurrent connections test skipped")

    @pytest.mark.asyncio
    async def test_large_message_handling(self, server_url):
        """Test handling of large JSON messages"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Create a large message
                large_params = {
                    "blueprint_name": "LargeTestActor",
                    "parent_class": "Actor",
                    "asset_path": "/Game/Tests/",
                    "large_data": "x" * 10000  # 10KB of data
                }

                large_message = {
                    "jsonrpc": "2.0",
                    "id": "large_message_test",
                    "method": "tools/call",
                    "params": {
                        "name": "create_blueprint",
                        "arguments": large_params
                    }
                }

                await websocket.send(json.dumps(large_message))
                response = await asyncio.wait_for(websocket.recv(), timeout=10)

                parsed_response = json.loads(response)
                assert parsed_response.get("id") == "large_message_test"

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - large message test skipped")

class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios"""

    @pytest.fixture
    def server_url(self):
        return "ws://localhost:6277"

    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, server_url):
        """Test server handling of invalid JSON"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                # Send invalid JSON
                invalid_json = '{"invalid": json without closing brace'

                await websocket.send(invalid_json)

                # Server should either close connection or send error response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    # If we get a response, check if it's an error
                    if response:
                        parsed = json.loads(response)
                        # Should contain error information
                        assert "error" in parsed or "jsonrpc" in parsed
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed, json.JSONDecodeError):
                    # Any of these responses is acceptable for invalid JSON
                    pass

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - invalid JSON test skipped")

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self):
        """Test connection timeout scenarios"""
        # Try to connect to non-existent server
        with pytest.raises((ConnectionRefusedError, OSError, asyncio.TimeoutError)):
            async with websockets.connect("ws://localhost:9999", timeout=2) as websocket:
                pass

    @pytest.mark.asyncio
    async def test_unexpected_connection_close(self, server_url):
        """Test handling of unexpected connection closure"""
        try:
            websocket = await websockets.connect(server_url, timeout=5)

            # Send a message
            message = {
                "jsonrpc": "2.0",
                "id": "close_test",
                "method": "tools/list"
            }

            await websocket.send(json.dumps(message))

            # Forcefully close the connection
            await websocket.close()

            # Verify connection is closed
            assert websocket.closed

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - connection close test skipped")

class TestWebSocketPerformance:
    """Test WebSocket performance characteristics"""

    @pytest.fixture
    def server_url(self):
        return "ws://localhost:6277"

    @pytest.mark.asyncio
    async def test_message_latency(self, server_url):
        """Test message round-trip latency"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                latencies = []

                for i in range(5):
                    start_time = time.time()

                    message = {
                        "jsonrpc": "2.0",
                        "id": f"latency_test_{i}",
                        "method": "tools/call",
                        "params": {
                            "name": "get_server_status",
                            "arguments": {}
                        }
                    }

                    await websocket.send(json.dumps(message))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)

                    end_time = time.time()
                    latency = end_time - start_time
                    latencies.append(latency)

                    # Verify we got the right response
                    parsed = json.loads(response)
                    assert parsed.get("id") == f"latency_test_{i}"

                # Check average latency is reasonable
                avg_latency = sum(latencies) / len(latencies)
                assert avg_latency < 1.0  # Should be less than 1 second

                # Check maximum latency
                max_latency = max(latencies)
                assert max_latency < 2.0  # Should be less than 2 seconds

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - latency test skipped")

    @pytest.mark.asyncio
    async def test_throughput(self, server_url):
        """Test message throughput"""
        try:
            async with websockets.connect(server_url, timeout=5) as websocket:
                num_messages = 10
                start_time = time.time()

                # Send multiple messages rapidly
                tasks = []
                for i in range(num_messages):
                    message = {
                        "jsonrpc": "2.0",
                        "id": f"throughput_test_{i}",
                        "method": "tools/call",
                        "params": {
                            "name": "get_server_status",
                            "arguments": {}
                        }
                    }

                    send_task = websocket.send(json.dumps(message))
                    tasks.append(send_task)

                # Wait for all sends to complete
                await asyncio.gather(*tasks)

                # Receive all responses
                responses = []
                for i in range(num_messages):
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    responses.append(json.loads(response))

                end_time = time.time()
                total_time = end_time - start_time

                # Calculate messages per second
                throughput = num_messages / total_time

                # Verify all responses received
                assert len(responses) == num_messages

                # Verify response IDs match
                response_ids = {r.get("id") for r in responses}
                expected_ids = {f"throughput_test_{i}" for i in range(num_messages)}
                assert response_ids == expected_ids

                # Basic throughput check (should handle at least 5 messages/second)
                assert throughput >= 5.0

        except (ConnectionRefusedError, OSError):
            pytest.skip("MCP server not running - throughput test skipped")

if __name__ == "__main__":
    # Run WebSocket tests
    pytest.main([__file__, "-v", "--tb=short"])