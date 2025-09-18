// Copyright Epic Games, Inc. All Rights Reserved.
// MCPClient - Implementation of WebSocket client for MCP server communication

#include "MCPClient.h"
#include "MCPStatusWidget.h"
#include "MCPBlueprintManager.h"
#include "WebSocketsModule.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "HAL/PlatformFilemanager.h"
#include "Misc/DateTime.h"
#include "Misc/Guid.h"
#include "Engine/Engine.h"
#include "TimerManager.h"
#include "Async/Async.h"

DEFINE_LOG_CATEGORY_STATIC(LogMCPClient, Log, All);

// Static member definitions
UMCPClient* UMCPClient::SingletonInstance = nullptr;
const float UMCPClient::BaseReconnectDelay = 2.0f;
const float UMCPClient::MaxReconnectDelay = 60.0f;
const float UMCPClient::ConnectionTimeout = 30.0f;
const FString UMCPClient::MCPProtocolVersion = TEXT("2024-11-05");

UMCPClient::UMCPClient()
	: MCPSettings(nullptr)
	, BlueprintManager(nullptr)
	, WebSocket(nullptr)
	, WebSocketsModule(nullptr)
	, CurrentConnectionState(EMCPConnectionState::Disconnected)
	, bAutoReconnectEnabled(true)
	, ReconnectAttempts(0)
	, RequestIdCounter(0)
{
	// Initialize WebSockets module
	WebSocketsModule = &FModuleManager::LoadModuleChecked<FWebSocketsModule>("WebSockets");
}

UMCPClient::~UMCPClient()
{
	// Clean up on destruction
	if (WebSocket.IsValid())
	{
		Disconnect(false);
	}

	// Clear singleton reference
	if (SingletonInstance == this)
	{
		SingletonInstance = nullptr;
	}
}

void UMCPClient::BeginDestroy()
{
	// Ensure clean disconnection before destruction
	if (WebSocket.IsValid())
	{
		Disconnect(false);
	}

	// Stop any running timers
	if (GEngine && GEngine->GetWorldFromContextObject(this, EGetWorldErrorMode::LogAndReturnNull))
	{
		if (UWorld* World = GEngine->GetWorldFromContextObject(this, EGetWorldErrorMode::LogAndReturnNull))
		{
			World->GetTimerManager().ClearTimer(AutoReconnectTimerHandle);
		}
	}

	Super::BeginDestroy();
}

UMCPClient* UMCPClient::Get()
{
	if (!SingletonInstance)
	{
		SingletonInstance = NewObject<UMCPClient>();
		SingletonInstance->AddToRoot(); // Prevent garbage collection
	}
	return SingletonInstance;
}

bool UMCPClient::Initialize(UMCPSettings* InSettings)
{
	// Use provided settings or get default instance
	MCPSettings = InSettings ? InSettings : UMCPSettings::Get();

	if (!MCPSettings)
	{
		LogMessage(TEXT("Failed to initialize MCPClient: No valid settings found"), ELogVerbosity::Error);
		return false;
	}

	// Validate settings
	if (!ValidateConnectionSettings())
	{
		LogMessage(TEXT("Failed to initialize MCPClient: Invalid connection settings"), ELogVerbosity::Error);
		return false;
	}

	// Initialize Blueprint Manager
	BlueprintManager = UMCPBlueprintManager::Get();
	if (BlueprintManager && !BlueprintManager->Initialize(MCPSettings))
	{
		LogMessage(TEXT("Failed to initialize Blueprint Manager"), ELogVerbosity::Warning);
		// Don't fail initialization - blueprint features just won't be available
	}

	// Initialize connection state
	SetConnectionState(EMCPConnectionState::Disconnected);
	ResetReconnectAttempts();

	LogMessage(TEXT("MCPClient initialized successfully"));
	return true;
}

