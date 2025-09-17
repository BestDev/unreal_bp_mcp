// Copyright Epic Games, Inc. All Rights Reserved.
// UnrealBlueprintMCP Plugin - Phase 1 Implementation
// Enables external AI agents to control Blueprint Editor through MCP protocol

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/**
 * Main module class for the UnrealBlueprintMCP plugin.
 *
 * This module provides the foundation for external AI agents (Gemini, Claude, etc.)
 * to programmatically control the Unreal Engine 5.6 Blueprint Editor through
 * the Model Context Protocol (MCP).
 *
 * Phase 1 Features:
 * - Plugin initialization and lifecycle management
 * - Editor toolbar integration with MCP menu
 * - Basic status window widget
 * - Settings management for MCP server configuration
 *
 * Architecture:
 * - External MCP Server (Python) <-> WebSocket <-> Unreal Plugin (C++)
 * - The plugin acts as a WebSocket client connecting to external Python MCP server
 * - Provides UI for monitoring connection status and basic configuration
 */
class FUnrealBlueprintMCPModule : public IModuleInterface
{
public:

	/**
	 * Called when the module is loaded.
	 * Initializes editor UI extensions and prepares for MCP server connection.
	 */
	virtual void StartupModule() override;

	/**
	 * Called when the module is unloaded.
	 * Cleans up UI extensions and closes any active connections.
	 */
	virtual void ShutdownModule() override;

private:

	/**
	 * Registers editor toolbar menu extensions.
	 * Adds MCP menu button to the main editor toolbar.
	 */
	void RegisterMenuExtensions();

	/**
	 * Unregisters editor toolbar menu extensions.
	 * Removes MCP menu button from the editor toolbar.
	 */
	void UnregisterMenuExtensions();

	/**
	 * Creates and populates the MCP menu with relevant actions.
	 * @param MenuBuilder The menu builder to populate
	 */
	void CreateMCPMenu(class FMenuBuilder& MenuBuilder);

	/**
	 * Opens the MCP status window.
	 * Shows current connection status, server settings, and logs.
	 */
	void OpenMCPStatusWindow();

	/**
	 * Handles the menu action for opening status window.
	 * Called when user clicks on "Open MCP Status" menu item.
	 */
	void OnOpenMCPStatusAction();

	/**
	 * Spawns the MCP status tab when requested.
	 * @param Args Spawn arguments for the tab
	 * @return The created dock tab containing the status widget
	 */
	TSharedRef<class SDockTab> SpawnMCPStatusTab(const class FSpawnTabArgs& Args);

	/**
	 * Initializes the MCP client and attempts auto-connection if enabled.
	 * Called during module startup to establish connection to MCP server.
	 */
	void InitializeMCPClient();

	/**
	 * Shuts down the MCP client and disconnects from server.
	 * Called during module shutdown to ensure clean disconnection.
	 */
	void ShutdownMCPClient();

	/** Handle to the registered menu extender */
	TSharedPtr<class FExtender> MenuExtender;

	/** Handle to the registered toolbar extension */
	TSharedPtr<const class FExtensionBase> ToolbarExtension;
};