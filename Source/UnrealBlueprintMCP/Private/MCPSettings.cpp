// Copyright Epic Games, Inc. All Rights Reserved.
// MCPSettings - Configuration management for MCP server connection

#include "MCPSettings.h"
#include "Misc/Paths.h"

// Logging
DEFINE_LOG_CATEGORY_STATIC(LogMCPSettings, Log, All);

#define LOCTEXT_NAMESPACE "MCPSettings"

UMCPSettings::UMCPSettings(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Set default values
	ServerAddress = TEXT("localhost");
	ServerPort = 6277;  // Changed to match FastAPI server port
	MCPEndpoint = TEXT("/");
	bAutoConnectOnStartup = false;
	ReconnectDelay = 5;
	MaxReconnectAttempts = 3;

	// Security defaults
	bUseSSL = false;
	APIKey = TEXT("");
	bVerifySSLCertificates = true;

	// Debug defaults
	bEnableVerboseLogging = false;
	MaxLogEntries = 1000;

	// Notification defaults
	bShowDesktopNotifications = true;
	bPlayConnectionSounds = false;

	// Safety defaults
	bCreateBlueprintBackups = true;
	BackupDirectory = TEXT("Saved/MCP_Backups");
	bRequireConfirmationForDestructiveOps = true;
	ProtectedBlueprintPaths.Add(TEXT("/Game/Core/"));
	ProtectedBlueprintPaths.Add(TEXT("/Engine/"));

	// Runtime state initialization
	ConnectionState = EMCPConnectionState::Disconnected;
	LastConnectionTime = FDateTime::MinValue();
	CurrentReconnectAttempts = 0;
}

FName UMCPSettings::GetCategoryName() const
{
	return FName("Plugins");
}

FText UMCPSettings::GetSectionText() const
{
	return LOCTEXT("MCPSettingsSection", "MCP Settings");
}

FText UMCPSettings::GetSectionDescription() const
{
	return LOCTEXT("MCPSettingsDescription", "Configure Model Context Protocol (MCP) server connection and behavior settings.");
}

UMCPSettings* UMCPSettings::Get()
{
	return GetMutableDefault<UMCPSettings>();
}

bool UMCPSettings::ValidateSettings() const
{
	// Check if server address is not empty
	if (ServerAddress.IsEmpty())
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("Server address is empty"));
		return false;
	}

	// Validate port range
	if (ServerPort < 1 || ServerPort > 65535)
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("Server port %d is out of valid range (1-65535)"), ServerPort);
		return false;
	}

	// Check endpoint format
	if (MCPEndpoint.IsEmpty() || !MCPEndpoint.StartsWith(TEXT("/")))
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("MCP endpoint must start with '/' and cannot be empty"));
		return false;
	}

	// Validate reconnection settings
	if (ReconnectDelay < 1 || ReconnectDelay > 300)
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("Reconnect delay %d is out of valid range (1-300 seconds)"), ReconnectDelay);
		return false;
	}

	if (MaxReconnectAttempts < 0 || MaxReconnectAttempts > 100)
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("Max reconnect attempts %d is out of valid range (0-100)"), MaxReconnectAttempts);
		return false;
	}

	// Validate backup directory if backups are enabled
	if (bCreateBlueprintBackups && BackupDirectory.IsEmpty())
	{
		UE_LOG(LogMCPSettings, Warning, TEXT("Backup directory cannot be empty when blueprint backups are enabled"));
		return false;
	}

	// All validations passed
	UE_LOG(LogMCPSettings, Log, TEXT("Settings validation passed"));
	return true;
}

void UMCPSettings::ResetToDefaults()
{
	UE_LOG(LogMCPSettings, Log, TEXT("Resetting MCP settings to defaults"));

	// Reset to constructor defaults
	ServerAddress = TEXT("localhost");
	ServerPort = 6277;  // Changed to match FastAPI server port
	MCPEndpoint = TEXT("/");
	bAutoConnectOnStartup = false;
	ReconnectDelay = 5;
	MaxReconnectAttempts = 3;

	bUseSSL = false;
	APIKey = TEXT("");
	bVerifySSLCertificates = true;

	bEnableVerboseLogging = false;
	MaxLogEntries = 1000;

	bShowDesktopNotifications = true;
	bPlayConnectionSounds = false;

	bCreateBlueprintBackups = true;
	BackupDirectory = TEXT("Saved/MCP_Backups");
	bRequireConfirmationForDestructiveOps = true;

	ProtectedBlueprintPaths.Empty();
	ProtectedBlueprintPaths.Add(TEXT("/Game/Core/"));
	ProtectedBlueprintPaths.Add(TEXT("/Engine/"));

	// Reset runtime state
	ConnectionState = EMCPConnectionState::Disconnected;
	LastConnectionTime = FDateTime::MinValue();
	CurrentReconnectAttempts = 0;

	// Save the updated settings
	SaveConfig();
}

FString UMCPSettings::GetWebSocketURL() const
{
	FString Protocol = bUseSSL ? TEXT("wss") : TEXT("ws");
	FString CleanEndpoint = MCPEndpoint;

	// Ensure endpoint starts with '/'
	if (!CleanEndpoint.StartsWith(TEXT("/")))
	{
		CleanEndpoint = TEXT("/") + CleanEndpoint;
	}

	return FString::Printf(TEXT("%s://%s:%d%s"), *Protocol, *ServerAddress, ServerPort, *CleanEndpoint);
}

void UMCPSettings::SetConnectionState(EMCPConnectionState NewState)
{
	if (ConnectionState != NewState)
	{
		EMCPConnectionState OldState = ConnectionState;
		ConnectionState = NewState;

		// Update connection time for successful connections
		if (NewState == EMCPConnectionState::Connected)
		{
			LastConnectionTime = FDateTime::Now();
			ResetReconnectAttempts();
		}

		// Log state change
		UE_LOG(LogMCPSettings, Log, TEXT("Connection state changed from %d to %d"),
			static_cast<int32>(OldState), static_cast<int32>(NewState));

		// Broadcast state change if needed (for UI updates)
		// Note: In a more complex implementation, you might want to add a delegate here
	}
}

void UMCPSettings::IncrementReconnectAttempts()
{
	CurrentReconnectAttempts++;
	UE_LOG(LogMCPSettings, Log, TEXT("Reconnect attempts: %d/%d"), CurrentReconnectAttempts, MaxReconnectAttempts);
}

void UMCPSettings::ResetReconnectAttempts()
{
	if (CurrentReconnectAttempts > 0)
	{
		UE_LOG(LogMCPSettings, Log, TEXT("Resetting reconnect attempts counter"));
		CurrentReconnectAttempts = 0;
	}
}

#undef LOCTEXT_NAMESPACE