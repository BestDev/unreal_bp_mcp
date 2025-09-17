// Copyright Epic Games, Inc. All Rights Reserved.
// UnrealBlueprintMCP Plugin - Phase 1 Implementation

#include "UnrealBlueprintMCP.h"
#include "MCPStatusWidget.h"
#include "MCPSettings.h"

// Unreal Engine includes
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/MultiBox/MultiBoxExtender.h"
#include "ToolMenus.h"
#include "Widgets/Docking/SDockTab.h"
#include "WorkspaceMenuStructure.h"
#include "WorkspaceMenuStructureModule.h"
#include "Styling/AppStyle.h"

// Logging
DEFINE_LOG_CATEGORY_STATIC(LogUnrealBlueprintMCP, Log, All);

#define LOCTEXT_NAMESPACE "FUnrealBlueprintMCPModule"

// Tab identifier for the MCP status window
static const FName MCPStatusTabName("MCPStatusTab");

void FUnrealBlueprintMCPModule::StartupModule()
{
	UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("UnrealBlueprintMCP module starting up..."));

	// Register editor menu extensions
	RegisterMenuExtensions();

	// Register tab spawner for MCP status window
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MCPStatusTabName,
		FOnSpawnTab::CreateRaw(this, &FUnrealBlueprintMCPModule::SpawnMCPStatusTab))
		.SetDisplayName(LOCTEXT("MCPStatusTabTitle", "MCP Status"))
		.SetTooltipText(LOCTEXT("MCPStatusTabTooltip", "Monitor MCP server connection status and settings"))
		.SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsDebugCategory())
		.SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.GameSettings"));

	UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("UnrealBlueprintMCP module started successfully"));
}

void FUnrealBlueprintMCPModule::ShutdownModule()
{
	UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("UnrealBlueprintMCP module shutting down..."));

	// Unregister menu extensions
	UnregisterMenuExtensions();

	// Unregister tab spawner
	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(MCPStatusTabName);

	UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("UnrealBlueprintMCP module shut down successfully"));
}

void FUnrealBlueprintMCPModule::RegisterMenuExtensions()
{
	// Register toolbar extension
	UToolMenus* ToolMenus = UToolMenus::Get();
	if (ToolMenus)
	{
		UToolMenu* ToolbarMenu = ToolMenus->ExtendMenu("LevelEditor.LevelEditorToolBar.PlayToolBar");
		if (ToolbarMenu)
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("MCP");
			Section.Label = LOCTEXT("MCPSectionLabel", "MCP");

			// Add MCP status button to toolbar
			Section.AddEntry(FToolMenuEntry::InitToolBarButton(
				"MCPStatus",
				FUIAction(FExecuteAction::CreateRaw(this, &FUnrealBlueprintMCPModule::OnOpenMCPStatusAction)),
				LOCTEXT("MCPStatusLabel", "MCP Status"),
				LOCTEXT("MCPStatusTooltip", "Open MCP Server Status Window"),
				FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.GameSettings")
			));

			UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("Registered MCP toolbar extension"));
		}
	}
}

void FUnrealBlueprintMCPModule::UnregisterMenuExtensions()
{
	// Cleanup is handled automatically when the module shuts down
	UE_LOG(LogUnrealBlueprintMCP, Log, TEXT("Unregistered MCP menu extensions"));
}

void FUnrealBlueprintMCPModule::OnOpenMCPStatusAction()
{
	// Open the MCP status tab
	FGlobalTabmanager::Get()->TryInvokeTab(MCPStatusTabName);
}

TSharedRef<SDockTab> FUnrealBlueprintMCPModule::SpawnMCPStatusTab(const FSpawnTabArgs& Args)
{
	// Create the MCP status widget
	TSharedRef<SMCPStatusWidget> StatusWidget = SNew(SMCPStatusWidget);

	// Create and return the dock tab containing the status widget
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			StatusWidget
		];
}

#undef LOCTEXT_NAMESPACE

// Required module implementation
IMPLEMENT_MODULE(FUnrealBlueprintMCPModule, UnrealBlueprintMCP)