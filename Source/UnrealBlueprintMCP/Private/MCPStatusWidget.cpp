// Copyright Epic Games, Inc. All Rights Reserved.
// MCPStatusWidget - UI widget for displaying MCP server connection status and logs

#include "MCPStatusWidget.h"
#include "MCPSettings.h"
#include "MCPClient.h"

// Slate includes
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Styling/AppStyle.h"
#include "Styling/CoreStyle.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFilemanager.h"
#include "Misc/Paths.h"
#include "Misc/DateTime.h"

// Logging
DEFINE_LOG_CATEGORY_STATIC(LogMCPStatusWidget, Log, All);

#define LOCTEXT_NAMESPACE "MCPStatusWidget"

// Color constants
const FLinearColor SMCPStatusWidget::InfoColor = FLinearColor::White;
const FLinearColor SMCPStatusWidget::WarningColor = FLinearColor::Yellow;
const FLinearColor SMCPStatusWidget::ErrorColor = FLinearColor::Red;
const FLinearColor SMCPStatusWidget::SuccessColor = FLinearColor::Green;

void SMCPStatusWidget::Construct(const FArguments& InArgs)
{
	// Get settings instance
	MCPSettings = UMCPSettings::Get();
	check(MCPSettings);

	// Initialize cached values
	CachedConnectionState = MCPSettings->GetConnectionState();
	CachedServerAddress = MCPSettings->ServerAddress;
	CachedServerPort = MCPSettings->ServerPort;

	// Build the widget hierarchy
	ChildSlot
	[
		SNew(SVerticalBox)

		// Header
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5, 5, 5, 10)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("MCPStatusTitle", "MCP Server Status"))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 16))
			.Justification(ETextJustify::Center)
		]

		// Connection Status Section
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5)
		[
			CreateConnectionStatusSection()
		]

		// Separator
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5, 2)
		[
			SNew(SSeparator)
		]

		// Server Settings Section
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5)
		[
			CreateServerSettingsSection()
		]

		// Separator
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5, 2)
		[
			SNew(SSeparator)
		]

		// Connection Controls Section
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5)
		[
			CreateConnectionControlsSection()
		]

		// Separator
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(5, 2)
		[
			SNew(SSeparator)
		]

		// Log Display Section
		+ SVerticalBox::Slot()
		.FillHeight(1.0f)
		.Padding(5)
		[
			CreateLogDisplaySection()
		]
	];

	// Add initial log entry
	AddLogEntry(TEXT("Info"), TEXT("MCP Status Widget initialized"), InfoColor);

	// Register with MCPClient for status updates
	UMCPClient* MCPClient = UMCPClient::Get();
	if (MCPClient)
	{
		MCPClient->RegisterStatusWidget(SharedThis(this));
		AddLogEntry(TEXT("Info"), TEXT("Registered with MCP Client for updates"), InfoColor);
	}
}

SMCPStatusWidget::~SMCPStatusWidget()
{
	// Unregister from MCPClient
	UMCPClient* MCPClient = UMCPClient::Get();
	if (MCPClient)
	{
		MCPClient->UnregisterStatusWidget(SharedThis(this));
	}
}

TSharedRef<SWidget> SMCPStatusWidget::CreateConnectionStatusSection()
{
	return SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
		.Padding(10)
		[
			SNew(SVerticalBox)

			// Section title
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 0, 0, 5)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ConnectionStatusSection", "Connection Status"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
			]

			// Connection state
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 2)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("StatusLabel", "Status: "))
				]

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				[
					SAssignNew(ConnectionStatusText, STextBlock)
					.Text(this, &SMCPStatusWidget::GetConnectionStatusText)
					.ColorAndOpacity(this, &SMCPStatusWidget::GetConnectionStatusColor)
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 10))
				]
			]

			// Server URL
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 2)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("ServerURLLabel", "Server URL: "))
				]

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				[
					SAssignNew(ServerURLText, STextBlock)
					.Text(this, &SMCPStatusWidget::GetServerURLText)
					.Font(FCoreStyle::GetDefaultFontStyle("Regular", 9))
				]
			]

			// Last connection time
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 2)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("LastConnectionLabel", "Last Connected: "))
				]

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				[
					SAssignNew(LastConnectionTimeText, STextBlock)
					.Text(this, &SMCPStatusWidget::GetLastConnectionTimeText)
					.Font(FCoreStyle::GetDefaultFontStyle("Regular", 9))
				]
			]
		];
}

