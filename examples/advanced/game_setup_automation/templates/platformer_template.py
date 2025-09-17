#!/usr/bin/env python3
"""
Platformer Template Generator

Complete 2D/3D Platformer game template with character controller, collectibles, and level mechanics.
"""

import asyncio
import json
import time
from typing import Dict, List, Any
import websockets
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import MCP_SERVER_URL

class PlatformerTemplate:
    """Platformer game template generator"""

    def __init__(self, project_name: str, features: Dict[str, Any] = None, custom_settings: Dict[str, Any] = None):
        self.project_name = project_name
        self.features = features or {}
        self.custom_settings = custom_settings or {}
        self.mcp_server_url = MCP_SERVER_URL

        # Default Platformer configuration
        self.default_config = {
            "abilities": ["DoubleJump"],
            "collectibles": ["Coins", "PowerUps"],
            "player_speed": 400,
            "jump_height": 600,
            "moving_platforms": True,
            "checkpoints": True,
            "time_trials": False
        }

        # Merge with provided features
        self.config = {**self.default_config, **self.features}

    async def generate_project(self) -> Dict[str, Any]:
        """Generate complete Platformer project"""
        start_time = time.time()

        try:
            result = {
                "success": True,
                "summary": {
                    "blueprints_created": 0,
                    "components_added": 0,
                    "assets_organized": 0
                }
            }

            # Generate core blueprints
            await self._create_player_character()
            result["summary"]["blueprints_created"] += 1

            await self._create_collectible_system()
            result["summary"]["blueprints_created"] += len(self.config.get("collectibles", []))

            await self._create_platform_system()
            result["summary"]["blueprints_created"] += 2

            await self._create_enemy_system()
            result["summary"]["blueprints_created"] += 2

            await self._create_level_mechanics()
            result["summary"]["blueprints_created"] += 3

            # Optional features
            if self.config.get("checkpoints"):
                await self._create_checkpoint_system()
                result["summary"]["blueprints_created"] += 1

            if self.config.get("time_trials"):
                await self._create_time_trial_system()
                result["summary"]["blueprints_created"] += 1

            # Calculate generation time
            generation_time = time.time() - start_time
            result["summary"]["generation_time"] = f"{generation_time:.2f} seconds"

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_player_character(self):
        """Create platformer player character"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create player character blueprint
            player_name = f"{self.project_name}_PlatformerPlayer"
            await self._create_blueprint(ws, player_name, "Character", "/Game/Blueprints/Characters/")

            # Add platformer-specific components
            components = [
                "CapsuleComponent",
                "SkeletalMeshComponent",
                "CharacterMovementComponent",
                "SpringArmComponent",
                "CameraComponent"
            ]

            for component in components:
                await self._add_component(ws, player_name, component)

            # Set platformer properties
            properties = {
                "MaxWalkSpeed": self.config.get("player_speed", 400),
                "JumpZVelocity": self.config.get("jump_height", 600),
                "AirControl": 0.8,
                "GravityScale": 1.5,
                "GroundFriction": 8.0
            }

            for prop_name, prop_value in properties.items():
                await self._set_property(ws, player_name, prop_name, prop_value)

            # Add special abilities
            abilities = self.config.get("abilities", [])
            if "DoubleJump" in abilities:
                await self._set_property(ws, player_name, "CanDoubleJump", True)
            if "WallJump" in abilities:
                await self._set_property(ws, player_name, "CanWallJump", True)
            if "Dash" in abilities:
                await self._set_property(ws, player_name, "CanDash", True)

    async def _create_collectible_system(self):
        """Create collectible items system"""
        collectibles = self.config.get("collectibles", ["Coins", "PowerUps"])

        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create base collectible class
            base_collectible = f"{self.project_name}_CollectibleBase"
            await self._create_blueprint(ws, base_collectible, "Actor", "/Game/Blueprints/Collectibles/")

            # Collectible configurations
            collectible_configs = {
                "Coins": {"value": 10, "effect": "score", "respawn": False},
                "Gems": {"value": 50, "effect": "score", "respawn": False},
                "PowerUps": {"value": 0, "effect": "power", "respawn": True},
                "Keys": {"value": 1, "effect": "unlock", "respawn": False}
            }

            for collectible in collectibles:
                collectible_name = f"{self.project_name}_{collectible}"
                await self._create_blueprint(ws, collectible_name, base_collectible, "/Game/Blueprints/Collectibles/")

                # Add collectible components
                await self._add_component(ws, collectible_name, "StaticMeshComponent")
                await self._add_component(ws, collectible_name, "SphereCollisionComponent")

                # Set collectible properties
                if collectible in collectible_configs:
                    config = collectible_configs[collectible]
                    for prop, value in config.items():
                        await self._set_property(ws, collectible_name, prop, value)

    async def _create_platform_system(self):
        """Create platform system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Static platform
            static_platform = f"{self.project_name}_StaticPlatform"
            await self._create_blueprint(ws, static_platform, "Actor", "/Game/Blueprints/Platforms/")
            await self._add_component(ws, static_platform, "StaticMeshComponent")
            await self._add_component(ws, static_platform, "BoxCollisionComponent")

            # Moving platform (if enabled)
            if self.config.get("moving_platforms"):
                moving_platform = f"{self.project_name}_MovingPlatform"
                await self._create_blueprint(ws, moving_platform, static_platform, "/Game/Blueprints/Platforms/")
                await self._add_component(ws, moving_platform, "MovementComponent")

                # Set movement properties
                await self._set_property(ws, moving_platform, "MovementSpeed", 200.0)
                await self._set_property(ws, moving_platform, "MovementPattern", "Linear")

    async def _create_enemy_system(self):
        """Create enemy system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Base enemy
            base_enemy = f"{self.project_name}_EnemyBase"
            await self._create_blueprint(ws, base_enemy, "Character", "/Game/Blueprints/Enemies/")

            # Patrol enemy
            patrol_enemy = f"{self.project_name}_PatrolEnemy"
            await self._create_blueprint(ws, patrol_enemy, base_enemy, "/Game/Blueprints/Enemies/")

            # Add enemy components
            enemy_components = ["AIControllerComponent", "PatrolComponent", "HealthComponent"]
            for component in enemy_components:
                await self._add_component(ws, patrol_enemy, component)

            # Set enemy properties
            properties = {
                "MaxHealth": 30,
                "MovementSpeed": 150,
                "PatrolDistance": 500,
                "DetectionRange": 300
            }

            for prop, value in properties.items():
                await self._set_property(ws, patrol_enemy, prop, value)

    async def _create_level_mechanics(self):
        """Create level mechanics"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Goal/Exit point
            goal = f"{self.project_name}_LevelGoal"
            await self._create_blueprint(ws, goal, "Actor", "/Game/Blueprints/Level/")
            await self._add_component(ws, goal, "StaticMeshComponent")
            await self._add_component(ws, goal, "BoxCollisionComponent")

            # Hazard/Spike
            hazard = f"{self.project_name}_Hazard"
            await self._create_blueprint(ws, hazard, "Actor", "/Game/Blueprints/Level/")
            await self._add_component(ws, hazard, "StaticMeshComponent")
            await self._add_component(ws, hazard, "BoxCollisionComponent")
            await self._set_property(ws, hazard, "Damage", 25)

            # Level manager
            level_manager = f"{self.project_name}_LevelManager"
            await self._create_blueprint(ws, level_manager, "ActorComponent", "/Game/Blueprints/Gameplay/")

    async def _create_checkpoint_system(self):
        """Create checkpoint system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            checkpoint = f"{self.project_name}_Checkpoint"
            await self._create_blueprint(ws, checkpoint, "Actor", "/Game/Blueprints/Gameplay/")

            # Add checkpoint components
            await self._add_component(ws, checkpoint, "StaticMeshComponent")
            await self._add_component(ws, checkpoint, "SphereCollisionComponent")

            # Set checkpoint properties
            await self._set_property(ws, checkpoint, "IsActive", False)
            await self._set_property(ws, checkpoint, "RespawnPoint", True)

    async def _create_time_trial_system(self):
        """Create time trial system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            time_trial = f"{self.project_name}_TimeTrialManager"
            await self._create_blueprint(ws, time_trial, "ActorComponent", "/Game/Blueprints/Gameplay/")

            # Set time trial properties
            await self._set_property(ws, time_trial, "TimeLimit", 120)  # 2 minutes
            await self._set_property(ws, time_trial, "BestTime", 0)
            await self._set_property(ws, time_trial, "ShowTimer", True)

    # Helper methods (same as FPS template)
    async def _create_blueprint(self, ws, name: str, parent_class: str, asset_path: str):
        """Helper method to create a blueprint"""
        request = {
            "jsonrpc": "2.0",
            "id": f"create_{name}",
            "method": "tools/call",
            "params": {
                "name": "create_blueprint",
                "arguments": {
                    "blueprint_name": name,
                    "parent_class": parent_class,
                    "asset_path": asset_path
                }
            }
        }

        await ws.send(json.dumps(request))
        await ws.recv()

    async def _add_component(self, ws, blueprint_name: str, component_type: str):
        """Helper method to add a component"""
        request = {
            "jsonrpc": "2.0",
            "id": f"add_component_{blueprint_name}",
            "method": "tools/call",
            "params": {
                "name": "add_component",
                "arguments": {
                    "blueprint_name": blueprint_name,
                    "component_type": component_type,
                    "component_name": f"{component_type}_Component"
                }
            }
        }

        await ws.send(json.dumps(request))
        await ws.recv()

    async def _set_property(self, ws, blueprint_name: str, property_name: str, property_value):
        """Helper method to set a property"""
        request = {
            "jsonrpc": "2.0",
            "id": f"set_property_{blueprint_name}",
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

        await ws.send(json.dumps(request))
        await ws.recv()