bool UMCPClient::Connect()
{
	if (!MCPSettings)
	{
		LogMessage(TEXT("Cannot connect: MCPClient not initialized"), ELogVerbosity::Error);
		return false;
	}

	if (CurrentConnectionState == EMCPConnectionState::Connected ||
		CurrentConnectionState == EMCPConnectionState::Connecting)
	{
		LogMessage(TEXT("Already connected or connecting to MCP server"));
		return true;
	}

	// Validate settings before attempting connection
	if (!ValidateConnectionSettings())
	{
		SetConnectionState(EMCPConnectionState::Failed, TEXT("Invalid connection settings"));
		return false;
	}

	// Create WebSocket if needed
	if (!WebSocket.IsValid() && WebSocketsModule)
	{
		FString WebSocketURL = GetWebSocketURL();
		FString Protocol = TEXT(""); // MCP doesn't require specific sub-protocol

		WebSocket = WebSocketsModule->CreateWebSocket(WebSocketURL, Protocol);

		if (!WebSocket.IsValid())
		{
			LogMessage(TEXT("Failed to create WebSocket instance"), ELogVerbosity::Error);
			SetConnectionState(EMCPConnectionState::Failed, TEXT("Failed to create WebSocket"));
			return false;
		}

		// Bind WebSocket event handlers
		WebSocket->OnConnected().AddUObject(this, &UMCPClient::OnWebSocketConnected);
		WebSocket->OnConnectionError().AddUObject(this, &UMCPClient::OnWebSocketConnectionError);
		WebSocket->OnClosed().AddUObject(this, &UMCPClient::OnWebSocketClosed);
		WebSocket->OnMessage().AddUObject(this, &UMCPClient::OnWebSocketMessage);
		WebSocket->OnBinaryMessage().AddUObject(this, &UMCPClient::OnWebSocketBinaryMessage);
		WebSocket->OnMessageSent().AddUObject(this, &UMCPClient::OnWebSocketMessageSent);
	}

	// Update state and attempt connection
	SetConnectionState(EMCPConnectionState::Connecting);
	LastConnectionAttempt = FDateTime::Now();

	LogMessage(FString::Printf(TEXT("Attempting to connect to MCP server: %s"), *GetWebSocketURL()));

	// Attempt connection
	WebSocket->Connect();

	return true;
}

void UMCPClient::Disconnect(bool bGraceful)
{
	StopAutoReconnectTimer();

	if (WebSocket.IsValid())
	{
		if (bGraceful && CurrentConnectionState == EMCPConnectionState::Connected)
		{
			// Send graceful disconnect notification if protocol supports it
			SendNotification(TEXT("session/end"), TEXT("{}"));
		}

		// Close WebSocket connection
		WebSocket->Close();
		WebSocket.Reset();
	}

	// Clear pending requests
	{
		FScopeLock Lock(&RequestsMutex);
		PendingRequests.Empty();
	}

	SetConnectionState(EMCPConnectionState::Disconnected);
	ResetReconnectAttempts();

	LogMessage(TEXT("Disconnected from MCP server"));
}

bool UMCPClient::IsConnected() const
{
	return CurrentConnectionState == EMCPConnectionState::Connected;
}

EMCPConnectionState UMCPClient::GetConnectionState() const
{
	return CurrentConnectionState;
}

FString UMCPClient::SendRequest(const FString& Method, const FString& Params, const FString& RequestId)
{
	if (!IsConnected())
	{
		LogMessage(TEXT("Cannot send request: Not connected to MCP server"), ELogVerbosity::Warning);
		return TEXT("");
	}

	// Generate request ID if not provided
	FString ActualRequestId = RequestId.IsEmpty() ? GenerateRequestId() : RequestId;

	// Create MCP message
	FMCPMessage Message(ActualRequestId, TEXT("request"), Method);
	Message.Params = Params;

	// Store pending request
	{
		FScopeLock Lock(&RequestsMutex);
		PendingRequests.Add(ActualRequestId, Message);
	}

	// Convert to JSON and send
	FString JsonMessage = CreateJsonFromMCPMessage(Message);
	if (SendRawMessage(JsonMessage))
	{
		LogMessage(FString::Printf(TEXT("Sent MCP request: %s (ID: %s)"), *Method, *ActualRequestId));
		return ActualRequestId;
	}
	else
	{
		// Remove from pending requests if send failed
		{
			FScopeLock Lock(&RequestsMutex);
			PendingRequests.Remove(ActualRequestId);
		}
		LogMessage(FString::Printf(TEXT("Failed to send MCP request: %s"), *Method), ELogVerbosity::Error);
		return TEXT("");
	}
}

