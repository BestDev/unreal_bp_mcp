// Copyright Epic Games, Inc. All Rights Reserved.
// MCPStatusWidget - UI widget for displaying MCP server connection status and logs

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "UnrealBlueprintMCPAPI.h"
#include "MCPSettings.h"

class UMCPClient;

class SVerticalBox;
class STextBlock;
class SEditableTextBox;
class SButton;
class SCheckBox;
class SScrollBox;
class SBorder;

/**
 * Structure representing a log entry for the MCP status widget
 */
struct FMCPLogEntry
{
	/** Timestamp when the log entry was created */
	FDateTime Timestamp;

	/** Log level (Info, Warning, Error, etc.) */
	FString Level;

	/** The log message content */
	FString Message;

	/** Color to display this log entry (based on level) */
	FLinearColor Color;

	/** Constructor */
	FMCPLogEntry(const FString& InLevel, const FString& InMessage, const FLinearColor& InColor = FLinearColor::White)
		: Timestamp(FDateTime::Now())
		, Level(InLevel)
		, Message(InMessage)
		, Color(InColor)
	{
	}
};

/**
 * Slate widget for displaying MCP server connection status, settings, and operation logs.
 *
 * This widget provides a comprehensive interface for monitoring and controlling
 * the MCP plugin's connection to external AI servers. It displays:
 * - Current connection status and server information
 * - Quick access to key settings
 * - Real-time operation logs
 * - Manual connection controls
 *
 * The widget automatically updates when connection state changes and provides
 * visual feedback for all MCP operations.
 */
class UNREALBLUEPRINTMCP_API SMCPStatusWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SMCPStatusWidget) {}
	SLATE_END_ARGS()

	/** Constructs the widget */
	void Construct(const FArguments& InArgs);

	/** Destructor */
	virtual ~SMCPStatusWidget();

	/**
	 * Add a new log entry to the status widget
	 * @param Level Log level (Info, Warning, Error, etc.)
	 * @param Message The log message to display
	 * @param Color Optional color override for the message
	 */
	void AddLogEntry(const FString& Level, const FString& Message, const FLinearColor& Color = FLinearColor::White);

	/**
	 * Clear all log entries from the display
	 */
	void ClearLogEntries();

	/**
	 * Update the connection status display
	 * @param NewState The new connection state to display
	 */
	void UpdateConnectionStatus(EMCPConnectionState NewState);

	/**
	 * Update the server information display
	 */
	void RefreshServerInfo();

private:
	// Widget construction helpers

	/** Creates the connection status section */
	TSharedRef<SWidget> CreateConnectionStatusSection();

	/** Creates the server settings section */
	TSharedRef<SWidget> CreateServerSettingsSection();

	/** Creates the connection controls section */
	TSharedRef<SWidget> CreateConnectionControlsSection();

	/** Creates the log display section */
	TSharedRef<SWidget> CreateLogDisplaySection();

	// Event handlers

	/** Called when the Connect button is clicked */
	FReply OnConnectButtonClicked();

	/** Called when the Disconnect button is clicked */
	FReply OnDisconnectButtonClicked();

	/** Called when the Refresh Settings button is clicked */
	FReply OnRefreshSettingsClicked();

	/** Called when the Clear Logs button is clicked */
	FReply OnClearLogsClicked();

	/** Called when the Export Logs button is clicked */
	FReply OnExportLogsClicked();

	/** Called when server address text is changed */
	void OnServerAddressChanged(const FText& NewText);

	/** Called when server port text is changed */
	void OnServerPortChanged(const FText& NewText);

	/** Called when auto-connect checkbox state changes */
	void OnAutoConnectChanged(ECheckBoxState NewState);

	// UI update helpers

	/** Get the text for connection status display */
	FText GetConnectionStatusText() const;

	/** Get the color for connection status display */
	FSlateColor GetConnectionStatusColor() const;

	/** Get the server URL display text */
	FText GetServerURLText() const;

	/** Get the last connection time display text */
	FText GetLastConnectionTimeText() const;

	/** Check if the Connect button should be enabled */
	bool IsConnectButtonEnabled() const;

	/** Check if the Disconnect button should be enabled */
	bool IsDisconnectButtonEnabled() const;

	/** Get the current server address for editing */
	FText GetServerAddressText() const;

	/** Get the current server port for editing */
	FText GetServerPortText() const;

	/** Get the current auto-connect state */
	ECheckBoxState GetAutoConnectState() const;

	/** Create a formatted log entry widget */
	TSharedRef<SWidget> CreateLogEntryWidget(const FMCPLogEntry& LogEntry);

	/** Refresh the log display */
	void RefreshLogDisplay();

	/** Apply color coding based on connection state */
	FLinearColor GetConnectionStateColor(EMCPConnectionState State) const;

	/** Format timestamp for display */
	FString FormatTimestamp(const FDateTime& Timestamp) const;

private:
	// Widget references
	TSharedPtr<STextBlock> ConnectionStatusText;
	TSharedPtr<STextBlock> ServerURLText;
	TSharedPtr<STextBlock> LastConnectionTimeText;
	TSharedPtr<SEditableTextBox> ServerAddressEditBox;
	TSharedPtr<SEditableTextBox> ServerPortEditBox;
	TSharedPtr<SCheckBox> AutoConnectCheckBox;
	TSharedPtr<SButton> ConnectButton;
	TSharedPtr<SButton> DisconnectButton;
	TSharedPtr<SScrollBox> LogScrollBox;
	TSharedPtr<SVerticalBox> LogContainer;

	// Data
	TArray<FMCPLogEntry> LogEntries;
	UMCPSettings* MCPSettings;

	// Cached state
	EMCPConnectionState CachedConnectionState;
	FString CachedServerAddress;
	int32 CachedServerPort;

	// Constants
	static const int32 MaxDisplayedLogEntries = 500;
	static const FLinearColor InfoColor;
	static const FLinearColor WarningColor;
	static const FLinearColor ErrorColor;
	static const FLinearColor SuccessColor;
};