#!/usr/bin/env python3
"""
Bulk Blueprint Creator

Demonstrates efficient batch creation of multiple blueprints
with parallel processing, progress tracking, and error handling.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import MCP_SERVER_URL, DEFAULT_BATCH_SIZE, MAX_CONCURRENT_OPERATIONS

import websockets

@dataclass
class BlueprintSpec:
    """Specification for creating a blueprint"""
    name: str
    parent_class: str
    asset_path: str
    properties: Dict[str, Any] = None
    components: List[str] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.components is None:
            self.components = []

@dataclass
class BatchResult:
    """Result of a batch operation"""
    total_requested: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]
    execution_time: float
    created_blueprints: List[str]

class BatchBlueprintCreator:
    """Handles bulk blueprint creation with advanced features"""

    def __init__(self, server_url: str = MCP_SERVER_URL, batch_size: int = DEFAULT_BATCH_SIZE):
        self.server_url = server_url
        self.batch_size = batch_size
        self.max_concurrent = MAX_CONCURRENT_OPERATIONS

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def create_single_blueprint(self, spec: BlueprintSpec) -> Dict[str, Any]:
        """Create a single blueprint"""
        try:
            async with websockets.connect(self.server_url, timeout=10) as websocket:
                request = {
                    "jsonrpc": "2.0",
                    "id": f"create_{spec.name}_{int(time.time())}",
                    "method": "tools/call",
                    "params": {
                        "name": "create_blueprint",
                        "arguments": {
                            "blueprint_name": spec.name,
                            "parent_class": spec.parent_class,
                            "asset_path": spec.asset_path
                        }
                    }
                }

                await websocket.send(json.dumps(request))
                response = await websocket.recv()
                result = json.loads(response)

                if "error" in result:
                    return {"success": False, "error": result["error"], "blueprint": spec.name}

                # Add components if specified
                if spec.components:
                    for component in spec.components:
                        await self._add_component(websocket, spec.name, component)

                # Set properties if specified
                if spec.properties:
                    for prop_name, prop_value in spec.properties.items():
                        await self._set_property(websocket, spec.name, prop_name, prop_value)

                return {"success": True, "blueprint": spec.name, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e), "blueprint": spec.name}

    async def _add_component(self, websocket, blueprint_name: str, component_type: str):
        """Add a component to a blueprint"""
        request = {
            "jsonrpc": "2.0",
            "id": f"add_component_{blueprint_name}_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "add_component",
                "arguments": {
                    "blueprint_name": blueprint_name,
                    "component_type": component_type,
                    "component_name": f"{component_type}Component"
                }
            }
        }
        await websocket.send(json.dumps(request))
        await websocket.recv()  # Consume response

    async def _set_property(self, websocket, blueprint_name: str, property_name: str, property_value: Any):
        """Set a property on a blueprint"""
        request = {
            "jsonrpc": "2.0",
            "id": f"set_property_{blueprint_name}_{int(time.time())}",
            "method": "tools/call",
            "params": {
                "name": "set_property",
                "arguments": {
                    "blueprint_name": blueprint_name,
                    "property_name": property_name,
                    "property_value": property_value
                }
            }
        }
        await websocket.send(json.dumps(request))
        await websocket.recv()  # Consume response

    async def create_batch(
        self,
        blueprints: List[BlueprintSpec],
        progress_callback: Optional[Callable[[float], None]] = None,
        max_retries: int = 3
    ) -> BatchResult:
        """Create multiple blueprints in batches with progress tracking"""

        start_time = time.time()
        total_blueprints = len(blueprints)
        successful = 0
        failed = 0
        errors = []
        created_blueprints = []

        self.logger.info(f"Starting batch creation of {total_blueprints} blueprints")

        # Process in batches
        for i in range(0, total_blueprints, self.batch_size):
            batch = blueprints[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}/{(total_blueprints + self.batch_size - 1)//self.batch_size}")

            # Create semaphore to limit concurrent operations
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def create_with_semaphore(spec: BlueprintSpec):
                async with semaphore:
                    return await self.create_single_blueprint(spec)

            # Execute batch with controlled concurrency
            batch_tasks = [create_with_semaphore(spec) for spec in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    errors.append({"error": str(result), "blueprint": "unknown"})
                elif result["success"]:
                    successful += 1
                    created_blueprints.append(result["blueprint"])
                else:
                    failed += 1
                    errors.append(result)

            # Update progress
            if progress_callback:
                progress = ((i + len(batch)) / total_blueprints) * 100
                progress_callback(progress)

            # Small delay between batches to avoid overwhelming the server
            await asyncio.sleep(0.1)

        execution_time = time.time() - start_time

        result = BatchResult(
            total_requested=total_blueprints,
            successful=successful,
            failed=failed,
            errors=errors,
            execution_time=execution_time,
            created_blueprints=created_blueprints
        )

        self.logger.info(f"Batch creation completed: {successful}/{total_blueprints} successful in {execution_time:.2f}s")
        return result

    def generate_character_blueprints(self, count: int, base_name: str = "Character") -> List[BlueprintSpec]:
        """Generate a list of character blueprint specifications"""
        blueprints = []
        for i in range(count):
            spec = BlueprintSpec(
                name=f"{base_name}{i+1:03d}",
                parent_class="Character",
                asset_path="/Game/Blueprints/Characters/",
                components=["SkeletalMeshComponent", "MovementComponent"],
                properties={
                    "MaxHealth": 100.0,
                    "Speed": 600.0,
                    "JumpHeight": 420.0
                }
            )
            blueprints.append(spec)
        return blueprints

    def generate_weapon_blueprints(self, count: int, base_name: str = "Weapon") -> List[BlueprintSpec]:
        """Generate a list of weapon blueprint specifications"""
        blueprints = []
        for i in range(count):
            spec = BlueprintSpec(
                name=f"{base_name}{i+1:03d}",
                parent_class="Actor",
                asset_path="/Game/Blueprints/Weapons/",
                components=["StaticMeshComponent", "CollisionComponent"],
                properties={
                    "Damage": 25.0 + (i * 5),
                    "Range": 1000.0,
                    "FireRate": 0.5
                }
            )
            blueprints.append(spec)
        return blueprints

    def generate_item_blueprints(self, count: int, base_name: str = "Item") -> List[BlueprintSpec]:
        """Generate a list of item blueprint specifications"""
        blueprints = []
        for i in range(count):
            spec = BlueprintSpec(
                name=f"{base_name}{i+1:03d}",
                parent_class="Actor",
                asset_path="/Game/Blueprints/Items/",
                components=["StaticMeshComponent"],
                properties={
                    "Value": 10 * (i + 1),
                    "Stackable": True,
                    "MaxStack": 99
                }
            )
            blueprints.append(spec)
        return blueprints

async def main():
    """Example usage of the BatchBlueprintCreator"""
    import argparse

    parser = argparse.ArgumentParser(description="Bulk Blueprint Creator")
    parser.add_argument("--count", type=int, default=5, help="Number of blueprints to create")
    parser.add_argument("--type", choices=["character", "weapon", "item"], default="character", help="Type of blueprints")
    parser.add_argument("--name", default=None, help="Base name for blueprints")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size")
    parser.add_argument("--concurrent", type=int, default=MAX_CONCURRENT_OPERATIONS, help="Max concurrent operations")

    args = parser.parse_args()

    creator = BatchBlueprintCreator(batch_size=args.batch_size)
    creator.max_concurrent = args.concurrent

    # Generate blueprints based on type
    if args.type == "character":
        blueprints = creator.generate_character_blueprints(args.count, args.name or "Character")
    elif args.type == "weapon":
        blueprints = creator.generate_weapon_blueprints(args.count, args.name or "Weapon")
    elif args.type == "item":
        blueprints = creator.generate_item_blueprints(args.count, args.name or "Item")

    # Progress callback
    def progress_callback(progress: float):
        print(f"Progress: {progress:.1f}%")

    try:
        result = await creator.create_batch(blueprints, progress_callback)

        print(f"\n{'='*60}")
        print(f"Batch Creation Results")
        print(f"{'='*60}")
        print(f"Total Requested: {result.total_requested}")
        print(f"Successful: {result.successful}")
        print(f"Failed: {result.failed}")
        print(f"Execution Time: {result.execution_time:.2f} seconds")
        print(f"Success Rate: {(result.successful/result.total_requested)*100:.1f}%")

        if result.created_blueprints:
            print(f"\nCreated Blueprints:")
            for blueprint in result.created_blueprints:
                print(f"  - {blueprint}")

        if result.errors:
            print(f"\nErrors:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error.get('blueprint', 'unknown')}: {error.get('error', 'unknown error')}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")

    except Exception as e:
        print(f"Batch creation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())