bool UMCPClient::SendNotification(const FString& Method, const FString& Params)
{
	if (!IsConnected())
	{
		LogMessage(TEXT("Cannot send notification: Not connected to MCP server"), ELogVerbosity::Warning);
		return false;
	}

	// Create MCP notification message (no ID for notifications)
	FMCPMessage Message(TEXT(""), TEXT("notification"), Method);
	Message.Params = Params;

	// Convert to JSON and send
	FString JsonMessage = CreateJsonFromMCPMessage(Message);
	if (SendRawMessage(JsonMessage))
	{
		LogMessage(FString::Printf(TEXT("Sent MCP notification: %s"), *Method));
		return true;
	}
	else
	{
		LogMessage(FString::Printf(TEXT("Failed to send MCP notification: %s"), *Method), ELogVerbosity::Error);
		return false;
	}
}

bool UMCPClient::SendRawMessage(const FString& JsonMessage)
{
	if (!WebSocket.IsValid() || !IsConnected())
	{
		LogMessage(TEXT("Cannot send message: WebSocket not connected"), ELogVerbosity::Warning);
		return false;
	}

	// Send message through WebSocket
	WebSocket->Send(JsonMessage);
	return true;
}

void UMCPClient::RegisterStatusWidget(TSharedPtr<SMCPStatusWidget> StatusWidget)
{
	if (StatusWidget.IsValid())
	{
		FScopeLock Lock(&StatusWidgetsMutex);
		RegisteredStatusWidgets.AddUnique(StatusWidget);
		LogMessage(TEXT("Status widget registered for MCP updates"));
	}
}

void UMCPClient::UnregisterStatusWidget(TSharedPtr<SMCPStatusWidget> StatusWidget)
{
	FScopeLock Lock(&StatusWidgetsMutex);
	RegisteredStatusWidgets.RemoveAll([StatusWidget](const TWeakPtr<SMCPStatusWidget>& Widget) {
		return !Widget.IsValid() || Widget.Pin() == StatusWidget;
	});
	LogMessage(TEXT("Status widget unregistered from MCP updates"));
}

void UMCPClient::SetAutoReconnectEnabled(bool bEnable)
{
	bAutoReconnectEnabled = bEnable;
	if (!bEnable)
	{
		StopAutoReconnectTimer();
	}
	LogMessage(FString::Printf(TEXT("Auto-reconnect %s"), bEnable ? TEXT("enabled") : TEXT("disabled")));
}

bool UMCPClient::IsAutoReconnectEnabled() const
{
	return bAutoReconnectEnabled;
}

FString UMCPClient::GetLastErrorMessage() const
{
	return LastErrorMessage;
}

void UMCPClient::ClearLastError()
{
	LastErrorMessage.Empty();
}

// WebSocket Event Handlers

void UMCPClient::OnWebSocketConnected()
{
	LogMessage(TEXT("WebSocket connected to MCP server"));

	SetConnectionState(EMCPConnectionState::Connected);
	ResetReconnectAttempts();

	// Update settings with successful connection
	if (MCPSettings)
	{
		MCPSettings->SetConnectionState(EMCPConnectionState::Connected);
	}
}

