#!/usr/bin/env python3
"""
Interactive Game Setup Wizard

Provides an interactive command-line interface for setting up
complete game projects using predefined templates.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import MCP_SERVER_URL, GAME_TEMPLATES, DEFAULT_ASSET_PATHS

# Import template classes
from templates.fps_template import FPSTemplate
from templates.platformer_template import PlatformerTemplate
from templates.rpg_template import RPGTemplate

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class GameSetupWizard:
    """Interactive wizard for game project setup"""

    def __init__(self):
        self.template_classes = {
            "fps": FPSTemplate,
            "platformer": PlatformerTemplate,
            "rpg": RPGTemplate
        }

        self.project_config = {
            "name": "",
            "template": "",
            "features": {},
            "custom_settings": {}
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def print_header(self, title: str):
        """Print colored header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title:^60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}\n")

    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.ENDC}")

    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

    def get_input(self, prompt: str, default: str = "") -> str:
        """Get user input with optional default"""
        if default:
            prompt += f" [{default}]"
        prompt += ": "

        user_input = input(f"{Colors.YELLOW}{prompt}{Colors.ENDC}").strip()
        return user_input if user_input else default

    def get_choice(self, prompt: str, choices: List[str], default: int = 0) -> str:
        """Get user choice from a list"""
        print(f"\n{Colors.YELLOW}{prompt}{Colors.ENDC}")

        for i, choice in enumerate(choices, 1):
            marker = "👉" if i == default + 1 else "  "
            print(f"{marker} {i}. {choice}")

        while True:
            try:
                choice_input = input(f"\n{Colors.YELLOW}Enter choice (1-{len(choices)}) [{default + 1}]: {Colors.ENDC}").strip()

                if not choice_input:
                    return choices[default]

                choice_num = int(choice_input)
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    self.print_error(f"Please enter a number between 1 and {len(choices)}")

            except ValueError:
                self.print_error("Please enter a valid number")

    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{Colors.YELLOW}{prompt} [{default_str}]: {Colors.ENDC}").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes', 'true', '1']

    async def run_wizard(self):
        """Run the interactive setup wizard"""
        try:
            self.print_header("🎮 UnrealBlueprintMCP Game Setup Wizard")

            # Welcome message
            print("Welcome to the Game Setup Wizard!")
            print("This tool will help you create a complete game project using predefined templates.")
            print("You can customize various aspects of your game during the setup process.\n")

            # Step 1: Project Information
            await self.collect_project_info()

            # Step 2: Template Selection
            await self.select_template()

            # Step 3: Feature Configuration
            await self.configure_features()

            # Step 4: Custom Settings
            await self.configure_custom_settings()

            # Step 5: Review Configuration
            await self.review_configuration()

            # Step 6: Generate Project
            if self.get_yes_no("Generate the project now?", True):
                await self.generate_project()
            else:
                await self.save_configuration()

        except KeyboardInterrupt:
            self.print_warning("\n\nWizard cancelled by user")
            sys.exit(0)
        except Exception as e:
            self.print_error(f"Wizard failed: {e}")
            sys.exit(1)

    async def collect_project_info(self):
        """Collect basic project information"""
        self.print_header("📋 Project Information")

        self.project_config["name"] = self.get_input(
            "Enter project name",
            "MyGameProject"
        )

        self.project_config["description"] = self.get_input(
            "Enter project description (optional)",
            f"A game project created with UnrealBlueprintMCP"
        )

        self.project_config["version"] = self.get_input(
            "Enter project version",
            "1.0.0"
        )

        # Target platforms
        platforms = ["Windows", "Mac", "Linux", "iOS", "Android"]
        selected_platforms = []

        self.print_info("Select target platforms (you can choose multiple):")
        for platform in platforms:
            if self.get_yes_no(f"Target {platform}?", platform in ["Windows", "Mac"]):
                selected_platforms.append(platform)

        self.project_config["target_platforms"] = selected_platforms

        self.print_success(f"Project '{self.project_config['name']}' configured for {len(selected_platforms)} platform(s)")

    async def select_template(self):
        """Select game template"""
        self.print_header("🎯 Template Selection")

        template_descriptions = {
            "fps": "First Person Shooter - Complete FPS framework with weapons, enemies, and combat",
            "platformer": "2D/3D Platformer - Character controller with jumping, collectibles, and enemies",
            "rpg": "Role Playing Game - Character stats, inventory, NPCs, and quest system",
            "custom": "Custom Template - Start with a minimal setup and configure everything manually"
        }

        template_names = list(template_descriptions.keys())
        template_choices = [f"{name.upper()}: {desc}" for name, desc in template_descriptions.items()]

        selected_template_desc = self.get_choice("Choose a game template:", template_choices, 0)
        selected_template = template_names[template_choices.index(selected_template_desc)]

        self.project_config["template"] = selected_template

        # Show template details
        if selected_template in GAME_TEMPLATES:
            template_info = GAME_TEMPLATES[selected_template]
            print(f"\n{Colors.GREEN}Template: {template_info['name']}{Colors.ENDC}")
            print(f"Blueprints: {', '.join(template_info['blueprints'])}")
            print(f"Components: {', '.join(template_info['required_components'])}")

        self.print_success(f"Selected template: {selected_template.upper()}")

    async def configure_features(self):
        """Configure template features"""
        self.print_header("⚙️ Feature Configuration")

        template = self.project_config["template"]

        if template == "fps":
            await self.configure_fps_features()
        elif template == "platformer":
            await self.configure_platformer_features()
        elif template == "rpg":
            await self.configure_rpg_features()
        elif template == "custom":
            await self.configure_custom_features()

    async def configure_fps_features(self):
        """Configure FPS template features"""
        features = {}

        # Weapon types
        weapon_types = ["Pistol", "AssaultRifle", "Shotgun", "SniperRifle", "RocketLauncher"]
        selected_weapons = []

        self.print_info("Select weapons to include:")
        for weapon in weapon_types:
            if self.get_yes_no(f"Include {weapon}?", weapon in ["Pistol", "AssaultRifle"]):
                selected_weapons.append(weapon)

        features["weapons"] = selected_weapons

        # Enemy types
        enemy_types = ["BasicSoldier", "HeavySoldier", "Scout", "Sniper"]
        selected_enemies = []

        self.print_info("Select enemy types:")
        for enemy in enemy_types:
            if self.get_yes_no(f"Include {enemy}?", enemy in ["BasicSoldier", "Scout"]):
                selected_enemies.append(enemy)

        features["enemies"] = selected_enemies

        # Additional features
        features["multiplayer"] = self.get_yes_no("Include multiplayer support?", False)
        features["vehicles"] = self.get_yes_no("Include vehicle system?", False)
        features["destructibles"] = self.get_yes_no("Include destructible objects?", True)

        self.project_config["features"] = features

    async def configure_platformer_features(self):
        """Configure Platformer template features"""
        features = {}

        # Character abilities
        abilities = ["DoubleJump", "WallJump", "Dash", "Glide"]
        selected_abilities = []

        self.print_info("Select character abilities:")
        for ability in abilities:
            if self.get_yes_no(f"Include {ability}?", ability in ["DoubleJump"]):
                selected_abilities.append(ability)

        features["abilities"] = selected_abilities

        # Collectibles
        collectible_types = ["Coins", "Gems", "PowerUps", "Keys"]
        selected_collectibles = []

        self.print_info("Select collectible types:")
        for collectible in collectible_types:
            if self.get_yes_no(f"Include {collectible}?", collectible in ["Coins", "PowerUps"]):
                selected_collectibles.append(collectible)

        features["collectibles"] = selected_collectibles

        # Level features
        features["moving_platforms"] = self.get_yes_no("Include moving platforms?", True)
        features["checkpoints"] = self.get_yes_no("Include checkpoint system?", True)
        features["time_trials"] = self.get_yes_no("Include time trial mode?", False)

        self.project_config["features"] = features

    async def configure_rpg_features(self):
        """Configure RPG template features"""
        features = {}

        # Character classes
        classes = ["Warrior", "Mage", "Rogue", "Archer"]
        selected_classes = []

        self.print_info("Select character classes:")
        for char_class in classes:
            if self.get_yes_no(f"Include {char_class}?", char_class in ["Warrior", "Mage"]):
                selected_classes.append(char_class)

        features["classes"] = selected_classes

        # Skills and magic
        features["skill_trees"] = self.get_yes_no("Include skill tree system?", True)
        features["magic_system"] = self.get_yes_no("Include magic/spell system?", True)
        features["crafting"] = self.get_yes_no("Include crafting system?", False)

        # Dialogue and quests
        features["dialogue_system"] = self.get_yes_no("Include NPC dialogue system?", True)
        features["quest_journal"] = self.get_yes_no("Include quest journal?", True)
        features["branching_dialogue"] = self.get_yes_no("Include branching dialogue trees?", False)

        self.project_config["features"] = features

    async def configure_custom_features(self):
        """Configure custom template features"""
        features = {}

        self.print_info("For custom templates, you can manually configure features after generation.")

        features["basic_character"] = self.get_yes_no("Include basic character controller?", True)
        features["basic_ui"] = self.get_yes_no("Include basic UI framework?", True)
        features["input_system"] = self.get_yes_no("Include input management system?", True)

        self.project_config["features"] = features

    async def configure_custom_settings(self):
        """Configure custom project settings"""
        self.print_header("🔧 Custom Settings")

        settings = {}

        # Asset paths
        if self.get_yes_no("Customize asset organization?", False):
            self.print_info("Configure asset paths (press Enter for defaults):")

            for category, default_path in DEFAULT_ASSET_PATHS.items():
                custom_path = self.get_input(f"{category.title()} path", default_path)
                settings[f"{category}_path"] = custom_path

        # Performance settings
        if self.get_yes_no("Configure performance settings?", False):
            quality_levels = ["Low", "Medium", "High", "Ultra"]
            quality = self.get_choice("Select default quality level:", quality_levels, 1)
            settings["default_quality"] = quality

            settings["enable_lod"] = self.get_yes_no("Enable Level of Detail (LOD) system?", True)
            settings["enable_occlusion"] = self.get_yes_no("Enable occlusion culling?", True)

        # Development settings
        if self.get_yes_no("Configure development settings?", False):
            settings["enable_debugging"] = self.get_yes_no("Enable debug features?", True)
            settings["enable_profiling"] = self.get_yes_no("Enable performance profiling?", False)
            settings["auto_compile"] = self.get_yes_no("Enable auto-compilation?", True)

        self.project_config["custom_settings"] = settings

    async def review_configuration(self):
        """Review and confirm configuration"""
        self.print_header("📋 Configuration Review")

        print(f"{Colors.BOLD}Project Configuration:{Colors.ENDC}")
        print(f"  Name: {self.project_config['name']}")
        print(f"  Template: {self.project_config['template'].upper()}")
        print(f"  Target Platforms: {', '.join(self.project_config['target_platforms'])}")

        if self.project_config["features"]:
            print(f"\n{Colors.BOLD}Selected Features:{Colors.ENDC}")
            for feature, value in self.project_config["features"].items():
                if isinstance(value, list):
                    if value:
                        print(f"  {feature}: {', '.join(value)}")
                elif value:
                    print(f"  {feature}: Enabled")

        if self.project_config["custom_settings"]:
            print(f"\n{Colors.BOLD}Custom Settings:{Colors.ENDC}")
            for setting, value in self.project_config["custom_settings"].items():
                print(f"  {setting}: {value}")

        print(f"\n{Colors.BOLD}Estimated Generation Time:{Colors.ENDC}")
        complexity = len(self.project_config["features"])
        if complexity <= 3:
            print("  ⏱️  Low complexity: 2-5 minutes")
        elif complexity <= 6:
            print("  ⏱️  Medium complexity: 5-10 minutes")
        else:
            print("  ⏱️  High complexity: 10-20 minutes")

    async def generate_project(self):
        """Generate the game project"""
        self.print_header("🚀 Generating Project")

        template_name = self.project_config["template"]

        if template_name not in self.template_classes:
            self.print_error(f"Template '{template_name}' not implemented yet")
            return

        try:
            # Create template instance
            template_class = self.template_classes[template_name]
            template = template_class(
                project_name=self.project_config["name"],
                features=self.project_config["features"],
                custom_settings=self.project_config["custom_settings"]
            )

            self.print_info("Starting project generation...")

            # Generate project
            result = await template.generate_project()

            if result.get("success", False):
                self.print_success(f"Project '{self.project_config['name']}' generated successfully!")

                # Show summary
                summary = result.get("summary", {})
                print(f"\n{Colors.GREEN}Generation Summary:{Colors.ENDC}")
                print(f"  Blueprints created: {summary.get('blueprints_created', 0)}")
                print(f"  Components added: {summary.get('components_added', 0)}")
                print(f"  Assets organized: {summary.get('assets_organized', 0)}")
                print(f"  Generation time: {summary.get('generation_time', 'Unknown')}")

                # Next steps
                print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
                print("1. Open your Unreal Engine project")
                print("2. Compile blueprints if needed")
                print("3. Test the generated systems")
                print("4. Customize and expand as needed")

            else:
                self.print_error(f"Project generation failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            self.print_error(f"Error during project generation: {e}")

    async def save_configuration(self):
        """Save configuration to file for later use"""
        config_path = Path(f"{self.project_config['name']}_config.json")

        with open(config_path, 'w') as f:
            json.dump(self.project_config, f, indent=2)

        self.print_success(f"Configuration saved to {config_path}")
        self.print_info(f"You can generate the project later using: python custom_game_setup.py --config {config_path}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Interactive Game Setup Wizard")
    parser.add_argument("--template", choices=["fps", "platformer", "rpg", "custom"], help="Skip template selection")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--config", help="Load configuration from file")

    args = parser.parse_args()

    wizard = GameSetupWizard()

    # Pre-fill configuration from arguments
    if args.name:
        wizard.project_config["name"] = args.name
    if args.template:
        wizard.project_config["template"] = args.template

    # Load configuration from file if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                loaded_config = json.load(f)
                wizard.project_config.update(loaded_config)
            wizard.print_success(f"Configuration loaded from {args.config}")
        except Exception as e:
            wizard.print_error(f"Failed to load configuration: {e}")
            sys.exit(1)

    # Run wizard
    try:
        asyncio.run(wizard.run_wizard())
    except KeyboardInterrupt:
        wizard.print_warning("\nWizard cancelled by user")

if __name__ == "__main__":
    main()