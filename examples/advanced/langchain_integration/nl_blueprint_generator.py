#!/usr/bin/env python3
"""
Natural Language Blueprint Generator

Uses LangChain and OpenAI to convert natural language descriptions
into Unreal Engine blueprints with intelligent component selection.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, LANGCHAIN_MODEL, MAX_TOKENS, MCP_SERVER_URL

try:
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain.schema import BaseOutputParser
    from langchain.output_parsers import PydanticOutputParser
    from pydantic import BaseModel, Field
except ImportError:
    print("LangChain not installed. Run: pip install langchain openai")
    sys.exit(1)

import websockets

@dataclass
class ComponentSpec:
    """Specification for a blueprint component"""
    type: str
    name: str
    properties: Dict[str, Any]

class BlueprintSpecification(BaseModel):
    """Pydantic model for blueprint specification"""
    name: str = Field(description="Name of the blueprint")
    parent_class: str = Field(description="Parent class for the blueprint")
    description: str = Field(description="Description of what this blueprint does")
    components: List[Dict[str, Any]] = Field(description="List of components to add")
    properties: Dict[str, Any] = Field(description="Properties to set on the blueprint")
    asset_path: str = Field(description="Asset path where blueprint should be created")

class NLBlueprintGenerator:
    """Generates blueprints from natural language descriptions"""

    def __init__(self, api_key: str = None, model: str = LANGCHAIN_MODEL):
        # Use provided key or get from environment
        self.api_key = api_key or OPENAI_API_KEY

        # Validate API key
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide api_key parameter."
            )

        # Basic security validation
        if not self.api_key.startswith('sk-') or len(self.api_key) < 20:
            raise ValueError(
                "Invalid OpenAI API key format. Key should start with 'sk-' and be at least 20 characters long."
            )
        self.model = model
        self.mcp_server_url = MCP_SERVER_URL

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize LangChain components
        self._setup_langchain()

    def _setup_langchain(self):
        """Setup LangChain components"""
        # Initialize chat model
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model,
            temperature=0.7,
            max_tokens=MAX_TOKENS
        )

        # Setup output parser
        self.output_parser = PydanticOutputParser(pydantic_object=BlueprintSpecification)

        # Create prompt template
        system_template = """
You are an expert Unreal Engine blueprint developer with deep knowledge of:
- Unreal Engine component architecture and best practices
- Performance optimization techniques for game development
- Blueprint visual scripting patterns and conventions
- Component relationships and dependencies
- Proper asset organization and naming conventions

When creating blueprint specifications from descriptions, always consider:
1. Performance implications of component choices
2. Maintainability and modularity of the design
3. Unreal Engine naming conventions and best practices
4. Component relationships and proper initialization order
5. Memory efficiency and runtime performance

Common Unreal Engine components you can use:
- StaticMeshComponent: For static 3D models
- SkeletalMeshComponent: For animated characters and objects
- CollisionComponent: For collision detection
- MovementComponent: For character/object movement
- AudioComponent: For sound effects and music
- ParticleSystemComponent: For visual effects
- LightComponent: For lighting
- CameraComponent: For viewpoints
- SceneComponent: For spatial hierarchy
- ActorComponent: For custom logic components

Common parent classes:
- Actor: Base class for objects that can be placed in the world
- Pawn: Can be possessed by controllers (AI or player)
- Character: Inherits from Pawn, has movement capabilities
- PlayerController: Controls pawns for players
- GameMode: Defines game rules and flow
- ActorComponent: For reusable functionality
- SceneComponent: For components with transform

Asset path conventions:
- Characters: /Game/Blueprints/Characters/
- Weapons: /Game/Blueprints/Weapons/
- Items: /Game/Blueprints/Items/
- UI: /Game/Blueprints/UI/
- Gameplay: /Game/Blueprints/Gameplay/
- Effects: /Game/Blueprints/Effects/

{format_instructions}
"""

        human_template = """
Based on this description, create a detailed blueprint specification:

Description: {description}

Additional context (if any): {context}