void UMCPClient::OnWebSocketConnectionError(const FString& Error)
{
	LogMessage(FString::Printf(TEXT("WebSocket connection error: %s"), *Error), ELogVerbosity::Error);

	SetConnectionState(EMCPConnectionState::Failed, Error);

	// Attempt auto-reconnect if enabled
	if (bAutoReconnectEnabled && ReconnectAttempts < MaxReconnectAttempts)
	{
		StartAutoReconnectTimer();
	}
}

void UMCPClient::OnWebSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean)
{
	LogMessage(FString::Printf(TEXT("WebSocket connection closed (Code: %d, Reason: %s, Clean: %s)"),
		StatusCode, *Reason, bWasClean ? TEXT("Yes") : TEXT("No")));

	// Reset WebSocket reference
	if (WebSocket.IsValid())
	{
		WebSocket.Reset();
	}

	// Update connection state
	if (CurrentConnectionState != EMCPConnectionState::Disconnected)
	{
		SetConnectionState(bWasClean ? EMCPConnectionState::Disconnected : EMCPConnectionState::Failed, Reason);

		// Attempt auto-reconnect if connection was not gracefully closed
		if (!bWasClean && bAutoReconnectEnabled && ReconnectAttempts < MaxReconnectAttempts)
		{
			StartAutoReconnectTimer();
		}
	}
}

void UMCPClient::OnWebSocketMessage(const FString& Message)
{
	LogMessage(FString::Printf(TEXT("Received WebSocket message: %s"), *Message));

	// Process the incoming MCP message
	ProcessIncomingMessage(Message);
}

void UMCPClient::OnWebSocketBinaryMessage(const void* Data, uint64 Size, bool bIsLastFragment)
{
	// MCP protocol uses JSON text messages, binary messages are not expected
	LogMessage(TEXT("Received unexpected binary message from MCP server"), ELogVerbosity::Warning);
}

void UMCPClient::OnWebSocketMessageSent(const FString& Message)
{
	// Optional: Log sent messages for debugging
	if (MCPSettings && MCPSettings->bEnableVerboseLogging)
	{
		LogMessage(FString::Printf(TEXT("WebSocket message sent: %s"), *Message));
	}
}

// Connection Management

void UMCPClient::SetConnectionState(EMCPConnectionState NewState, const FString& ErrorMessage)
{
	if (CurrentConnectionState != NewState)
	{
		EMCPConnectionState OldState = CurrentConnectionState;
		CurrentConnectionState = NewState;

		// Store error message if provided
		if (!ErrorMessage.IsEmpty())
		{
			LastErrorMessage = ErrorMessage;
		}

		// Update settings
		if (MCPSettings)
		{
			MCPSettings->SetConnectionState(NewState);
		}

		// Log state change
		LogMessage(FString::Printf(TEXT("Connection state changed: %s -> %s"),
			*StaticEnum<EMCPConnectionState>()->GetValueAsString(OldState),
			*StaticEnum<EMCPConnectionState>()->GetValueAsString(NewState)));

		// Notify status widgets on game thread
		AsyncTask(ENamedThreads::GameThread, [this, NewState, ErrorMessage]()
		{
			// Fire delegate
			OnConnectionStateChanged.Broadcast(NewState, ErrorMessage);

			// Notify registered status widgets
			NotifyStatusWidgets(TEXT("Info"), FString::Printf(TEXT("Connection state: %s"),
				*StaticEnum<EMCPConnectionState>()->GetValueAsString(NewState)));
		});
	}
}

void UMCPClient::StartAutoReconnectTimer()
{
	if (!bAutoReconnectEnabled || !GEngine)
	{
		return;
	}

	UWorld* World = GEngine->GetWorldFromContextObject(this, EGetWorldErrorMode::LogAndReturnNull);
	if (!World)
	{
		return;
	}

	// Calculate exponential backoff delay
	float Delay = FMath::Min(BaseReconnectDelay * FMath::Pow(2.0f, ReconnectAttempts), MaxReconnectDelay);

	LogMessage(FString::Printf(TEXT("Scheduling auto-reconnect in %.1f seconds (attempt %d/%d)"),
		Delay, ReconnectAttempts + 1, MaxReconnectAttempts));

	World->GetTimerManager().SetTimer(AutoReconnectTimerHandle, this, &UMCPClient::AttemptReconnect, Delay, false);
}

