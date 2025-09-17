#!/usr/bin/env python3
"""
FPS Template Generator

Complete First Person Shooter game template with weapons, enemies, and combat systems.
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

class FPSTemplate:
    """FPS game template generator"""

    def __init__(self, project_name: str, features: Dict[str, Any] = None, custom_settings: Dict[str, Any] = None):
        self.project_name = project_name
        self.features = features or {}
        self.custom_settings = custom_settings or {}
        self.mcp_server_url = MCP_SERVER_URL

        # Default FPS configuration
        self.default_config = {
            "weapons": ["Pistol", "AssaultRifle"],
            "enemies": ["BasicSoldier", "Scout"],
            "player_health": 100,
            "player_speed": 600,
            "multiplayer": False,
            "vehicles": False,
            "destructibles": True
        }

        # Merge with provided features
        self.config = {**self.default_config, **self.features}

    async def generate_project(self) -> Dict[str, Any]:
        """Generate complete FPS project"""
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

            await self._create_weapon_system()
            result["summary"]["blueprints_created"] += len(self.config.get("weapons", []))

            await self._create_enemy_system()
            result["summary"]["blueprints_created"] += len(self.config.get("enemies", []))

            await self._create_game_mode()
            result["summary"]["blueprints_created"] += 1

            await self._create_ui_system()
            result["summary"]["blueprints_created"] += 3  # HUD, Menu, Inventory

            # Optional features
            if self.config.get("multiplayer"):
                await self._create_multiplayer_system()
                result["summary"]["blueprints_created"] += 2

            if self.config.get("vehicles"):
                await self._create_vehicle_system()
                result["summary"]["blueprints_created"] += 1

            if self.config.get("destructibles"):
                await self._create_destructible_system()
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
        """Create FPS player character"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create player character blueprint
            request = {
                "jsonrpc": "2.0",
                "id": "create_fps_player",
                "method": "tools/call",
                "params": {
                    "name": "create_blueprint",
                    "arguments": {
                        "blueprint_name": f"{self.project_name}_Player",
                        "parent_class": "Character",
                        "asset_path": "/Game/Blueprints/Characters/"
                    }
                }
            }

            await ws.send(json.dumps(request))
            await ws.recv()

            # Add FPS-specific components
            fps_components = [
                "CameraComponent",
                "SkeletalMeshComponent",
                "MovementComponent",
                "HealthComponent",
                "WeaponManagerComponent"
            ]

            for component in fps_components:
                await self._add_component(ws, f"{self.project_name}_Player", component)

            # Set FPS properties
            properties = {
                "MaxHealth": self.config.get("player_health", 100),
                "WalkSpeed": self.config.get("player_speed", 600),
                "JumpZVelocity": 420.0,
                "MouseSensitivity": 1.0
            }

            for prop_name, prop_value in properties.items():
                await self._set_property(ws, f"{self.project_name}_Player", prop_name, prop_value)

    async def _create_weapon_system(self):
        """Create weapon system blueprints"""
        weapons = self.config.get("weapons", ["Pistol", "AssaultRifle"])

        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create base weapon class
            await self._create_blueprint(ws, f"{self.project_name}_WeaponBase", "Actor", "/Game/Blueprints/Weapons/")

            # Create specific weapons
            weapon_configs = {
                "Pistol": {"damage": 25, "fire_rate": 0.5, "ammo_capacity": 12},
                "AssaultRifle": {"damage": 30, "fire_rate": 0.1, "ammo_capacity": 30},
                "Shotgun": {"damage": 80, "fire_rate": 1.0, "ammo_capacity": 8},
                "SniperRifle": {"damage": 100, "fire_rate": 2.0, "ammo_capacity": 5}
            }

            for weapon in weapons:
                weapon_name = f"{self.project_name}_{weapon}"
                await self._create_blueprint(ws, weapon_name, f"{self.project_name}_WeaponBase", "/Game/Blueprints/Weapons/")

                # Set weapon-specific properties
                if weapon in weapon_configs:
                    config = weapon_configs[weapon]
                    for prop, value in config.items():
                        await self._set_property(ws, weapon_name, prop, value)

    async def _create_enemy_system(self):
        """Create enemy AI system"""
        enemies = self.config.get("enemies", ["BasicSoldier", "Scout"])

        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create base enemy class
            await self._create_blueprint(ws, f"{self.project_name}_EnemyBase", "Character", "/Game/Blueprints/Characters/")

            # Enemy configurations
            enemy_configs = {
                "BasicSoldier": {"health": 75, "speed": 300, "damage": 20},
                "HeavySoldier": {"health": 150, "speed": 200, "damage": 35},
                "Scout": {"health": 50, "speed": 500, "damage": 15},
                "Sniper": {"health": 60, "speed": 250, "damage": 50}
            }

            for enemy in enemies:
                enemy_name = f"{self.project_name}_{enemy}"
                await self._create_blueprint(ws, enemy_name, f"{self.project_name}_EnemyBase", "/Game/Blueprints/Characters/")

                # Add AI components
                ai_components = ["AIControllerComponent", "BehaviorTreeComponent", "BlackboardComponent"]
                for component in ai_components:
                    await self._add_component(ws, enemy_name, component)

                # Set enemy properties
                if enemy in enemy_configs:
                    config = enemy_configs[enemy]
                    for prop, value in config.items():
                        await self._set_property(ws, enemy_name, prop, value)

    async def _create_game_mode(self):
        """Create FPS game mode"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            game_mode_name = f"{self.project_name}_GameMode"
            await self._create_blueprint(ws, game_mode_name, "GameModeBase", "/Game/Blueprints/Gameplay/")

            # Set game mode properties
            properties = {
                "DefaultPlayerClass": f"{self.project_name}_Player",
                "SpawnPointClass": "PlayerStart",
                "MaxPlayers": 1 if not self.config.get("multiplayer") else 8,
                "GameTimeLimit": 600,  # 10 minutes
                "RespawnTime": 5
            }

            for prop, value in properties.items():
                await self._set_property(ws, game_mode_name, prop, value)

    async def _create_ui_system(self):
        """Create UI system blueprints"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create HUD
            hud_name = f"{self.project_name}_HUD"
            await self._create_blueprint(ws, hud_name, "HUD", "/Game/Blueprints/UI/")

            # Create Main Menu
            menu_name = f"{self.project_name}_MainMenu"
            await self._create_blueprint(ws, menu_name, "UserWidget", "/Game/Blueprints/UI/")

            # Create Pause Menu
            pause_menu_name = f"{self.project_name}_PauseMenu"
            await self._create_blueprint(ws, pause_menu_name, "UserWidget", "/Game/Blueprints/UI/")

    async def _create_multiplayer_system(self):
        """Create multiplayer system (if enabled)"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create multiplayer game mode
            mp_gamemode_name = f"{self.project_name}_MultiplayerGameMode"
            await self._create_blueprint(ws, mp_gamemode_name, "GameModeBase", "/Game/Blueprints/Multiplayer/")

            # Create network manager
            network_manager_name = f"{self.project_name}_NetworkManager"
            await self._create_blueprint(ws, network_manager_name, "ActorComponent", "/Game/Blueprints/Multiplayer/")

    async def _create_vehicle_system(self):
        """Create vehicle system (if enabled)"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            vehicle_name = f"{self.project_name}_Vehicle"
            await self._create_blueprint(ws, vehicle_name, "WheeledVehicle", "/Game/Blueprints/Vehicles/")

    async def _create_destructible_system(self):
        """Create destructible objects system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            destructible_name = f"{self.project_name}_DestructibleObject"
            await self._create_blueprint(ws, destructible_name, "Actor", "/Game/Blueprints/Destructibles/")

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