#!/usr/bin/env python3
"""
Shared Configuration for Advanced Examples

This module provides common configuration settings used across
all advanced examples in the UnrealBlueprintMCP project.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    # Look for .env file in project root (two levels up from this file)
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print(f".env file not found at {env_path}, using system environment variables only")
except ImportError:
    print("python-dotenv not installed, using system environment variables only")

# MCP Server Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "ws://localhost:6277")
MCP_TIMEOUT = float(os.getenv("MCP_TIMEOUT", "30.0"))

# Unreal Engine Configuration
UNREAL_PROJECT_PATH = os.getenv("UNREAL_PROJECT_PATH", "/path/to/your/unreal/project")
UNREAL_ENGINE_PATH = os.getenv("UNREAL_ENGINE_PATH", "/path/to/unreal/engine")

# Batch Operation Settings
DEFAULT_BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_CONCURRENT_OPERATIONS = int(os.getenv("MAX_CONCURRENT_OPS", "5"))
BATCH_DELAY_SECONDS = float(os.getenv("BATCH_DELAY", "0.1"))

# Performance Monitoring
ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERF_LOGGING", "true").lower() == "true"
PERFORMANCE_LOG_FILE = os.getenv("PERF_LOG_FILE", "examples_performance.log")

# Web Dashboard Configuration
WEB_DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "localhost")
WEB_DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))
DASHBOARD_AUTO_REFRESH = int(os.getenv("DASHBOARD_REFRESH", "5"))  # seconds

# AI/LangChain Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_MODEL = os.getenv("LANGCHAIN_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

def validate_openai_api_key() -> bool:
    """Validate OpenAI API key format and presence"""
    if not OPENAI_API_KEY:
        return False

    # Basic API key format validation (OpenAI keys start with 'sk-' and are typically 51 chars)
    if not OPENAI_API_KEY.startswith('sk-') or len(OPENAI_API_KEY) < 20:
        return False

    return True

# Game Template Configurations
GAME_TEMPLATES = {
    "fps_template": {
        "name": "First Person Shooter Template",
        "blueprints": ["PlayerCharacter", "WeaponBase", "ProjectileBase", "GameMode"],
        "base_classes": ["Character", "Actor", "Actor", "GameModeBase"],
        "required_components": ["Movement", "Inventory", "Health", "Weapon"]
    },
    "platformer_template": {
        "name": "2D Platformer Template",
        "blueprints": ["PlatformerCharacter", "MovingPlatform", "Collectible", "Enemy"],
        "base_classes": ["Character", "Actor", "Actor", "Pawn"],
        "required_components": ["Movement", "Physics", "Collection", "AI"]
    },
    "rpg_template": {
        "name": "RPG Template",
        "blueprints": ["RPGCharacter", "NPCBase", "ItemBase", "QuestSystem"],
        "base_classes": ["Character", "Character", "Actor", "ActorComponent"],
        "required_components": ["Stats", "Dialogue", "Inventory", "Quest"]
    }
}

# Asset Path Configurations
DEFAULT_ASSET_PATHS = {
    "blueprints": "/Game/Blueprints/",
    "characters": "/Game/Blueprints/Characters/",
    "weapons": "/Game/Blueprints/Weapons/",
    "items": "/Game/Blueprints/Items/",
    "ui": "/Game/Blueprints/UI/",
    "gameplay": "/Game/Blueprints/Gameplay/"
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "advanced_examples.log",
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        }
    }
}

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent.parent

def get_unreal_project_path() -> Path:
    """Get the Unreal project path, with validation"""
    path = Path(UNREAL_PROJECT_PATH)
    if not path.exists() or UNREAL_PROJECT_PATH == "/path/to/your/unreal/project":
        raise ValueError(
            f"Invalid Unreal project path: {UNREAL_PROJECT_PATH}. "
            "Please set UNREAL_PROJECT_PATH environment variable."
        )
    return path

def validate_configuration() -> Dict[str, Any]:
    """Validate configuration and return status"""
    issues = []

    # Check MCP server URL
    if not MCP_SERVER_URL.startswith(("ws://", "wss://")):
        issues.append(f"Invalid MCP server URL: {MCP_SERVER_URL}")

    # Check Unreal paths
    try:
        get_unreal_project_path()
    except ValueError as e:
        issues.append(str(e))

    # Check AI configuration if needed
    if not validate_openai_api_key():
        issues.append("OPENAI_API_KEY is missing or invalid format (should start with 'sk-' and be at least 20 characters)")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "config": {
            "mcp_server": MCP_SERVER_URL,
            "batch_size": DEFAULT_BATCH_SIZE,
            "performance_logging": ENABLE_PERFORMANCE_LOGGING,
            "dashboard_port": WEB_DASHBOARD_PORT
        }
    }

if __name__ == "__main__":
    # Configuration validation when run directly
    result = validate_configuration()
    print("Configuration Validation Results:")
    print(f"Valid: {result['valid']}")

    if result['issues']:
        print("Issues found:")
        for issue in result['issues']:
            print(f"  - {issue}")

    print(f"\nCurrent Configuration:")
    for key, value in result['config'].items():
        print(f"  {key}: {value}")