void UMCPClient::StopAutoReconnectTimer()
{
	if (GEngine)
	{
		if (UWorld* World = GEngine->GetWorldFromContextObject(this, EGetWorldErrorMode::LogAndReturnNull))
		{
			World->GetTimerManager().ClearTimer(AutoReconnectTimerHandle);
		}
	}
}

void UMCPClient::AttemptReconnect()
{
	if (CurrentConnectionState == EMCPConnectionState::Connected ||
		CurrentConnectionState == EMCPConnectionState::Connecting)
	{
		// Already connected or connecting
		return;
	}

	if (ReconnectAttempts >= MaxReconnectAttempts)
	{
		LogMessage(FString::Printf(TEXT("Maximum reconnection attempts (%d) reached, giving up"), MaxReconnectAttempts),
			ELogVerbosity::Error);
		SetConnectionState(EMCPConnectionState::Failed, TEXT("Maximum reconnection attempts reached"));
		return;
	}

	ReconnectAttempts++;
	LogMessage(FString::Printf(TEXT("Auto-reconnect attempt %d/%d"), ReconnectAttempts, MaxReconnectAttempts));

	// Increment reconnect attempts in settings
	if (MCPSettings)
	{
		MCPSettings->IncrementReconnectAttempts();
	}

	// Attempt to connect
	if (!Connect())
	{
		// If connection fails, schedule another attempt
		StartAutoReconnectTimer();
	}
}

void UMCPClient::ResetReconnectAttempts()
{
	ReconnectAttempts = 0;
	if (MCPSettings)
	{
		MCPSettings->ResetReconnectAttempts();
	}
}

// Message Handling

void UMCPClient::ProcessIncomingMessage(const FString& JsonMessage)
{
	FMCPMessage Message;
	if (!ParseMCPMessage(JsonMessage, Message))
	{
		LogMessage(FString::Printf(TEXT("Failed to parse incoming MCP message: %s"), *JsonMessage), ELogVerbosity::Error);
		return;
	}

	// Dispatch to game thread for delegate broadcasting
	AsyncTask(ENamedThreads::GameThread, [this, Message, JsonMessage]()
	{
		// Fire message received delegate
		OnMessageReceived.Broadcast(Message.Type, JsonMessage);

		// Handle responses to pending requests
		if (Message.Type == TEXT("response") && !Message.Id.IsEmpty())
		{
			FMCPMessage OriginalRequest;
			bool bFoundRequest = false;

			{
				FScopeLock Lock(&RequestsMutex);
				if (FMCPMessage* FoundMessage = PendingRequests.Find(Message.Id))
				{
					OriginalRequest = *FoundMessage;
					PendingRequests.Remove(Message.Id);
					bFoundRequest = true;
				}
			}

			if (bFoundRequest)
			{
				bool bSuccess = Message.Error.IsEmpty();
				FString ResponseData = bSuccess ? Message.Result : Message.Error;

				// Fire operation complete delegate
				OnOperationComplete.Broadcast(Message.Id, bSuccess, ResponseData);

				LogMessage(FString::Printf(TEXT("Received response for request %s: %s"),
					*Message.Id, bSuccess ? TEXT("Success") : TEXT("Error")));
			}
		}

		// Handle blueprint commands automatically
		if (Message.Type == TEXT("request") && !Message.Method.IsEmpty())
		{
			if (Message.Method == TEXT("create_blueprint") ||
				Message.Method == TEXT("set_property") ||
				Message.Method == TEXT("set_blueprint_property") ||
				Message.Method == TEXT("add_component") ||
				Message.Method == TEXT("compile_blueprint") ||
				Message.Method == TEXT("get_server_status"))
			{
				// Process blueprint command
				FString Response = ProcessBlueprintCommand(Message.Method, Message.Params);

				// Send response back if we have a request ID
				if (!Message.Id.IsEmpty())
				{
					// Create proper JSON-RPC 2.0 response
					TSharedPtr<FJsonObject> ResponseObject = MakeShareable(new FJsonObject);
					ResponseObject->SetStringField(TEXT("jsonrpc"), TEXT("2.0"));
					ResponseObject->SetStringField(TEXT("id"), Message.Id);

					// Try to parse the response as JSON object
					TSharedPtr<FJsonObject> ResultObject;
					TSharedRef<TJsonReader<>> ResultReader = TJsonReaderFactory<>::Create(Response);
					if (FJsonSerializer::Deserialize(ResultReader, ResultObject) && ResultObject.IsValid())
					{
						ResponseObject->SetObjectField(TEXT("result"), ResultObject);
					}
					else
					{
						ResponseObject->SetStringField(TEXT("result"), Response);
					}

					FString ResponseString;
					TSharedRef<TJsonWriter<>> ResponseWriter = TJsonWriterFactory<>::Create(&ResponseString);
					FJsonSerializer::Serialize(ResponseObject.ToSharedRef(), ResponseWriter);

					SendRawMessage(ResponseString);
				}

				LogMessage(FString::Printf(TEXT("Processed blueprint command: %s"), *Message.Method));
			}
		}

		// Notify status widgets
		NotifyStatusWidgets(TEXT("Info"), FString::Printf(TEXT("Received %s: %s"), *Message.Type, *Message.Method));
	});
}

