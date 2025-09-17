// Copyright Epic Games, Inc. All Rights Reserved.
// MCPSettings - Configuration management for MCP server connection

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "Engine/DeveloperSettings.h"
#include "UnrealBlueprintMCPAPI.h"
#include "MCPSettings.generated.h"

/**
 * Enumeration for MCP connection state
 */
UENUM(BlueprintType)
enum class EMCPConnectionState : uint8
{
	/** Not connected to MCP server */
	Disconnected = 0,

	/** Attempting to connect to MCP server */
	Connecting = 1,

	/** Successfully connected to MCP server */
	Connected = 2,

	/** Connection failed or lost */
	Failed = 3,

	/** Connection was manually disabled */
	Disabled = 4
};

/**
 * Settings class for configuring MCP server connection and behavior.
 *
 * This class manages all configuration options for the UnrealBlueprintMCP plugin,
 * including server connection details, authentication settings, and operational parameters.
 *
 * Settings are automatically saved to the project's configuration files and can be
 * modified through the Editor Preferences or programmatically at runtime.
 */
UCLASS(config = EditorPerProjectUserSettings, defaultconfig, meta = (DisplayName = "MCP Settings"))
class UNREALBLUEPRINTMCP_API UMCPSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	/** Constructor */
	UMCPSettings(const FObjectInitializer& ObjectInitializer);

	//~ Begin UDeveloperSettings Interface
	virtual FName GetCategoryName() const override;
	virtual FText GetSectionText() const override;
	virtual FText GetSectionDescription() const override;
	//~ End UDeveloperSettings Interface

	/** Get the singleton instance of MCPSettings */
	static UMCPSettings* Get();

	/**
	 * Validate the current settings configuration
	 * @return True if settings are valid and ready for connection
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Settings")
	bool ValidateSettings() const;

	/**
	 * Reset all settings to their default values
	 */
	UFUNCTION(BlueprintCallable, Category = "MCP Settings")
	void ResetToDefaults();

	/**
	 * Get the complete WebSocket URL for MCP server connection
	 * @return Formatted WebSocket URL (ws://ServerAddress:ServerPort/MCPEndpoint)
	 */
	UFUNCTION(BlueprintPure, Category = "MCP Settings")
	FString GetWebSocketURL() const;

public:
	// Connection Settings

	/** IP address or hostname of the MCP server */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Server Address"))
	FString ServerAddress;

	/** Port number for the MCP server WebSocket connection */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Server Port", ClampMin = "1", ClampMax = "65535"))
	int32 ServerPort;

	/** WebSocket endpoint path on the MCP server */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Endpoint Path"))
	FString MCPEndpoint;

	/** Whether to automatically attempt connection when the editor starts */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Auto Connect on Startup"))
	bool bAutoConnectOnStartup;

	/** Number of seconds to wait before attempting to reconnect after connection loss */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Reconnect Delay (seconds)", ClampMin = "1", ClampMax = "300"))
	int32 ReconnectDelay;

	/** Maximum number of reconnection attempts before giving up */
	UPROPERTY(config, EditAnywhere, Category = "Connection", meta = (DisplayName = "Max Reconnect Attempts", ClampMin = "0", ClampMax = "100"))
	int32 MaxReconnectAttempts;

	// Security Settings

	/** Whether to use SSL/TLS for WebSocket connection (wss://) */
	UPROPERTY(config, EditAnywhere, Category = "Security", meta = (DisplayName = "Use SSL/TLS"))
	bool bUseSSL;

	/** API key for authenticating with the MCP server (optional) */
	UPROPERTY(config, EditAnywhere, Category = "Security", meta = (DisplayName = "API Key", PasswordField = true))
	FString APIKey;

	/** Whether to verify SSL certificates (only used when SSL is enabled) */
	UPROPERTY(config, EditAnywhere, Category = "Security", meta = (DisplayName = "Verify SSL Certificates", EditCondition = "bUseSSL"))
	bool bVerifySSLCertificates;

	// Operational Settings

	/** Whether to enable verbose logging for MCP operations */
	UPROPERTY(config, EditAnywhere, Category = "Debug", meta = (DisplayName = "Enable Verbose Logging"))
	bool bEnableVerboseLogging;

	/** Maximum number of log entries to keep in memory */
	UPROPERTY(config, EditAnywhere, Category = "Debug", meta = (DisplayName = "Max Log Entries", ClampMin = "10", ClampMax = "10000"))
	int32 MaxLogEntries;

	/** Whether to show desktop notifications for important MCP events */
	UPROPERTY(config, EditAnywhere, Category = "Notifications", meta = (DisplayName = "Show Desktop Notifications"))
	bool bShowDesktopNotifications;

	/** Whether to play sounds for connection state changes */
	UPROPERTY(config, EditAnywhere, Category = "Notifications", meta = (DisplayName = "Play Connection Sounds"))
	bool bPlayConnectionSounds;

	// Blueprint Safety Settings

	/** Whether to create backup copies of blueprints before modification */
	UPROPERTY(config, EditAnywhere, Category = "Safety", meta = (DisplayName = "Create Blueprint Backups"))
	bool bCreateBlueprintBackups;

	/** Directory path for storing blueprint backups (relative to project folder) */
	UPROPERTY(config, EditAnywhere, Category = "Safety", meta = (DisplayName = "Backup Directory", EditCondition = "bCreateBlueprintBackups"))
	FString BackupDirectory;

	/** Whether to require user confirmation before executing destructive operations */
	UPROPERTY(config, EditAnywhere, Category = "Safety", meta = (DisplayName = "Require Confirmation for Destructive Operations"))
	bool bRequireConfirmationForDestructiveOps;

	/** List of blueprint paths that are protected from MCP modifications */
	UPROPERTY(config, EditAnywhere, Category = "Safety", meta = (DisplayName = "Protected Blueprint Paths"))
	TArray<FString> ProtectedBlueprintPaths;

private:
	/** Current connection state (runtime only, not saved to config) */
	UPROPERTY(Transient)
	EMCPConnectionState ConnectionState;

	/** Timestamp of last successful connection (runtime only) */
	UPROPERTY(Transient)
	FDateTime LastConnectionTime;

	/** Number of reconnection attempts made for current session */
	UPROPERTY(Transient)
	int32 CurrentReconnectAttempts;

public:
	// Runtime State Accessors (not saved to config)

	/** Get the current connection state */
	UFUNCTION(BlueprintPure, Category = "MCP Status")
	EMCPConnectionState GetConnectionState() const { return ConnectionState; }

	/** Set the current connection state */
	void SetConnectionState(EMCPConnectionState NewState);

	/** Get the time of last successful connection */
	UFUNCTION(BlueprintPure, Category = "MCP Status")
	FDateTime GetLastConnectionTime() const { return LastConnectionTime; }

	/** Get the current number of reconnection attempts */
	UFUNCTION(BlueprintPure, Category = "MCP Status")
	int32 GetCurrentReconnectAttempts() const { return CurrentReconnectAttempts; }

	/** Increment the reconnection attempt counter */
	void IncrementReconnectAttempts();

	/** Reset the reconnection attempt counter */
	void ResetReconnectAttempts();
};