TSharedRef<SWidget> SMCPStatusWidget::CreateServerSettingsSection()
{
	return SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
		.Padding(10)
		[
			SNew(SVerticalBox)

			// Section title
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 0, 0, 5)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ServerSettingsSection", "Quick Settings"))
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
			]

			// Server address
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 2)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				.Padding(0, 0, 10, 0)
				[
					SNew(SBox)
					.WidthOverride(100)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("ServerAddressLabel", "Server Address:"))
					]
				]

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				[
					SAssignNew(ServerAddressEditBox, SEditableTextBox)
					.Text(this, &SMCPStatusWidget::GetServerAddressText)
					.OnTextChanged(this, &SMCPStatusWidget::OnServerAddressChanged)
				]
			]

			// Server port
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 2)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.VAlign(VAlign_Center)
				.Padding(0, 0, 10, 0)
				[
					SNew(SBox)
					.WidthOverride(100)
					[
						SNew(STextBlock)
						.Text(LOCTEXT("ServerPortLabel", "Server Port:"))
					]
				]

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				[
					SAssignNew(ServerPortEditBox, SEditableTextBox)
					.Text(this, &SMCPStatusWidget::GetServerPortText)
					.OnTextChanged(this, &SMCPStatusWidget::OnServerPortChanged)
				]
			]

			// Auto-connect checkbox
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 5, 0, 0)
			[
				SAssignNew(AutoConnectCheckBox, SCheckBox)
				.IsChecked(this, &SMCPStatusWidget::GetAutoConnectState)
				.OnCheckStateChanged(this, &SMCPStatusWidget::OnAutoConnectChanged)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("AutoConnectLabel", "Auto-connect on startup"))
				]
			]
		];
}

TSharedRef<SWidget> SMCPStatusWidget::CreateConnectionControlsSection()
{
	return SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
		.Padding(10)
		[
			SNew(SHorizontalBox)

			// Connect button
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(0, 0, 5, 0)
			[
				SAssignNew(ConnectButton, SButton)
				.Text(LOCTEXT("ConnectButton", "Connect"))
				.ToolTipText(LOCTEXT("ConnectButtonTooltip", "Attempt to connect to the MCP server"))
				.OnClicked(this, &SMCPStatusWidget::OnConnectButtonClicked)
				.IsEnabled(this, &SMCPStatusWidget::IsConnectButtonEnabled)
			]

			// Disconnect button
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(5, 0)
			[
				SAssignNew(DisconnectButton, SButton)
				.Text(LOCTEXT("DisconnectButton", "Disconnect"))
				.ToolTipText(LOCTEXT("DisconnectButtonTooltip", "Disconnect from the MCP server"))
				.OnClicked(this, &SMCPStatusWidget::OnDisconnectButtonClicked)
				.IsEnabled(this, &SMCPStatusWidget::IsDisconnectButtonEnabled)
			]

			// Refresh settings button
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.Padding(5, 0)
			[
				SNew(SButton)
				.Text(LOCTEXT("RefreshButton", "Refresh Settings"))
				.ToolTipText(LOCTEXT("RefreshButtonTooltip", "Reload settings from configuration"))
				.OnClicked(this, &SMCPStatusWidget::OnRefreshSettingsClicked)
			]
		];
}

TSharedRef<SWidget> SMCPStatusWidget::CreateLogDisplaySection()
{
	return SNew(SBorder)
		.BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder"))
		.Padding(10)
		[
			SNew(SVerticalBox)

			// Section header
			+ SVerticalBox::Slot()
			.AutoHeight()
			.Padding(0, 0, 0, 5)
			[
				SNew(SHorizontalBox)

				+ SHorizontalBox::Slot()
				.FillWidth(1.0f)
				.VAlign(VAlign_Center)
				[
					SNew(STextBlock)
					.Text(LOCTEXT("LogDisplaySection", "Operation Logs"))
					.Font(FCoreStyle::GetDefaultFontStyle("Bold", 12))
				]

				+ SHorizontalBox::Slot()
				.AutoWidth()
				[
					SNew(SButton)
					.Text(LOCTEXT("ClearLogsButton", "Clear"))
					.ToolTipText(LOCTEXT("ClearLogsTooltip", "Clear all log entries"))
					.OnClicked(this, &SMCPStatusWidget::OnClearLogsClicked)
				]

				+ SHorizontalBox::Slot()
				.AutoWidth()
				.Padding(5, 0, 0, 0)
				[
					SNew(SButton)
					.Text(LOCTEXT("ExportLogsButton", "Export"))
					.ToolTipText(LOCTEXT("ExportLogsTooltip", "Export logs to file"))
					.OnClicked(this, &SMCPStatusWidget::OnExportLogsClicked)
				]
			]

			// Log scroll area
			+ SVerticalBox::Slot()
			.FillHeight(1.0f)
			[
				SAssignNew(LogScrollBox, SScrollBox)
				.Orientation(Orient_Vertical)
				.ScrollBarAlwaysVisible(true)
				+ SScrollBox::Slot()
				[
					SAssignNew(LogContainer, SVerticalBox)
				]
			]
		];
}