bool UMCPClient::ParseMCPMessage(const FString& JsonMessage, FMCPMessage& OutMessage)
{
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonMessage);

	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		return false;
	}

	// Parse basic fields
	JsonObject->TryGetStringField(TEXT("id"), OutMessage.Id);
	JsonObject->TryGetStringField(TEXT("method"), OutMessage.Method);

	// Determine message type based on content
	if (JsonObject->HasField(TEXT("method")))
	{
		OutMessage.Type = !OutMessage.Id.IsEmpty() ? TEXT("request") : TEXT("notification");
	}
	else if (JsonObject->HasField(TEXT("result")) || JsonObject->HasField(TEXT("error")))
	{
		OutMessage.Type = TEXT("response");
	}
	else
	{
		OutMessage.Type = TEXT("unknown");
	}

	// Parse params (can be object or string)
	if (JsonObject->HasField(TEXT("params")))
	{
		const TSharedPtr<FJsonValue> ParamsValue = JsonObject->TryGetField(TEXT("params"));
		if (ParamsValue.IsValid())
		{
			if (ParamsValue->Type == EJson::Object)
			{
				TSharedPtr<FJsonObject> ParamsObject = ParamsValue->AsObject();
				FString ParamsString;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ParamsString);
				FJsonSerializer::Serialize(ParamsObject.ToSharedRef(), Writer);
				OutMessage.Params = ParamsString;
			}
			else if (ParamsValue->Type == EJson::String)
			{
				OutMessage.Params = ParamsValue->AsString();
			}
		}
	}

	// Parse result
	if (JsonObject->HasField(TEXT("result")))
	{
		const TSharedPtr<FJsonValue> ResultValue = JsonObject->TryGetField(TEXT("result"));
		if (ResultValue.IsValid())
		{
			if (ResultValue->Type == EJson::Object || ResultValue->Type == EJson::Array)
			{
				FString ResultString;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ResultString);
				FJsonSerializer::Serialize(ResultValue, TEXT(""), Writer, false);
				OutMessage.Result = ResultString;
			}
			else
			{
				OutMessage.Result = ResultValue->AsString();
			}
		}
	}

	// Parse error
	if (JsonObject->HasField(TEXT("error")))
	{
		const TSharedPtr<FJsonValue> ErrorValue = JsonObject->TryGetField(TEXT("error"));
		if (ErrorValue.IsValid())
		{
			if (ErrorValue->Type == EJson::Object)
			{
				TSharedPtr<FJsonObject> ErrorObject = ErrorValue->AsObject();
				FString ErrorString;
				TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&ErrorString);
				FJsonSerializer::Serialize(ErrorObject.ToSharedRef(), Writer);
				OutMessage.Error = ErrorString;
			}
			else
			{
				OutMessage.Error = ErrorValue->AsString();
			}
		}
	}

	return true;
}

