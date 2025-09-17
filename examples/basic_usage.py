#!/usr/bin/env python3
"""
Basic Usage Example for UnrealBlueprintMCP

This example demonstrates the fundamental operations:
1. Creating blueprints
2. Setting properties
3. Checking server status

Prerequisites:
- MCP server running: fastmcp dev unreal_blueprint_mcp_server.py
- Unreal Editor with UnrealBlueprintMCP plugin enabled
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unreal_mcp_client import UnrealBlueprintMCPClient

async def basic_blueprint_operations():
    """Demonstrate basic blueprint operations"""
    print("🎮 UnrealBlueprintMCP Basic Usage Example")
    print("=" * 50)

    # Initialize client
    client = UnrealBlueprintMCPClient()

    try:
        # 1. Check server status
        print("\n1️⃣ Checking MCP server status...")
        status = await client.get_server_status()
        print(f"   Server: {status.get('server_name')}")
        print(f"   Version: {status.get('version')}")
        print(f"   Status: {status.get('connection_status')}")

        # 2. List supported blueprint classes
        print("\n2️⃣ Supported blueprint classes:")
        classes = await client.list_supported_classes()
        for i, cls in enumerate(classes, 1):
            print(f"   {i}. {cls}")

        # 3. Create a simple Actor blueprint
        print("\n3️⃣ Creating Actor blueprint...")
        blueprint_result = await client.create_blueprint(
            name="BasicActor",
            parent_class="Actor",
            asset_path="/Game/Blueprints/"
        )

        if blueprint_result.get("success"):
            print(f"   ✅ Blueprint created: {blueprint_result.get('blueprint_path')}")
            blueprint_path = blueprint_result.get('blueprint_path')
        else:
            print(f"   ❌ Failed to create blueprint: {blueprint_result}")
            return

        # 4. Set a Vector property (location)
        print("\n4️⃣ Setting blueprint location...")
        location_result = await client.set_blueprint_property(
            blueprint_path=blueprint_path,
            property_name="RootComponent",
            property_value="100.0,200.0,300.0",
            property_type="Vector"
        )

        if location_result.get("success"):
            print(f"   ✅ Location set to (100, 200, 300)")
        else:
            print(f"   ❌ Failed to set location: {location_result}")

        # 5. Create a Character blueprint
        print("\n5️⃣ Creating Character blueprint...")
        character_result = await client.create_blueprint(
            name="BasicCharacter",
            parent_class="Character",
            asset_path="/Game/Blueprints/"
        )

        if character_result.get("success"):
            print(f"   ✅ Character blueprint created: {character_result.get('blueprint_path')}")

            # Set character health
            health_result = await client.set_blueprint_property(
                blueprint_path=character_result.get('blueprint_path'),
                property_name="Health",
                property_value="100",
                property_type="int"
            )

            if health_result.get("success"):
                print(f"   ✅ Character health set to 100")

        # 6. Create a UI Widget
        print("\n6️⃣ Creating UserWidget blueprint...")
        widget_result = await client.create_blueprint(
            name="BasicUI",
            parent_class="UserWidget",
            asset_path="/Game/UI/"
        )

        if widget_result.get("success"):
            print(f"   ✅ UI widget created: {widget_result.get('blueprint_path')}")

        # 7. Test Unreal connection
        print("\n7️⃣ Testing Unreal Engine connection...")
        connection_test = await client.test_connection()

        if connection_test.get("success"):
            print(f"   ✅ Connection successful (Response time: {connection_test.get('response_time_seconds', 'N/A')}s)")
        else:
            print(f"   ⚠️ Connection test result: {connection_test.get('message', 'Unknown')}")

        print("\n🎉 Basic operations completed successfully!")
        print("\nNext steps:")
        print("1. Open Unreal Editor")
        print("2. Check Content Browser for created blueprints:")
        print("   - /Game/Blueprints/BasicActor")
        print("   - /Game/Blueprints/BasicCharacter")
        print("   - /Game/UI/BasicUI")
        print("3. Open blueprints to verify properties were set correctly")

    except Exception as e:
        print(f"\n❌ Error during operations: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure MCP server is running: fastmcp dev unreal_blueprint_mcp_server.py")
        print("2. Check if Unreal Editor is running with plugin enabled")
        print("3. Verify MCP Status window is open in Unreal Editor")

async def quick_test():
    """Quick test to verify everything is working"""
    print("🔧 Quick Connection Test")
    print("-" * 30)

    client = UnrealBlueprintMCPClient()

    try:
        # Simple server status check
        status = await client.get_server_status()
        print(f"✅ MCP Server: {status.get('server_name')} v{status.get('version')}")

        # Quick blueprint creation test
        result = await client.create_test_actor("QuickTestActor")
        if result.get("success"):
            print(f"✅ Test blueprint created successfully")
        else:
            print(f"⚠️ Test blueprint creation returned: {result}")

    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Run full basic operations demo")
    print("2. Run quick connection test")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(basic_blueprint_operations())
    elif choice == "2":
        asyncio.run(quick_test())
    else:
        print("Invalid choice. Running quick test...")
        asyncio.run(quick_test())