void SMCPStatusWidget::AddLogEntry(const FString& Level, const FString& Message, const FLinearColor& Color)
{
	// Create new log entry
	FMCPLogEntry NewEntry(Level, Message, Color);
	LogEntries.Add(NewEntry);

	// Limit the number of stored entries
	if (LogEntries.Num() > MaxDisplayedLogEntries)
	{
		LogEntries.RemoveAt(0, LogEntries.Num() - MaxDisplayedLogEntries);
	}

	// Refresh the display
	RefreshLogDisplay();

	// Auto-scroll to bottom
	if (LogScrollBox.IsValid())
	{
		LogScrollBox->ScrollToEnd();
	}

	UE_LOG(LogMCPStatusWidget, Log, TEXT("[%s] %s"), *Level, *Message);
}

void SMCPStatusWidget::ClearLogEntries()
{
	LogEntries.Empty();
	RefreshLogDisplay();
	AddLogEntry(TEXT("Info"), TEXT("Log cleared"), InfoColor);
}

void SMCPStatusWidget::RefreshLogDisplay()
{
	if (!LogContainer.IsValid())
	{
		return;
	}

	// Clear existing widgets
	LogContainer->ClearChildren();

	// Add widgets for all log entries
	for (const FMCPLogEntry& Entry : LogEntries)
	{
		LogContainer->AddSlot()
		.AutoHeight()
		.Padding(0, 1)
		[
			CreateLogEntryWidget(Entry)
		];
	}
}

TSharedRef<SWidget> SMCPStatusWidget::CreateLogEntryWidget(const FMCPLogEntry& LogEntry)
{
	return SNew(SHorizontalBox)

		// Timestamp
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(0, 0, 10, 0)
		[
			SNew(STextBlock)
			.Text(FText::FromString(FormatTimestamp(LogEntry.Timestamp)))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 8))
			.ColorAndOpacity(FLinearColor::Gray)
		]

		// Level
		+ SHorizontalBox::Slot()
		.AutoWidth()
		.VAlign(VAlign_Center)
		.Padding(0, 0, 10, 0)
		[
			SNew(STextBlock)
			.Text(FText::FromString(LogEntry.Level))
			.Font(FCoreStyle::GetDefaultFontStyle("Bold", 8))
			.ColorAndOpacity(LogEntry.Color)
		]

		// Message
		+ SHorizontalBox::Slot()
		.FillWidth(1.0f)
		.VAlign(VAlign_Center)
		[
			SNew(STextBlock)
			.Text(FText::FromString(LogEntry.Message))
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 9))
			.ColorAndOpacity(LogEntry.Color)
			.AutoWrapText(true)
		];
}

FString SMCPStatusWidget::FormatTimestamp(const FDateTime& Timestamp) const
{
	return Timestamp.ToString(TEXT("%H:%M:%S"));
}

// Event handlers implementation
FReply SMCPStatusWidget::OnConnectButtonClicked()
{
	AddLogEntry(TEXT("Info"), TEXT("Manual connection requested"), InfoColor);

	// Get MCPClient instance and attempt connection
	UMCPClient* MCPClient = UMCPClient::Get();
	if (MCPClient)
	{
		// Initialize the client with current settings
		if (MCPClient->Initialize(MCPSettings))
		{
			// Attempt to connect
			if (MCPClient->Connect())
			{
				AddLogEntry(TEXT("Info"), TEXT("Connection attempt started"), InfoColor);
			}
			else
			{
				AddLogEntry(TEXT("Error"), TEXT("Failed to start connection attempt"), ErrorColor);
			}
		}
		else
		{
			AddLogEntry(TEXT("Error"), TEXT("Failed to initialize MCP client"), ErrorColor);
		}
	}
	else
	{
		AddLogEntry(TEXT("Error"), TEXT("MCP Client not available"), ErrorColor);
	}

	return FReply::Handled();
}