FString UMCPClient::CreateJsonFromMCPMessage(const FMCPMessage& Message)
{
	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);

	// Set JSON-RPC 2.0 version
	JsonObject->SetStringField(TEXT("jsonrpc"), TEXT("2.0"));

	// Set basic fields
	if (!Message.Id.IsEmpty())
	{
		JsonObject->SetStringField(TEXT("id"), Message.Id);
	}

	// For JSON-RPC 2.0, we use method field directly instead of type
	if (!Message.Method.IsEmpty())
	{
		JsonObject->SetStringField(TEXT("method"), Message.Method);
	}

	// Set params if present
	if (!Message.Params.IsEmpty())
	{
		// Try to parse params as JSON object first
		TSharedPtr<FJsonObject> ParamsObject;
		TSharedRef<TJsonReader<>> ParamsReader = TJsonReaderFactory<>::Create(Message.Params);

		if (FJsonSerializer::Deserialize(ParamsReader, ParamsObject) && ParamsObject.IsValid())
		{
			JsonObject->SetObjectField(TEXT("params"), ParamsObject);
		}
		else
		{
			// If not valid JSON object, treat as string
			JsonObject->SetStringField(TEXT("params"), Message.Params);
		}
	}

	// Set result if present
	if (!Message.Result.IsEmpty())
	{
		// Try to parse result as JSON
		TSharedPtr<FJsonValue> ResultValue;
		TSharedRef<TJsonReader<>> ResultReader = TJsonReaderFactory<>::Create(Message.Result);

		if (FJsonSerializer::Deserialize(ResultReader, ResultValue) && ResultValue.IsValid())
		{
			JsonObject->SetField(TEXT("result"), ResultValue);
		}
		else
		{
			JsonObject->SetStringField(TEXT("result"), Message.Result);
		}
	}

	// Set error if present
	if (!Message.Error.IsEmpty())
	{
		// Try to parse error as JSON object
		TSharedPtr<FJsonObject> ErrorObject;
		TSharedRef<TJsonReader<>> ErrorReader = TJsonReaderFactory<>::Create(Message.Error);

		if (FJsonSerializer::Deserialize(ErrorReader, ErrorObject) && ErrorObject.IsValid())
		{
			JsonObject->SetObjectField(TEXT("error"), ErrorObject);
		}
		else
		{
			JsonObject->SetStringField(TEXT("error"), Message.Error);
		}
	}

	// Serialize to string
	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

	return OutputString;
}

FString UMCPClient::GenerateRequestId()
{
	RequestIdCounter++;
	return FString::Printf(TEXT("req_%d_%s"), RequestIdCounter, *FGuid::NewGuid().ToString(EGuidFormats::Short));
}

bool UMCPClient::ValidateMCPMessage(const FMCPMessage& Message)
{
	// Basic validation rules for MCP messages
	if (Message.Type.IsEmpty())
	{
		return false;
	}

	if (Message.Type == TEXT("request") || Message.Type == TEXT("notification"))
	{
		if (Message.Method.IsEmpty())
		{
			return false;
		}
	}

	if (Message.Type == TEXT("request") && Message.Id.IsEmpty())
	{
		return false;
	}

	return true;
}

// Utility Functions

