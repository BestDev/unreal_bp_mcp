// Copyright Epic Games, Inc. All Rights Reserved.
// UnrealBlueprintMCP Plugin Build Configuration

using UnrealBuildTool;

public class UnrealBlueprintMCP : ModuleRules
{
	public UnrealBlueprintMCP(ReadOnlyTargetRules Target) : base(Target)
	{
		// Precompiled header usage for faster compilation
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		// Public include paths - accessible to other modules
		PublicIncludePaths.AddRange(
			new string[] {
				// Add public include paths here if needed
			}
		);

		// Private include paths - only for this module
		PrivateIncludePaths.AddRange(
			new string[] {
				// Add private include paths here if needed
			}
		);

		// Public dependencies - required by modules that depend on this one
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine"
			}
		);

		// Private dependencies - only used by this module internally
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				// Core engine modules
				"UnrealEd",
				"ToolMenus",
				// "ToolWidgets", // Deprecated in UE5.6
				"EditorWidgets",
				"WorkspaceMenuStructure",

				// UI framework
				"Slate",
				"SlateCore",
				"InputCore",
				// "ApplicationCore", // Deprecated in UE5.6

				// Additional Slate widgets
				// "EditorStyle", // Deprecated in UE5.6

				// WebSocket support for MCP server communication (Phase 2)
				"WebSockets",
				"HTTP",

				// JSON parsing for MCP protocol
				"Json",
				"JsonUtilities",

				// Blueprint editing APIs (Phase 3)
				"KismetCompiler",
				"BlueprintGraph",
				"AssetRegistry",
				"Kismet",           // Kismet editor utilities
				"AssetTools",       // Asset creation/management tools

				// Settings management
				"Settings",
				"DeveloperSettings",
				"PropertyEditor",

				// Project management
				"Projects"
			}
		);

		// Dynamic loading modules - loaded at runtime when needed
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// Add modules that should be loaded dynamically
			}
		);

		// Editor-only module - not included in packaged builds
		if (Target.Type == TargetType.Editor)
		{
			PrivateDependencyModuleNames.AddRange(
				new string[]
				{
					"LevelEditor",
					"MainFrame"
				}
			);
		}

		// Platform-specific settings
		if (Target.Platform == UnrealTargetPlatform.Win64)
		{
			// Windows-specific dependencies if needed
		}
		else if (Target.Platform == UnrealTargetPlatform.Mac)
		{
			// Mac-specific dependencies if needed
		}
		else if (Target.Platform == UnrealTargetPlatform.Linux)
		{
			// Linux-specific dependencies if needed
		}

		// Compiler definitions
		PublicDefinitions.AddRange(
			new string[]
			{
				"UNREAL_BLUEPRINT_MCP_PLUGIN=1"
			}
		);

		// Enable RTTI for advanced C++ features if needed
		bUseRTTI = false;

		// Exception handling
		bEnableExceptions = false;

		// Optimization settings
		OptimizeCode = CodeOptimization.Default;
	}
}