Please provide a complete blueprint specification that follows Unreal Engine best practices.
"""

        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

    async def generate_from_description(
        self,
        description: str,
        context: str = "",
        validate: bool = True
    ) -> Dict[str, Any]:
        """Generate a blueprint specification from natural language description"""

        self.logger.info(f"Generating blueprint from description: {description}")

        try:
            # Format the prompt
            formatted_prompt = self.prompt.format_prompt(
                description=description,
                context=context,
                format_instructions=self.output_parser.get_format_instructions()
            )

            # Generate response
            response = await asyncio.to_thread(
                self.llm.predict,
                formatted_prompt.to_string()
            )

            # Parse the response
            blueprint_spec = self.output_parser.parse(response)

            self.logger.info(f"Generated blueprint specification for: {blueprint_spec.name}")

            # Validate the specification if requested
            if validate:
                validation_result = await self._validate_specification(blueprint_spec)
                if not validation_result["valid"]:
                    self.logger.warning(f"Validation issues found: {validation_result['issues']}")

            # Convert to dictionary for easier handling
            result = {
                "specification": blueprint_spec.dict(),
                "original_description": description,
                "context": context,
                "model_used": self.model
            }

            return result

        except Exception as e:
            self.logger.error(f"Error generating blueprint: {e}")
            return {"error": str(e), "description": description}

    async def _validate_specification(self, spec: BlueprintSpecification) -> Dict[str, Any]:
        """Validate a blueprint specification"""
        issues = []

        # Check naming conventions
        if not spec.name.replace("_", "").replace("-", "").isalnum():
            issues.append("Blueprint name should only contain alphanumeric characters, underscores, and hyphens")

        # Check parent class validity
        valid_parents = [
            "Actor", "Pawn", "Character", "PlayerController", "GameMode",
            "ActorComponent", "SceneComponent", "StaticMeshActor"
        ]
        if spec.parent_class not in valid_parents:
            issues.append(f"Unusual parent class: {spec.parent_class}")

        # Check asset path format
        if not spec.asset_path.startswith("/Game/"):
            issues.append("Asset path should start with /Game/")

        # Check component specifications
        for component in spec.components:
            if "type" not in component:
                issues.append("Component missing 'type' field")
            if "name" not in component:
                issues.append("Component missing 'name' field")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    async def create_blueprint_from_spec(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """Create an actual blueprint from a specification using MCP"""

        try:
            spec = specification["specification"]

            async with websockets.connect(self.mcp_server_url, timeout=30) as websocket:
                # Create the blueprint
                create_request = {
                    "jsonrpc": "2.0",
                    "id": f"create_{spec['name']}",
                    "method": "tools/call",
                    "params": {
                        "name": "create_blueprint",
                        "arguments": {
                            "blueprint_name": spec["name"],
                            "parent_class": spec["parent_class"],
                            "asset_path": spec["asset_path"]
                        }
                    }
                }

                await websocket.send(json.dumps(create_request))
                response = await websocket.recv()
                result = json.loads(response)

                if "error" in result:
                    return {"success": False, "error": result["error"]}

                # Add components
                for component in spec.get("components", []):
                    await self._add_component_to_blueprint(
                        websocket,
                        spec["name"],
                        component
                    )

                # Set properties
                for prop_name, prop_value in spec.get("properties", {}).items():
                    await self._set_blueprint_property(
                        websocket,
                        spec["name"],
                        prop_name,
                        prop_value
                    )

                return {
                    "success": True,
                    "blueprint_name": spec["name"],
                    "asset_path": spec["asset_path"],
                    "components_added": len(spec.get("components", [])),
                    "properties_set": len(spec.get("properties", {}))
                }

        except Exception as e:
            self.logger.error(f"Error creating blueprint: {e}")
            return {"success": False, "error": str(e)}

    async def _add_component_to_blueprint(self, websocket, blueprint_name: str, component: Dict[str, Any]):
        """Add a component to a blueprint"""
        request = {
            "jsonrpc": "2.0",
            "id": f"add_component_{blueprint_name}",
            "method": "tools/call",
            "params": {
                "name": "add_component",
                "arguments": {
                    "blueprint_name": blueprint_name,
                    "component_type": component["type"],
                    "component_name": component["name"]
                }
            }
        }
        await websocket.send(json.dumps(request))
        await websocket.recv()

    async def _set_blueprint_property(self, websocket, blueprint_name: str, prop_name: str, prop_value: Any):
        """Set a property on a blueprint"""
        request = {
            "jsonrpc": "2.0",
            "id": f"set_property_{blueprint_name}",
            "method": "tools/call",
            "params": {
                "name": "set_property",
                "arguments": {
                    "blueprint_name": blueprint_name,
                    "property_name": prop_name,
                    "property_value": prop_value
                }
            }
        }
        await websocket.send(json.dumps(request))
        await websocket.recv()

    async def generate_and_create(self, description: str, context: str = "") -> Dict[str, Any]:
        """Complete workflow: generate specification and create blueprint"""

        # Generate specification
        spec_result = await self.generate_from_description(description, context)

        if "error" in spec_result:
            return spec_result

        # Create the blueprint
        creation_result = await self.create_blueprint_from_spec(spec_result)

        return {
            "specification": spec_result,
            "creation": creation_result,
            "success": creation_result.get("success", False)
        }

async def main():
    """Example usage of the NL Blueprint Generator"""
    import argparse

    parser = argparse.ArgumentParser(description="Natural Language Blueprint Generator")
    parser.add_argument("--description", required=True, help="Description of the blueprint to create")
    parser.add_argument("--context", default="", help="Additional context for generation")
    parser.add_argument("--create", action="store_true", help="Actually create the blueprint in Unreal")
    parser.add_argument("--model", default=LANGCHAIN_MODEL, help="OpenAI model to use")

    args = parser.parse_args()

    generator = NLBlueprintGenerator(model=args.model)

    try:
        if args.create:
            # Generate and create
            result = await generator.generate_and_create(args.description, args.context)

            print(f"\n{'='*60}")
            print(f"Natural Language Blueprint Generation Results")
            print(f"{'='*60}")

            if result["success"]:
                spec = result["specification"]["specification"]
                creation = result["creation"]

                print(f"✅ Successfully created blueprint: {spec['name']}")
                print(f"📁 Asset Path: {spec['asset_path']}")
                print(f"🏗️ Parent Class: {spec['parent_class']}")
                print(f"⚙️ Components Added: {creation['components_added']}")
                print(f"🔧 Properties Set: {creation['properties_set']}")
                print(f"\n📝 Description: {spec['description']}")

                if spec.get("components"):
                    print(f"\n🔧 Components:")
                    for component in spec["components"]:
                        print(f"  - {component['name']} ({component['type']})")

                if spec.get("properties"):
                    print(f"\n⚙️ Properties:")
                    for prop_name, prop_value in spec["properties"].items():
                        print(f"  - {prop_name}: {prop_value}")

            else:
                print(f"❌ Failed to create blueprint")
                if "error" in result["specification"]:
                    print(f"Specification Error: {result['specification']['error']}")
                if "error" in result["creation"]:
                    print(f"Creation Error: {result['creation']['error']}")

        else:
            # Generate specification only
            result = await generator.generate_from_description(args.description, args.context)

            if "error" not in result:
                spec = result["specification"]
                print(f"\n{'='*60}")
                print(f"Generated Blueprint Specification")
                print(f"{'='*60}")
                print(json.dumps(spec, indent=2))
            else:
                print(f"Error: {result['error']}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())