void UMCPClient::LogMessage(const FString& Message, ELogVerbosity::Type Verbosity)
{
	// Use UE logging system with appropriate log level
	switch (Verbosity)
	{
		case ELogVerbosity::Error:
			UE_LOG(LogMCPClient, Error, TEXT("[MCPClient] %s"), *Message);
			break;
		case ELogVerbosity::Warning:
			UE_LOG(LogMCPClient, Warning, TEXT("[MCPClient] %s"), *Message);
			break;
		default:
			UE_LOG(LogMCPClient, Log, TEXT("[MCPClient] %s"), *Message);
			break;
	}

	// Also notify status widgets if available
	FString MessageLogLevel;
	switch (Verbosity)
	{
		case ELogVerbosity::Error:
			MessageLogLevel = TEXT("Error");
			break;
		case ELogVerbosity::Warning:
			MessageLogLevel = TEXT("Warning");
			break;
		default:
			MessageLogLevel = TEXT("Info");
			break;
	}

	NotifyStatusWidgets(MessageLogLevel, Message);
}

void UMCPClient::NotifyStatusWidgets(const FString& MessageLogLevel, const FString& LogMessage)
{
	// Must be called from game thread
	if (!IsInGameThread())
	{
		AsyncTask(ENamedThreads::GameThread, [this, MessageLogLevel, LogMessage]()
		{
			NotifyStatusWidgets(MessageLogLevel, LogMessage);
		});
		return;
	}

	FScopeLock Lock(&StatusWidgetsMutex);

	// Clean up invalid widgets and notify valid ones
	for (int32 i = RegisteredStatusWidgets.Num() - 1; i >= 0; i--)
	{
		if (RegisteredStatusWidgets[i].IsValid())
		{
			if (TSharedPtr<SMCPStatusWidget> Widget = RegisteredStatusWidgets[i].Pin())
			{
				Widget->AddLogEntry(MessageLogLevel, LogMessage);
				Widget->UpdateConnectionStatus(CurrentConnectionState);
			}
		}
		else
		{
			// Remove invalid widget references
			RegisteredStatusWidgets.RemoveAt(i);
		}
	}
}

FString UMCPClient::GetWebSocketURL() const
{
	if (!MCPSettings)
	{
		return TEXT("");
	}

	return MCPSettings->GetWebSocketURL();
}

bool UMCPClient::ValidateConnectionSettings() const
{
	if (!MCPSettings)
	{
		return false;
	}

	return MCPSettings->ValidateSettings();
}

FString UMCPClient::ProcessBlueprintCommand(const FString& Method, const FString& Params)
{
	// Check if Blueprint Manager is available
	if (!BlueprintManager)
	{
		LogMessage(TEXT("Blueprint Manager not available for command processing"), ELogVerbosity::Error);
		return TEXT("{\"success\":false,\"error\":\"Blueprint Manager not initialized\"}");
	}

	// Log the command
	LogMessage(FString::Printf(TEXT("Processing blueprint command: %s"), *Method));

	// Process different blueprint commands
	if (Method == TEXT("create_blueprint"))
	{
		return BlueprintManager->ProcessCreateBlueprintCommand(Params);
	}
	else if (Method == TEXT("set_property") || Method == TEXT("set_blueprint_property"))
	{
		return BlueprintManager->ProcessSetPropertyCommand(Params);
	}
	else if (Method == TEXT("add_component"))
	{
		return BlueprintManager->ProcessAddComponentCommand(Params);
	}
	else if (Method == TEXT("compile_blueprint"))
	{
		return BlueprintManager->ProcessCompileBlueprintCommand(Params);
	}
	else if (Method == TEXT("get_server_status"))
	{
		return BlueprintManager->ProcessGetServerStatusCommand(Params);
	}
	else
	{
		FString ErrorMsg = FString::Printf(TEXT("Unknown blueprint command: %s"), *Method);
		LogMessage(ErrorMsg, ELogVerbosity::Error);
		return FString::Printf(TEXT("{\"success\":false,\"error\":\"%s\"}"), *ErrorMsg);
	}
}