FReply SMCPStatusWidget::OnDisconnectButtonClicked()
{
	AddLogEntry(TEXT("Info"), TEXT("Manual disconnection requested"), InfoColor);

	// Get MCPClient instance and disconnect
	UMCPClient* MCPClient = UMCPClient::Get();
	if (MCPClient)
	{
		if (MCPClient->IsConnected())
		{
			MCPClient->Disconnect(true); // Graceful disconnect
			AddLogEntry(TEXT("Info"), TEXT("Disconnection initiated"), InfoColor);
		}
		else
		{
			AddLogEntry(TEXT("Warning"), TEXT("Client was not connected"), WarningColor);
		}
	}
	else
	{
		AddLogEntry(TEXT("Error"), TEXT("MCP Client not available"), ErrorColor);
	}

	return FReply::Handled();
}

FReply SMCPStatusWidget::OnRefreshSettingsClicked()
{
	RefreshServerInfo();
	AddLogEntry(TEXT("Info"), TEXT("Settings refreshed from configuration"), InfoColor);
	return FReply::Handled();
}

FReply SMCPStatusWidget::OnClearLogsClicked()
{
	ClearLogEntries();
	return FReply::Handled();
}

FReply SMCPStatusWidget::OnExportLogsClicked()
{
	// Create log file content
	FString LogContent;
	for (const FMCPLogEntry& Entry : LogEntries)
	{
		LogContent += FString::Printf(TEXT("[%s] [%s] %s\n"),
			*FormatTimestamp(Entry.Timestamp),
			*Entry.Level,
			*Entry.Message);
	}

	// Save to file
	FString FileName = FString::Printf(TEXT("MCP_Logs_%s.txt"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
	FString FilePath = FPaths::ProjectSavedDir() / TEXT("Logs") / FileName;

	if (FFileHelper::SaveStringToFile(LogContent, *FilePath))
	{
		AddLogEntry(TEXT("Info"), FString::Printf(TEXT("Logs exported to: %s"), *FilePath), SuccessColor);
	}
	else
	{
		AddLogEntry(TEXT("Error"), FString::Printf(TEXT("Failed to export logs to: %s"), *FilePath), ErrorColor);
	}

	return FReply::Handled();
}

void SMCPStatusWidget::OnServerAddressChanged(const FText& NewText)
{
	if (MCPSettings)
	{
		MCPSettings->ServerAddress = NewText.ToString();
		MCPSettings->SaveConfig();
		CachedServerAddress = MCPSettings->ServerAddress;
	}
}

void SMCPStatusWidget::OnServerPortChanged(const FText& NewText)
{
	if (MCPSettings)
	{
		int32 NewPort = FCString::Atoi(*NewText.ToString());
		if (NewPort > 0 && NewPort <= 65535)
		{
			MCPSettings->ServerPort = NewPort;
			MCPSettings->SaveConfig();
			CachedServerPort = MCPSettings->ServerPort;
		}
	}
}

void SMCPStatusWidget::OnAutoConnectChanged(ECheckBoxState NewState)
{
	if (MCPSettings)
	{
		MCPSettings->bAutoConnectOnStartup = (NewState == ECheckBoxState::Checked);
		MCPSettings->SaveConfig();
	}
}

// UI state getters
FText SMCPStatusWidget::GetConnectionStatusText() const
{
	// Get status from MCPClient first, fallback to MCPSettings
	UMCPClient* MCPClient = UMCPClient::Get();
	EMCPConnectionState CurrentState = EMCPConnectionState::Disconnected;

	if (MCPClient)
	{
		CurrentState = MCPClient->GetConnectionState();
	}
	else if (MCPSettings)
	{
		CurrentState = MCPSettings->GetConnectionState();
	}
	else
	{
		return LOCTEXT("UnknownStatus", "Unknown");
	}

	switch (CurrentState)
	{
	case EMCPConnectionState::Disconnected:
		return LOCTEXT("DisconnectedStatus", "Disconnected");
	case EMCPConnectionState::Connecting:
		return LOCTEXT("ConnectingStatus", "Connecting...");
	case EMCPConnectionState::Connected:
		return LOCTEXT("ConnectedStatus", "Connected");
	case EMCPConnectionState::Failed:
		return LOCTEXT("FailedStatus", "Connection Failed");
	case EMCPConnectionState::Disabled:
		return LOCTEXT("DisabledStatus", "Disabled");
	default:
		return LOCTEXT("UnknownStatus", "Unknown");
	}
}

FSlateColor SMCPStatusWidget::GetConnectionStatusColor() const
{
	// Get status from MCPClient first, fallback to MCPSettings
	UMCPClient* MCPClient = UMCPClient::Get();
	EMCPConnectionState CurrentState = EMCPConnectionState::Disconnected;

	if (MCPClient)
	{
		CurrentState = MCPClient->GetConnectionState();
	}
	else if (MCPSettings)
	{
		CurrentState = MCPSettings->GetConnectionState();
	}
	else
	{
		return FSlateColor(FLinearColor::Gray);
	}

	return FSlateColor(GetConnectionStateColor(CurrentState));
}

FLinearColor SMCPStatusWidget::GetConnectionStateColor(EMCPConnectionState State) const
{
	switch (State)
	{
	case EMCPConnectionState::Disconnected:
		return FLinearColor::Gray;
	case EMCPConnectionState::Connecting:
		return FLinearColor::Yellow;
	case EMCPConnectionState::Connected:
		return SuccessColor;
	case EMCPConnectionState::Failed:
		return ErrorColor;
	case EMCPConnectionState::Disabled:
		return FLinearColor::Gray;
	default:
		return FLinearColor::White;
	}
}

FText SMCPStatusWidget::GetServerURLText() const
{
	if (MCPSettings)
	{
		return FText::FromString(MCPSettings->GetWebSocketURL());
	}
	return LOCTEXT("NoURL", "No URL configured");
}

FText SMCPStatusWidget::GetLastConnectionTimeText() const
{
	if (MCPSettings)
	{
		FDateTime LastTime = MCPSettings->GetLastConnectionTime();
		if (LastTime == FDateTime::MinValue())
		{
			return LOCTEXT("NeverConnected", "Never");
		}
		return FText::FromString(LastTime.ToString());
	}
	return LOCTEXT("Unknown", "Unknown");
}

bool SMCPStatusWidget::IsConnectButtonEnabled() const
{
	// Get status from MCPClient first, fallback to MCPSettings
	UMCPClient* MCPClient = UMCPClient::Get();
	EMCPConnectionState State = EMCPConnectionState::Disconnected;

	if (MCPClient)
	{
		State = MCPClient->GetConnectionState();
	}
	else if (MCPSettings)
	{
		State = MCPSettings->GetConnectionState();
	}
	else
	{
		return false;
	}

	return (State == EMCPConnectionState::Disconnected || State == EMCPConnectionState::Failed);
}

bool SMCPStatusWidget::IsDisconnectButtonEnabled() const
{
	// Get status from MCPClient first, fallback to MCPSettings
	UMCPClient* MCPClient = UMCPClient::Get();
	EMCPConnectionState State = EMCPConnectionState::Disconnected;

	if (MCPClient)
	{
		State = MCPClient->GetConnectionState();
	}
	else if (MCPSettings)
	{
		State = MCPSettings->GetConnectionState();
	}
	else
	{
		return false;
	}

	return (State == EMCPConnectionState::Connected || State == EMCPConnectionState::Connecting);
}

FText SMCPStatusWidget::GetServerAddressText() const
{
	return MCPSettings ? FText::FromString(MCPSettings->ServerAddress) : FText::GetEmpty();
}

FText SMCPStatusWidget::GetServerPortText() const
{
	return MCPSettings ? FText::FromString(FString::FromInt(MCPSettings->ServerPort)) : FText::GetEmpty();
}

ECheckBoxState SMCPStatusWidget::GetAutoConnectState() const
{
	if (MCPSettings && MCPSettings->bAutoConnectOnStartup)
	{
		return ECheckBoxState::Checked;
	}
	return ECheckBoxState::Unchecked;
}

void SMCPStatusWidget::UpdateConnectionStatus(EMCPConnectionState NewState)
{
	CachedConnectionState = NewState;
	// Widget will automatically update through binding
}

void SMCPStatusWidget::RefreshServerInfo()
{
	if (MCPSettings)
	{
		CachedServerAddress = MCPSettings->ServerAddress;
		CachedServerPort = MCPSettings->ServerPort;
	}
}

#undef LOCTEXT_NAMESPACE