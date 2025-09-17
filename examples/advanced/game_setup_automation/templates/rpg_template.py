#!/usr/bin/env python3
"""
RPG Template Generator

Complete Role Playing Game template with character stats, inventory, NPCs, and quest systems.
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

class RPGTemplate:
    """RPG game template generator"""

    def __init__(self, project_name: str, features: Dict[str, Any] = None, custom_settings: Dict[str, Any] = None):
        self.project_name = project_name
        self.features = features or {}
        self.custom_settings = custom_settings or {}
        self.mcp_server_url = MCP_SERVER_URL

        # Default RPG configuration
        self.default_config = {
            "classes": ["Warrior", "Mage"],
            "skill_trees": True,
            "magic_system": True,
            "crafting": False,
            "dialogue_system": True,
            "quest_journal": True,
            "branching_dialogue": False
        }

        # Merge with provided features
        self.config = {**self.default_config, **self.features}

    async def generate_project(self) -> Dict[str, Any]:
        """Generate complete RPG project"""
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
            await self._create_character_system()
            result["summary"]["blueprints_created"] += len(self.config.get("classes", [])) + 1

            await self._create_inventory_system()
            result["summary"]["blueprints_created"] += 3

            await self._create_npc_system()
            result["summary"]["blueprints_created"] += 2

            await self._create_combat_system()
            result["summary"]["blueprints_created"] += 2

            # Optional features
            if self.config.get("skill_trees"):
                await self._create_skill_tree_system()
                result["summary"]["blueprints_created"] += 1

            if self.config.get("magic_system"):
                await self._create_magic_system()
                result["summary"]["blueprints_created"] += 2

            if self.config.get("dialogue_system"):
                await self._create_dialogue_system()
                result["summary"]["blueprints_created"] += 1

            if self.config.get("quest_journal"):
                await self._create_quest_system()
                result["summary"]["blueprints_created"] += 2

            if self.config.get("crafting"):
                await self._create_crafting_system()
                result["summary"]["blueprints_created"] += 2

            # Calculate generation time
            generation_time = time.time() - start_time
            result["summary"]["generation_time"] = f"{generation_time:.2f} seconds"

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_character_system(self):
        """Create RPG character system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Create base character class
            base_character = f"{self.project_name}_RPGCharacterBase"
            await self._create_blueprint(ws, base_character, "Character", "/Game/Blueprints/Characters/")

            # Add RPG components
            rpg_components = [
                "StatsComponent",
                "InventoryComponent",
                "ExperienceComponent",
                "SkillComponent",
                "EquipmentComponent"
            ]

            for component in rpg_components:
                await self._add_component(ws, base_character, component)

            # Set base properties
            base_properties = {
                "Level": 1,
                "Experience": 0,
                "Health": 100,
                "Mana": 50,
                "Strength": 10,
                "Intelligence": 10,
                "Dexterity": 10,
                "Constitution": 10
            }

            for prop, value in base_properties.items():
                await self._set_property(ws, base_character, prop, value)

            # Create character classes
            classes = self.config.get("classes", ["Warrior", "Mage"])
            class_configs = {
                "Warrior": {
                    "Health": 150, "Mana": 25, "Strength": 15, "Constitution": 14,
                    "Intelligence": 8, "Dexterity": 10
                },
                "Mage": {
                    "Health": 80, "Mana": 100, "Strength": 8, "Constitution": 9,
                    "Intelligence": 15, "Dexterity": 12
                },
                "Rogue": {
                    "Health": 100, "Mana": 40, "Strength": 11, "Constitution": 10,
                    "Intelligence": 12, "Dexterity": 16
                },
                "Archer": {
                    "Health": 110, "Mana": 35, "Strength": 12, "Constitution": 11,
                    "Intelligence": 10, "Dexterity": 15
                }
            }

            for char_class in classes:
                class_name = f"{self.project_name}_{char_class}"
                await self._create_blueprint(ws, class_name, base_character, "/Game/Blueprints/Characters/")

                if char_class in class_configs:
                    config = class_configs[char_class]
                    for prop, value in config.items():
                        await self._set_property(ws, class_name, prop, value)

    async def _create_inventory_system(self):
        """Create inventory system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Inventory manager
            inventory_manager = f"{self.project_name}_InventoryManager"
            await self._create_blueprint(ws, inventory_manager, "ActorComponent", "/Game/Blueprints/Inventory/")

            # Item base class
            item_base = f"{self.project_name}_ItemBase"
            await self._create_blueprint(ws, item_base, "Actor", "/Game/Blueprints/Items/")

            # Equipment system
            equipment_manager = f"{self.project_name}_EquipmentManager"
            await self._create_blueprint(ws, equipment_manager, "ActorComponent", "/Game/Blueprints/Equipment/")

            # Set inventory properties
            await self._set_property(ws, inventory_manager, "MaxSlots", 30)
            await self._set_property(ws, inventory_manager, "StackSize", 99)

    async def _create_npc_system(self):
        """Create NPC system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Base NPC
            npc_base = f"{self.project_name}_NPCBase"
            await self._create_blueprint(ws, npc_base, "Character", "/Game/Blueprints/NPCs/")

            # Add NPC components
            npc_components = ["DialogueComponent", "QuestGiverComponent", "TradeComponent"]
            for component in npc_components:
                await self._add_component(ws, npc_base, component)

            # Merchant NPC
            merchant = f"{self.project_name}_Merchant"
            await self._create_blueprint(ws, merchant, npc_base, "/Game/Blueprints/NPCs/")
            await self._set_property(ws, merchant, "CanTrade", True)
            await self._set_property(ws, merchant, "ShopInventorySize", 20)

    async def _create_combat_system(self):
        """Create combat system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Combat manager
            combat_manager = f"{self.project_name}_CombatManager"
            await self._create_blueprint(ws, combat_manager, "ActorComponent", "/Game/Blueprints/Combat/")

            # Damage calculator
            damage_calculator = f"{self.project_name}_DamageCalculator"
            await self._create_blueprint(ws, damage_calculator, "ActorComponent", "/Game/Blueprints/Combat/")

            # Set combat properties
            await self._set_property(ws, combat_manager, "TurnBased", False)
            await self._set_property(ws, combat_manager, "CriticalChance", 0.05)

    async def _create_skill_tree_system(self):
        """Create skill tree system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            skill_tree = f"{self.project_name}_SkillTree"
            await self._create_blueprint(ws, skill_tree, "ActorComponent", "/Game/Blueprints/Skills/")

            await self._set_property(ws, skill_tree, "MaxSkillPoints", 100)
            await self._set_property(ws, skill_tree, "SkillsPerLevel", 2)

    async def _create_magic_system(self):
        """Create magic system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Spell manager
            spell_manager = f"{self.project_name}_SpellManager"
            await self._create_blueprint(ws, spell_manager, "ActorComponent", "/Game/Blueprints/Magic/")

            # Spell base class
            spell_base = f"{self.project_name}_SpellBase"
            await self._create_blueprint(ws, spell_base, "Actor", "/Game/Blueprints/Magic/")

            await self._add_component(ws, spell_base, "ParticleSystemComponent")
            await self._set_property(ws, spell_base, "ManaCost", 10)
            await self._set_property(ws, spell_base, "CastTime", 1.0)

    async def _create_dialogue_system(self):
        """Create dialogue system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            dialogue_manager = f"{self.project_name}_DialogueManager"
            await self._create_blueprint(ws, dialogue_manager, "ActorComponent", "/Game/Blueprints/Dialogue/")

            branching = self.config.get("branching_dialogue", False)
            await self._set_property(ws, dialogue_manager, "SupportsBranching", branching)
            await self._set_property(ws, dialogue_manager, "AutoAdvance", False)

    async def _create_quest_system(self):
        """Create quest system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Quest manager
            quest_manager = f"{self.project_name}_QuestManager"
            await self._create_blueprint(ws, quest_manager, "ActorComponent", "/Game/Blueprints/Quests/")

            # Quest base class
            quest_base = f"{self.project_name}_QuestBase"
            await self._create_blueprint(ws, quest_base, "ActorComponent", "/Game/Blueprints/Quests/")

            await self._set_property(ws, quest_manager, "MaxActiveQuests", 10)
            await self._set_property(ws, quest_base, "ExperienceReward", 100)

    async def _create_crafting_system(self):
        """Create crafting system"""
        async with websockets.connect(self.mcp_server_url, timeout=30) as ws:
            # Crafting manager
            crafting_manager = f"{self.project_name}_CraftingManager"
            await self._create_blueprint(ws, crafting_manager, "ActorComponent", "/Game/Blueprints/Crafting/")

            # Recipe system
            recipe_manager = f"{self.project_name}_RecipeManager"
            await self._create_blueprint(ws, recipe_manager, "ActorComponent", "/Game/Blueprints/Crafting/")

            await self._set_property(ws, crafting_manager, "MaxRecipes", 50)

    # Helper methods (same as other templates)
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